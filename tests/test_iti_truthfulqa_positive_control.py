import copy
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import hmac
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from cognitive_console.eval.truthfulqa_positive_control import (
    LocalTruthInfoJudge,
    OFFICIAL_BASE_PROMPT_ID,
    PROMPT_BANK_SHA256,
    PINNED_SNAPSHOTS,
    TruthfulQAItem,
    cached_pinned_snapshot_bytes,
    download_pinned_snapshot,
    load_pinned_truthfulqa,
    load_prompt_bank,
    official_twofold_splits,
    parse_binary_judge,
    resolve_pinned_snapshot_path,
    verify_pinned_snapshot,
)
from cognitive_console.experiments.iti_positive_control import (
    AUTHORIZATION_KEY_ENV,
    EXPERIMENT_ID,
    GenerationJob,
    GenerationRecord,
    JsonlCheckpoint,
    PRIMARY_BOOTSTRAP_SEED,
    RANDOM_BOOTSTRAP_SEED,
    RANDOM_DIRECTION_SEED_OFFSET,
    SAMPLE_SEED_MAPPING_VERSION,
    BOOTSTRAP_PERCENTILE_METHOD,
    authorization_signing_bytes,
    adjudicate_test,
    config_hash,
    consume_signed_test_authorization,
    dev_eligibility,
    deterministic_sample_seed,
)
from cognitive_console.ops.transformers_compat import (
    REQUIRED_TRANSFORMERS_VERSION,
    TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS,
    assert_transformers_compatibility,
)
from cognitive_console.steering.official_iti import (
    FROZEN_EOS_TOKEN_IDS,
    FROZEN_EOS_TOKEN_STRINGS,
    FROZEN_SAMPLING_CONFIG,
    ITIHeadSpec,
    MAX_POST_UNLOAD_CUDA_BYTES,
    OfficialITIConfig,
    OfficialITIHFBackend,
    fit_official_iti,
    generation_was_truncated,
    hook_bite_metrics,
    matched_random_config,
    validate_frozen_eos_mapping,
)
from cognitive_console.randomness import NUMPY_RNG_ALGORITHM, pcg64_rng
from scripts import run_iti_truthfulqa_positive_control as runner


REPO = Path(__file__).resolve().parents[1]


def test_prompt_bank_is_exact_bounded_and_stable():
    prompts = load_prompt_bank(REPO)
    import hashlib

    assert hashlib.sha256(
        (REPO / "data/strongest_prompts/truthfulness_positive_control.jsonl").read_bytes()
    ).hexdigest() == PROMPT_BANK_SHA256
    assert len(prompts) == 16
    assert prompts[0][0] == OFFICIAL_BASE_PROMPT_ID
    assert len({prompt_id for prompt_id, _ in prompts}) == 16
    assert all(len(text.split()) <= 48 for _, text in prompts)


def test_frozen_runner_config_matches_preregistered_identities():
    frozen = runner.frozen_config(code_commit="abc")
    assert frozen["model"] == {
        "id": runner.MODEL_ID,
        "revision": runner.MODEL_REVISION,
    }
    assert frozen["dataset"]["revision"] == runner.TRUTHFULQA_REVISION
    assert frozen["dataset"]["canonical_order_config"] == "multiple_choice"
    assert frozen["method"]["top_k_heads"] == 48
    assert frozen["method"]["alpha"] == 15.0
    assert frozen["generation"]["k"] == 5
    assert frozen["generation"]["top_p"] == 1.0
    assert frozen["generation"]["top_k"] == 0
    assert frozen["generation"]["eos_token_ids"] == [128001, 128009]
    assert frozen["disk"]["overridable"] is False
    assert frozen["hardware_profile"]["name"] == runner.DEFAULT_HARDWARE_PROFILE
    assert (
        frozen["generation"]["transformers_required_version"]
        == REQUIRED_TRANSFORMERS_VERSION
    )
    assert frozen["test_once"]["global_registry"] == (
        "/var/lib/cognitive-console/iti-truthfulqa-positive-control/"
        "test-attempts.jsonl"
    )
    assert frozen["statistics"]["ci_level"] == pytest.approx(1.0 - 0.05 / 3.0)
    assert frozen["current_grid_preservation"].endswith("0/12")
    assert "scikit-learn" in runner._runtime_environment()["packages"]
    autodl = runner.frozen_config(
        code_commit="abc",
        hardware_profile_name=runner.AUTODL_HARDWARE_PROFILE,
    )
    assert autodl["generation"]["activation_batch_size"] == 1
    assert autodl["generation"]["k"] == frozen["generation"]["k"] == 5
    assert autodl["method"] == frozen["method"]
    assert autodl["statistics"] == frozen["statistics"]
    assert autodl["disk"]["budget_gib"] == 44.0
    assert autodl["disk"]["ceiling_gib"] == 47.0


def test_official_twofold_is_deterministic_disjoint_and_covers_all_items():
    first = official_twofold_splits()
    second = official_twofold_splits()
    assert first == second
    assert sorted(index for fold in first for index in fold.test) == list(range(817))
    for split in first:
        assert set(split.inner_train).isdisjoint(split.inner_dev)
        assert set(split.outer_train).isdisjoint(split.test)
        assert set(split.inner_train) | set(split.inner_dev) == set(split.outer_train)
    assert first[0].inner_train[:5] == (410, 412, 414, 415, 416)
    assert first[0].inner_dev[:5] == (409, 411, 413, 418, 423)
    assert first[1].inner_train[:5] == (0, 1, 2, 3, 4)
    assert first[1].inner_dev[:5] == (8, 9, 10, 11, 22)


def test_truthfulqa_canonical_identity_changes_with_scientific_content():
    item = TruthfulQAItem(
        "truthfulqa-0000",
        0,
        "Question?",
        ("True",),
        ("False",),
        ("True", "False"),
        (1, 0),
    )
    baseline = runner._truthfulqa_identity([item])
    mutated = runner._truthfulqa_identity(
        [
            TruthfulQAItem(
                item.item_id,
                item.index,
                "Changed?",
                item.correct_answers,
                item.incorrect_answers,
                item.mc2_choices,
                item.mc2_labels,
            )
        ]
    )
    assert baseline["canonical_items_hash"] != mutated["canonical_items_hash"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("yes", True),
        ("Yes.", True),
        (" no! ", False),
        ("yes because", None),
        ("maybe", None),
        ("", None),
    ],
)
def test_strict_judge_parser(text, expected):
    assert parse_binary_judge(text) is expected


@pytest.mark.parametrize(
    "kind, expected_snapshot_name",
    [
        ("truth", "truth_judge"),
        ("info", "info_judge"),
    ],
)
def test_real_judge_load_resolves_runtime_kind_to_pinned_snapshot_key(
    kind,
    expected_snapshot_name,
    tmp_path,
    monkeypatch,
):
    class SnapshotKeyObserved(Exception):
        pass

    seen = []
    transformers = ModuleType("transformers")
    transformers.AutoConfig = object
    transformers.AutoModelForCausalLM = object
    transformers.AutoTokenizer = object
    monkeypatch.setitem(sys.modules, "torch", ModuleType("torch"))
    monkeypatch.setitem(sys.modules, "transformers", transformers)

    def observe_snapshot_key(name, snapshot_dir, **kwargs):
        del snapshot_dir, kwargs
        assert name in PINNED_SNAPSHOTS
        seen.append(name)
        raise SnapshotKeyObserved

    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control.download_pinned_snapshot",
        observe_snapshot_key,
    )
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )
    judge._resident_kind = kind
    with pytest.raises(SnapshotKeyObserved):
        judge._load(
            kind,
            runner.TRUTH_JUDGE_ID if kind == "truth" else runner.INFO_JUDGE_ID,
            (
                runner.TRUTH_JUDGE_REVISION
                if kind == "truth"
                else runner.INFO_JUDGE_REVISION
            ),
            tmp_path / kind,
        )
    judge._resident_kind = None
    assert seen == [expected_snapshot_name]


def test_judges_load_sequentially_from_shared_hub_cache(tmp_path, monkeypatch):
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )
    events = []
    runtime_marker = {"value": "audited"}

    def fake_load(kind, model_id, revision, cache_dir):
        assert judge._resident_kind == kind
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "weight.bin").write_bytes(b"x")
        judge.snapshot_identities[kind] = {
            "name": kind,
            "revision": revision,
            "files": {"weight.bin": {"sha256": "test"}},
        }
        judge.runtime_fingerprints[kind] = {
            "model_id": model_id,
            "revision": revision,
            "attention_implementation": "eager",
            "implementation_marker": runtime_marker["value"],
        }
        events.append(("load", kind, model_id, revision, cache_dir.name))
        return object(), object()

    monkeypatch.setattr(judge, "_load", fake_load)
    monkeypatch.setattr(
        judge,
        "_generate_label",
        lambda model, tokenizer, prompt: "yes" if "True:" in prompt else "no",
    )
    scores = judge.score_many(
        [("Question?", "Answer.")],
        identities=["job-1"],
        checkpoint_root=tmp_path / "judge-checkpoints",
    )
    assert scores[0].truth is True
    assert scores[0].informative is False
    assert [row[4] for row in events] == ["judges", "judges"]
    assert {path.name for path in judge.cache_root.glob("*")} == {"weight.bin"}
    resumed = judge.score_many(
        [("Question?", "Answer.")],
        identities=["job-1"],
        checkpoint_root=tmp_path / "judge-checkpoints",
    )
    assert resumed == scores
    assert [row[4] for row in events] == ["judges", "judges"]
    audited_snapshots = copy.deepcopy(judge.snapshot_identities)
    audited_runtimes = copy.deepcopy(judge.runtime_fingerprints)
    runtime_marker["value"] = "current-judge-drift"
    forced = judge.score_many(
        [("Question?", "Answer.")],
        identities=["job-1"],
        checkpoint_root=tmp_path / "judge-checkpoints",
        force_runtime_refresh=True,
    )
    assert forced == scores
    assert [row[4] for row in events] == [
        "judges",
        "judges",
        "judges",
        "judges",
    ]
    assert {
        row["implementation_marker"]
        for row in judge.runtime_fingerprints.values()
    } == {"current-judge-drift"}
    preflight = {
        "generator_snapshot_identity": {"snapshot_hash": "a" * 64},
        "model_config_hash": "b" * 64,
        "tokenizer_class": "PinnedTokenizer",
        "tokenizer_vocab_size": 128256,
        "eos_token_mapping": {"eos_token_ids": [128001, 128009]},
        "effective_generation_config": {"eos_token_id": [128001, 128009]},
        "gpu": {
            "physical_identity": {
                "uuid": "GPU-current",
                "pci_bus_id": "00000000:65:00.0",
            }
        },
        "attention_implementation": "eager",
        "attention_layers": [{"layer": 0, "source_sha256": "c" * 64}],
        "hardware_profile": {"name": runner.DEFAULT_HARDWARE_PROFILE},
        "host_binding": {"fingerprint_hash": "host-a"},
        "transformers_compatibility": {
            "required_version": REQUIRED_TRANSFORMERS_VERSION
        },
        "environment": {"packages": {"transformers": "x"}},
    }
    audited_fingerprint = runner._execution_fingerprint(
        preflight=preflight,
        judge_snapshot_identities=audited_snapshots,
        judge_runtime_fingerprints=audited_runtimes,
    )
    current_fingerprint = runner._execution_fingerprint(
        preflight=preflight,
        judge_snapshot_identities=judge.snapshot_identities,
        judge_runtime_fingerprints=judge.runtime_fingerprints,
    )
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        runner._assert_execution_fingerprint_matches_dev(
            {"execution_fingerprint": audited_fingerprint},
            current_fingerprint,
        )
    truth_manifest = json.loads(
        (
            tmp_path
            / "judge-checkpoints"
            / "truth.jsonl.manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert truth_manifest["complete"] is True
    assert truth_manifest["snapshot_identity"]["revision"] == runner.TRUTH_JUDGE_REVISION
    assert (
        truth_manifest["runtime_fingerprint"]["implementation_marker"]
        == "current-judge-drift"
    )
    with pytest.raises(ValueError, match="ordered_inputs_hash"):
        judge.score_many(
            [("Question?", "Changed answer.")],
            identities=["job-1"],
            checkpoint_root=tmp_path / "judge-checkpoints",
        )


def test_execute_jobs_unloads_generator_before_any_real_judge(
    tmp_path, monkeypatch
):
    item = SimpleNamespace(item_id="item-0", index=0, question="Question?")
    job = GenerationJob(
        0,
        "dev",
        "baseline",
        OFFICIAL_BASE_PROMPT_ID,
        item.item_id,
        item.index,
        0,
        123,
    )

    class GuardedGenerator:
        resident = True

        def generate_with_metadata(self, prompt, **kwargs):
            del prompt, kwargs
            assert self.resident is True
            return "Answer.", 1, False

        def release_for_sequential_judging(self):
            assert self.resident is True
            self.resident = False
            return {"after": {"allocated_bytes": 0, "reserved_bytes": 0}}

        def assert_unloaded_for_sequential_judging(self):
            if self.resident:
                raise RuntimeError("generator remains resident")
            return {
                "released": True,
                "max_post_unload_cuda_bytes": MAX_POST_UNLOAD_CUDA_BYTES,
                "allocated_bytes": 0,
                "reserved_bytes": 0,
            }

    generator = GuardedGenerator()
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )

    def guarded_score_many(pairs, *, identities, checkpoint_root):
        del identities, checkpoint_root
        judge._assert_ready_for_judge_load()
        assert generator.resident is False
        return [runner.JudgeScore(True, True, "yes", "yes") for _ in pairs]

    monkeypatch.setattr(judge, "score_many", guarded_score_many)
    records = runner._execute_jobs(
        [job],
        checkpoint_path=tmp_path / "dev.jsonl",
        run_config_hash="run-hash",
        items=[item],
        prompts={OFFICIAL_BASE_PROMPT_ID: "Answer truthfully."},
        generator=generator,
        judge=judge,
        configs={},
        checkpoint_binding={"run_config_hash": "run-hash"},
    )
    assert len(records) == 1
    assert generator.resident is False
    assert judge.generator_release_report is not None


def test_judge_residency_lock_rejects_concurrent_model_load(tmp_path):
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )
    assert judge._residency_lock.acquire(blocking=False)
    try:
        with pytest.raises(RuntimeError, match="concurrent judge residency"):
            judge.score_many(
                [("Question?", "Answer.")],
                identities=["job-1"],
                checkpoint_root=tmp_path / "checkpoints",
            )
    finally:
        judge._residency_lock.release()


def test_official_iti_recovers_planted_attention_head():
    rng = np.random.default_rng(4)
    shape = (3, 4, 6)
    train = rng.normal(size=(160, *shape))
    valid = rng.normal(size=(80, *shape))
    y_train = np.asarray([0, 1] * 80)
    y_valid = np.asarray([0, 1] * 40)
    planted = np.arange(1, 7, dtype=np.float64)
    planted /= np.linalg.norm(planted)
    train[y_train == 1, 1, 2, :] += 3.0 * planted
    train[y_train == 0, 1, 2, :] -= 3.0 * planted
    valid[y_valid == 1, 1, 2, :] += 3.0 * planted
    valid[y_valid == 0, 1, 2, :] -= 3.0 * planted

    config = fit_official_iti(
        train, y_train, valid, y_valid, top_k=3, alpha=15.0
    )
    assert (config.specs[0].layer, config.specs[0].head) == (1, 2)
    assert float(np.dot(config.specs[0].direction, planted)) > 0.95
    assert config.specs[0].sigma > 0.0
    random = matched_random_config(config, seed=9)
    assert random.method == "matched_random_attention_head_control"
    assert [(x.layer, x.head, x.sigma) for x in random.specs] == [
        (x.layer, x.head, x.sigma) for x in config.specs
    ]


def _simple_config():
    return OfficialITIConfig(
        specs=(
            ITIHeadSpec(
                layer=0,
                head=1,
                direction=np.asarray([1.0, 0.0]),
                sigma=0.5,
                validation_accuracy=1.0,
            ),
        ),
        alpha=2.0,
        num_attention_heads=4,
        head_dim=2,
    )


def test_hook_bites_detect_expected_delta_and_reject_noop():
    config = _simple_config()
    before = {0: np.zeros((2, 8))}
    after = {0: np.zeros((2, 8))}
    after[0][:, 2] = 1.0
    assert hook_bite_metrics(before, after, config)["passed"] is True
    assert hook_bite_metrics(before, before, config)["passed"] is False


def test_tiny_model_attention_pre_hook_edits_only_last_token_and_cleans_hooks():
    torch = pytest.importorskip("torch")

    class TinyAttention(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.o_proj = torch.nn.Identity()

        def forward(self, hidden):
            return self.o_proj(hidden)

    class TinyBlock(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.self_attn = TinyAttention()

        def forward(self, hidden):
            return self.self_attn(hidden)

    class TinyCore(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = torch.nn.ModuleList([TinyBlock(), TinyBlock()])

    class TinyLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = TinyCore()

    class TinyTokenizer:
        pad_token = "<pad>"
        eos_token = "</s>"
        padding_side = "left"

    config_obj = SimpleNamespace(
        hidden_size=8,
        num_hidden_layers=2,
        num_attention_heads=4,
    )
    model = TinyLM()
    backend = OfficialITIHFBackend(
        "tiny",
        model=model,
        tokenizer=TinyTokenizer(),
        config=config_obj,
    )
    handles = backend._register_iti_hooks(_simple_config())
    hidden = torch.zeros((2, 3, 8), dtype=torch.float32)
    try:
        output = model.model.layers[0](hidden)
    finally:
        for handle in reversed(handles):
            handle.remove()
    assert torch.all(output[:, :-1, :] == 0)
    assert torch.all(output[:, -1, 2] == 1.0)
    assert torch.count_nonzero(output[:, -1, :]) == 2
    assert not model.model.layers[0].self_attn.o_proj._forward_pre_hooks


def test_transformers_4_44_2_llama_eager_o_proj_hook_shape_and_delta():
    torch = pytest.importorskip("torch")
    import transformers
    from transformers import LlamaConfig, LlamaForCausalLM

    assert transformers.__version__ == REQUIRED_TRANSFORMERS_VERSION
    config_obj = LlamaConfig(
        vocab_size=32,
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=2,
        max_position_embeddings=32,
    )
    config_obj._attn_implementation = "eager"
    model = LlamaForCausalLM(config_obj).eval()
    tokenizer = SimpleNamespace(
        pad_token="<pad>",
        eos_token="</s>",
        padding_side="left",
    )
    backend = OfficialITIHFBackend(
        "tiny-llama",
        model=model,
        tokenizer=tokenizer,
        config=model.config,
    )
    iti_config = OfficialITIConfig(
        specs=(
            ITIHeadSpec(
                layer=0,
                head=1,
                direction=np.asarray([1.0, 0.0, 0.0, 0.0]),
                sigma=0.5,
                validation_accuracy=1.0,
            ),
        ),
        alpha=2.0,
        num_attention_heads=2,
        head_dim=4,
    )
    stats = {}
    handles = backend._register_iti_hooks(
        iti_config, stats_by_layer=stats
    )
    try:
        with torch.no_grad():
            model.model(
                input_ids=torch.tensor([[1, 2, 3]], dtype=torch.long),
                use_cache=False,
            )
    finally:
        for handle in reversed(handles):
            handle.remove()
    before = {0: np.concatenate(stats[0]["before"], axis=0)}
    after = {0: np.concatenate(stats[0]["after"], axis=0)}
    assert before[0].shape == after[0].shape == (1, 8)
    assert hook_bite_metrics(before, after, iti_config)["passed"] is True
    assert not model.model.layers[0].self_attn.o_proj._forward_pre_hooks


def test_effective_generation_config_overrides_model_top_p_and_top_k():
    torch = pytest.importorskip("torch")
    from transformers import GenerationConfig

    class TinyAttention(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.o_proj = torch.nn.Identity()

    class TinyBlock(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.self_attn = TinyAttention()

    class TinyCore(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = torch.nn.ModuleList([TinyBlock()])

    class TinyLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = TinyCore()
            self.generation_config = GenerationConfig(
                do_sample=True, top_p=0.9, top_k=50, temperature=1.3
            )

    class TinyTokenizer:
        pad_token = "<pad>"
        eos_token = "<|eot_id|>"
        padding_side = "left"
        pad_token_id = 128009
        eos_token_id = 128009
        bos_token_id = 128000

        @staticmethod
        def convert_ids_to_tokens(token_ids):
            mapping = {
                128001: "<|end_of_text|>",
                128009: "<|eot_id|>",
            }
            return [mapping[token_id] for token_id in token_ids]

    backend = OfficialITIHFBackend(
        "tiny",
        model=TinyLM(),
        tokenizer=TinyTokenizer(),
        config=SimpleNamespace(
            hidden_size=8,
            num_hidden_layers=1,
            num_attention_heads=4,
        ),
    )
    generation_kwargs, effective = backend.effective_generation_config(
        max_new_tokens=64,
        do_sample=True,
        temperature=0.7,
    )
    assert effective["top_p"] == 1.0
    assert effective["top_k"] == 0
    assert effective["temperature"] == 0.7
    assert effective["eos_token_id"] == [128001, 128009]
    supported_frozen = {
        key: value
        for key, value in FROZEN_SAMPLING_CONFIG.items()
        if key in effective
    }
    assert {
        key: effective[key] for key in supported_frozen
    } == supported_frozen
    assert (
        set(FROZEN_SAMPLING_CONFIG) - set(effective)
        == set(TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS)
    )
    runtime_fields = set(GenerationConfig().to_dict()) - {
        "_from_model_config",
        "transformers_version",
    }
    assert set(generation_kwargs) == runtime_fields
    assert generation_kwargs == effective


def test_official_backend_release_is_irreversible_and_memory_guarded(monkeypatch):
    torch = pytest.importorskip("torch")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    class TinyLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = SimpleNamespace(
                layers=torch.nn.ModuleList([torch.nn.Identity()])
            )

    tokenizer = SimpleNamespace(
        pad_token="<pad>",
        eos_token="<eos>",
        padding_side="left",
    )
    backend = OfficialITIHFBackend(
        "tiny",
        model=TinyLM(),
        tokenizer=tokenizer,
        config=SimpleNamespace(
            hidden_size=8,
            num_hidden_layers=1,
            num_attention_heads=1,
        ),
    )
    report = backend.release_for_sequential_judging()
    assert report["after"]["released"] is True
    assert report["after"]["allocated_bytes"] <= MAX_POST_UNLOAD_CUDA_BYTES
    with pytest.raises(RuntimeError, match="irreversibly released"):
        backend._ensure_loaded()
    with pytest.raises(RuntimeError, match="already released"):
        backend.release_for_sequential_judging()


def test_transformers_4_44_2_is_explicit_and_other_versions_fail_closed():
    compatibility = assert_transformers_compatibility("4.44.2")
    assert compatibility["installed_version"] == "4.44.2"
    assert compatibility["protocol_only_neutral_fields"] == (
        TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS
    )
    with pytest.raises(RuntimeError, match="requires exact Transformers 4.44.2"):
        assert_transformers_compatibility("4.45.0")


def test_frozen_multi_eos_mapping_and_second_eos_stops_without_truncation():
    class PinnedTokenizer:
        eos_token_id = 128009

        @staticmethod
        def convert_ids_to_tokens(token_ids):
            mapping = {
                128001: "<|end_of_text|>",
                128009: "<|eot_id|>",
            }
            return [mapping[token_id] for token_id in token_ids]

    mapping = validate_frozen_eos_mapping(PinnedTokenizer())
    assert tuple(mapping["eos_token_ids"]) == FROZEN_EOS_TOKEN_IDS
    assert tuple(mapping["eos_token_strings"]) == FROZEN_EOS_TOKEN_STRINGS
    assert generation_was_truncated(
        [7] * 63 + [128009], max_new_tokens=64
    ) is False
    assert generation_was_truncated(
        [7] * 63 + [128001], max_new_tokens=64
    ) is False
    assert generation_was_truncated([7] * 64, max_new_tokens=64) is True

    class SwappedTokenizer(PinnedTokenizer):
        @staticmethod
        def convert_ids_to_tokens(token_ids):
            return ["<|eot_id|>", "<|end_of_text|>"]

    with pytest.raises(RuntimeError, match="EOS mapping mismatch"):
        validate_frozen_eos_mapping(SwappedTokenizer())


def test_judge_effective_generation_config_overrides_model_defaults():
    pytest.importorskip("torch")
    from transformers import GenerationConfig

    class TinyModel:
        generation_config = GenerationConfig(
            do_sample=True,
            num_beams=4,
            top_p=0.2,
            temperature=1.8,
        )

    tokenizer = SimpleNamespace(
        pad_token_id=0,
        eos_token_id=1,
        bos_token_id=2,
    )
    generation_kwargs, effective = LocalTruthInfoJudge._effective_generation_config(
        TinyModel(), tokenizer
    )
    assert generation_kwargs == effective
    assert effective["do_sample"] is False
    assert effective["num_beams"] == 1
    assert effective["num_return_sequences"] == 1
    assert effective["max_new_tokens"] == 3
    assert effective["max_length"] is None


def test_fold_configs_are_atomic_full_identity_bound_and_resume_rejects_mismatch(
    tmp_path, monkeypatch
):
    config = _simple_config()
    monkeypatch.setattr(
        runner,
        "_fit_fold_configs",
        lambda items, splits, backend, *, activation_batch_size: (
            {0: config},
            {
                "0": {
                    "hook_bites": {"passed": True},
                    "activation_batch_size": activation_batch_size,
                }
            },
        ),
    )

    class Backend:
        def assert_hook_bites(self, prompts, persisted):
            assert persisted.to_dict() == config.to_dict()
            return {"passed": True}

    path = tmp_path / "fold_configs.json"
    identity = {
        "data": "hash-a",
        "model": "hash-b",
        "environment": "hash-c",
    }
    configs, payload = runner._load_or_create_fold_config_manifest(
        path=path,
        identity=identity,
        items=[],
        splits=[],
        backend=Backend(),
        activation_batch_size=1,
    )
    assert configs[0].to_dict() == config.to_dict()
    assert payload["fold_configs_hash"] == config_hash(payload["fold_configs"])
    resumed, _ = runner._load_or_create_fold_config_manifest(
        path=path,
        identity=identity,
        items=[],
        splits=[],
        backend=Backend(),
        activation_batch_size=1,
    )
    assert resumed[0].to_dict() == config.to_dict()
    with pytest.raises(ValueError, match="data/model/environment"):
        runner._load_or_create_fold_config_manifest(
            path=path,
            identity={**identity, "environment": "changed"},
            items=[],
            splits=[],
            backend=Backend(),
            activation_batch_size=1,
        )


def test_pinned_snapshot_verifies_git_blob_lfs_and_all_file_sha256(
    tmp_path, monkeypatch
):
    git_raw = b"small config"
    lfs_raw = b"weight shard"
    git_oid = hashlib.sha1(
        f"blob {len(git_raw)}\0".encode() + git_raw
    ).hexdigest()
    monkeypatch.setitem(
        PINNED_SNAPSHOTS,
        "tiny",
        {
            "repo_id": "owner/tiny",
            "repo_type": "model",
            "revision": "abc",
            "files": {
                "config.json": {"size": len(git_raw), "git_oid": git_oid},
                "model.bin": {
                    "size": len(lfs_raw),
                    "lfs_sha256": hashlib.sha256(lfs_raw).hexdigest(),
                },
            },
        },
    )
    (tmp_path / "config.json").write_bytes(git_raw)
    (tmp_path / "model.bin").write_bytes(lfs_raw)
    identity = verify_pinned_snapshot("tiny", tmp_path)
    assert identity["files"]["config.json"]["sha256"] == hashlib.sha256(
        git_raw
    ).hexdigest()
    (tmp_path / "unexpected.txt").write_text("stale", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory mismatch"):
        verify_pinned_snapshot("tiny", tmp_path)
    (tmp_path / "unexpected.txt").unlink()
    (tmp_path / "model.bin").write_bytes(b"forged shard")
    with pytest.raises(ValueError, match="size mismatch|LFS SHA-256"):
        verify_pinned_snapshot("tiny", tmp_path)
    assert (
        PINNED_SNAPSHOTS["generator"]["files"]["tokenizer.json"]["git_oid"]
        == "b197f72effb9d5ed16ee0f5663e11e4cfac2ba62"
    )
    assert (
        PINNED_SNAPSHOTS["truth_judge"]["files"]["tokenizer_config.json"][
            "git_oid"
        ]
        == "a933e74dc87d5d5e5d8820a71f035c5ce3dac12f"
    )


def test_pinned_download_populates_only_the_standard_hub_cache(
    tmp_path, monkeypatch
):
    import huggingface_hub

    revision = "b" * 40
    monkeypatch.setitem(
        PINNED_SNAPSHOTS,
        "tiny-download",
        {
            "repo_id": "owner/tiny-download",
            "repo_type": "model",
            "revision": revision,
            "files": {"config.json": {"size": 6}},
        },
    )
    calls = []

    def fake_hf_hub_download(**kwargs):
        calls.append(kwargs)
        snapshot = (
            Path(kwargs["cache_dir"])
            / "models--owner--tiny-download"
            / "snapshots"
            / revision
        )
        snapshot.mkdir(parents=True, exist_ok=True)
        path = snapshot / kwargs["filename"]
        path.write_bytes(b"pinned")
        return str(path)

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fake_hf_hub_download)
    identity = download_pinned_snapshot("tiny-download", tmp_path)

    assert identity["expected_snapshot_bytes"] == 6
    assert calls == [
        {
            "repo_id": "owner/tiny-download",
            "filename": "config.json",
            "revision": revision,
            "repo_type": "model",
            "cache_dir": str(tmp_path / "hub"),
        }
    ]
    assert not (tmp_path / "tiny-download").exists()


@pytest.mark.parametrize(
    "name, repo_type",
    [
        ("generator", "model"),
        ("truth_judge", "model"),
        ("info_judge", "model"),
        ("truthfulqa", "dataset"),
    ],
)
def test_pinned_resolver_rejects_same_files_from_different_revision(
    name, repo_type, tmp_path, monkeypatch
):
    import huggingface_hub

    pinned_revision = "c" * 40
    wrong_revision = "d" * 40
    repo_id = f"owner/{name}"
    monkeypatch.setitem(
        PINNED_SNAPSHOTS,
        name,
        {
            "repo_id": repo_id,
            "repo_type": repo_type,
            "revision": pinned_revision,
            "files": {"payload.bin": {"size": 6}},
        },
    )
    wrong_file = (
        tmp_path
        / "hub"
        / (f"{repo_type}s--" + repo_id.replace("/", "--"))
        / "snapshots"
        / wrong_revision
        / "payload.bin"
    )
    wrong_file.parent.mkdir(parents=True)
    wrong_file.write_bytes(b"pinned")
    monkeypatch.setattr(
        huggingface_hub,
        "try_to_load_from_cache",
        lambda **kwargs: str(wrong_file),
    )

    with pytest.raises(RuntimeError, match="outside pinned Hub revision"):
        resolve_pinned_snapshot_path(name, tmp_path)


def test_truthfulqa_loader_joins_exact_configs_and_rejects_question_set_drift(
    tmp_path, monkeypatch
):
    generation_rows = [
        {
            "question": "Question one?",
            "correct_answers": ["Correct one"],
            "incorrect_answers": ["Incorrect one"],
        },
        {
            "question": "Question two?",
            "correct_answers": ["Correct two"],
            "incorrect_answers": ["Incorrect two"],
        },
    ]
    multiple_choice_rows = [
        {
            "question": "Question two? ",
            "mc2_targets": {
                "choices": ["Correct two", "Incorrect two"],
                "labels": [1, 0],
            },
        },
        {
            "question": "Question one?",
            "mc2_targets": {
                "choices": ["Incorrect one", "Correct one"],
                "labels": [0, 1],
            },
        },
    ]
    calls = []
    pyarrow = ModuleType("pyarrow")
    parquet = ModuleType("pyarrow.parquet")

    def fake_read_table(path):
        path = str(path)
        calls.append(path)
        if "generation" in path:
            return SimpleNamespace(to_pylist=lambda: generation_rows)
        if "multiple_choice" in path:
            return SimpleNamespace(to_pylist=lambda: multiple_choice_rows)
        raise AssertionError(f"unexpected TruthfulQA config path: {path}")

    parquet.read_table = fake_read_table
    pyarrow.parquet = parquet
    monkeypatch.setitem(sys.modules, "pyarrow", pyarrow)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", parquet)
    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control.TRUTHFULQA_N", 2
    )

    def question_order_hash(rows):
        return hashlib.sha256(
            json.dumps(
                [row["question"] for row in rows],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

    canonical_order_hash = question_order_hash(multiple_choice_rows)
    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control."
        "TRUTHFULQA_CANONICAL_ORDER_SHA256",
        canonical_order_hash,
    )
    pinned_snapshot = tmp_path / "hub" / "pinned-truthfulqa"
    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control."
        "resolve_pinned_snapshot_path",
        lambda name, cache_root: pinned_snapshot,
    )
    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control."
        "verify_pinned_snapshot",
        lambda name, snapshot_dir: {"name": name},
    )

    items = load_pinned_truthfulqa(tmp_path)
    assert [item.question for item in items] == [
        "Question two? ",
        "Question one?",
    ]
    assert items[0].correct_answers == ("Correct two",)
    assert items[1].mc2_choices == ("Incorrect one", "Correct one")
    assert "generation/validation-00000-of-00001.parquet" in calls[0].replace(
        "\\", "/"
    )
    assert (
        "multiple_choice/validation-00000-of-00001.parquet"
        in calls[1].replace("\\", "/")
    )

    multiple_choice_rows.reverse()
    with pytest.raises(ValueError, match="canonical multiple_choice row order"):
        load_pinned_truthfulqa(tmp_path)
    multiple_choice_rows.reverse()

    multiple_choice_rows[0] = {
        "question": "Wrong config question?",
        "mc2_targets": {
            "choices": ["Wrong", "Also wrong"],
            "labels": [1, 0],
        },
    }
    monkeypatch.setattr(
        "cognitive_console.eval.truthfulqa_positive_control."
        "TRUTHFULQA_CANONICAL_ORDER_SHA256",
        question_order_hash(multiple_choice_rows),
    )
    with pytest.raises(ValueError, match="config question set mismatch"):
        load_pinned_truthfulqa(tmp_path)


def test_checkpoint_resume_rejects_unknown_and_preserves_order(tmp_path):
    jobs = [
        GenerationJob(0, "dev", "baseline", OFFICIAL_BASE_PROMPT_ID, "a", 0, i, 7 + i)
        for i in range(2)
    ]
    cfg = config_hash({"x": 1})
    binding = {
        "run_config_hash": cfg,
        "fold_config_file_sha256": "a" * 64,
        "fold_configs_hash": "b" * 64,
        "data_identity": {"canonical_items_hash": "c" * 64},
        "model_identity": {"snapshot_hash": "d" * 64},
        "environment_identity": {"fingerprint_hash": "e" * 64},
    }
    checkpoint = JsonlCheckpoint(
        tmp_path / "records.jsonl",
        run_config_hash=cfg,
        jobs=jobs,
        checkpoint_binding=binding,
    )
    first = GenerationRecord.build(
        jobs[0],
        run_config_hash=cfg,
        output_text="answer",
        token_count=1,
        truncated=False,
        truth=True,
        informative=True,
        truth_raw="yes",
        info_raw="yes",
    )
    checkpoint.append(first)
    resumed = JsonlCheckpoint(
        tmp_path / "records.jsonl",
        run_config_hash=cfg,
        jobs=jobs,
        checkpoint_binding=binding,
    )
    assert resumed.pending() == [jobs[1]]
    second = GenerationRecord.build(
        jobs[1],
        run_config_hash=cfg,
        output_text="answer two",
        token_count=2,
        truncated=False,
        truth=False,
        informative=True,
        truth_raw="no",
        info_raw="yes",
    )
    resumed.append(second)
    assert [row.job_id for row in resumed.ordered_records()] == [
        job.job_id for job in jobs
    ]
    with pytest.raises(ValueError, match="identity mismatch"):
        JsonlCheckpoint(
            tmp_path / "records.jsonl",
            run_config_hash=cfg,
            jobs=jobs,
            checkpoint_binding={
                **binding,
                "environment_identity": {"fingerprint_hash": "changed"},
            },
        )


def test_common_random_seed_is_condition_independent():
    seed = deterministic_sample_seed(3, fold=1, item_id="x", sample_index=2)
    assert SAMPLE_SEED_MAPPING_VERSION == "sha256-v1-utf8-pipe-mod-2pow31"
    assert seed == 97396565
    assert seed == deterministic_sample_seed(3, fold=1, item_id="x", sample_index=2)
    assert seed != deterministic_sample_seed(3, fold=1, item_id="x", sample_index=3)
    assert (
        deterministic_sample_seed(
            20260811,
            fold=0,
            item_id="truthfulqa-0000",
            sample_index=0,
        )
        == 1462874046
    )
    assert (
        deterministic_sample_seed(
            20260811,
            fold=1,
            item_id="truthfulqa-0816",
            sample_index=4,
        )
        == 629855610
    )
    assert [
        20260811 + RANDOM_DIRECTION_SEED_OFFSET + fold for fold in range(2)
    ] == [20261720, 20261721]
    assert PRIMARY_BOOTSTRAP_SEED == 20260811
    assert RANDOM_BOOTSTRAP_SEED == 20260812
    assert NUMPY_RNG_ALGORITHM == "numpy.random.Generator(numpy.random.PCG64)"
    assert BOOTSTRAP_PERCENTILE_METHOD == "linear"
    assert type(pcg64_rng(1).bit_generator).__name__ == "PCG64"


def _authorization_fixture(monkeypatch, tmp_path):
    key = "k" * 40
    monkeypatch.setenv(AUTHORIZATION_KEY_ENV, key)
    registry = tmp_path / "global" / "attempts.jsonl"
    registry.parent.mkdir(parents=True)
    if os.name == "posix":
        registry.parent.chmod(0o700)
    monkeypatch.setattr(
        "cognitive_console.experiments.iti_positive_control.global_attempt_registry_path",
        lambda: registry,
    )
    profile = {
        "schema_version": 1,
        "hostname": "designated-a800",
        "system": "Linux",
        "release": "test",
        "machine": "x86_64",
        "machine_id_sha256": "a" * 64,
        "effective_uid": 1000,
        "effective_user": "runner",
        "registry_path": str(registry),
    }
    profile["fingerprint_hash"] = config_hash(profile)
    monkeypatch.setattr(
        "cognitive_console.experiments.iti_positive_control.designated_host_profile",
        lambda: profile,
    )
    manifest = {
        "schema_version": 3,
        "authorization_nonce": "b" * 64,
        "experiment_id": EXPERIMENT_ID,
        "code_commit": "abc",
        "audited_dev_artifact_sha256": "d" * 64,
        "audited_dev_artifact_manifest_sha256": "e" * 64,
        "audited_execution_fingerprint_hash": "sha256:" + "f" * 64,
        "designated_host_fingerprint": profile["fingerprint_hash"],
        "registry_path": str(registry),
        "issued_at": "2026-08-11T19:00:00+08:00",
        "key_id": "owner-local-v1",
    }
    manifest["signature_hmac_sha256"] = hmac.new(
        key.encode(),
        authorization_signing_bytes(manifest),
        hashlib.sha256,
    ).hexdigest()
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, registry


def _consume_authorization(path, out_dir):
    return consume_signed_test_authorization(
        authorization_manifest=path,
        code_commit="abc",
        audited_dev_artifact_sha256="d" * 64,
        audited_dev_artifact_manifest_sha256="e" * 64,
        audited_execution_fingerprint_hash="sha256:" + "f" * 64,
        out_dir=out_dir,
    )


def test_signed_host_registry_is_atomic_and_cross_home_cross_outdir(
    monkeypatch, tmp_path
):
    path, registry = _authorization_fixture(monkeypatch, tmp_path)
    with pytest.raises(PermissionError, match="commit mismatch"):
        consume_signed_test_authorization(
            authorization_manifest=path,
            code_commit="wrong",
            audited_dev_artifact_sha256="d" * 64,
            audited_dev_artifact_manifest_sha256="e" * 64,
            audited_execution_fingerprint_hash="sha256:" + "f" * 64,
            out_dir=tmp_path / "run-a",
        )
    first = _consume_authorization(path, tmp_path / "run-a")
    assert first["status"] == "CONSUMED"
    assert first["sequence"] == 1
    assert first["previous_record_hash"]
    assert first["record_hash"] == config_hash(
        {key: value for key, value in first.items() if key != "record_hash"}
    )
    monkeypatch.setenv("HOME", str(tmp_path / "other-home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "other-profile"))
    with pytest.raises(PermissionError, match="already consumed globally"):
        _consume_authorization(path, tmp_path / "run-a")
    with pytest.raises(PermissionError, match="already consumed globally"):
        _consume_authorization(path, tmp_path / "run-b")
    assert registry.is_file()
    assert len(registry.read_text(encoding="utf-8").splitlines()) == 1


def test_signed_host_registry_concurrent_consumption_has_one_winner(
    monkeypatch, tmp_path
):
    path, registry = _authorization_fixture(monkeypatch, tmp_path)

    def attempt(index):
        try:
            return _consume_authorization(path, tmp_path / f"run-{index}")
        except PermissionError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, PermissionError) for result in results) == 1
    assert len(registry.read_text(encoding="utf-8").splitlines()) == 1


def test_signed_host_registry_rejects_hash_chain_tampering(monkeypatch, tmp_path):
    path, registry = _authorization_fixture(monkeypatch, tmp_path)
    _consume_authorization(path, tmp_path / "run-a")
    if os.name == "posix":
        registry.chmod(0o600)
    row = json.loads(registry.read_text(encoding="utf-8"))
    row["out_dir_sha256"] = "0" * 64
    registry.write_text(json.dumps(row) + "\n", encoding="utf-8")
    if os.name == "posix":
        registry.chmod(0o400)
    with pytest.raises(ValueError, match="record hash mismatch"):
        _consume_authorization(path, tmp_path / "run-b")


def test_signed_authorization_refuses_host_path_and_profile_drift(
    monkeypatch, tmp_path
):
    path, registry = _authorization_fixture(monkeypatch, tmp_path)
    key = os.environ[AUTHORIZATION_KEY_ENV]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["registry_path"] = str(tmp_path / "alternate" / "attempts.jsonl")
    manifest["signature_hmac_sha256"] = hmac.new(
        key.encode(),
        authorization_signing_bytes(manifest),
        hashlib.sha256,
    ).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(PermissionError, match="registry path mismatch"):
        _consume_authorization(path, tmp_path / "run-a")

    manifest["registry_path"] = str(registry)
    manifest["signature_hmac_sha256"] = hmac.new(
        key.encode(),
        authorization_signing_bytes(manifest),
        hashlib.sha256,
    ).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    drifted_profile = {
        "schema_version": 1,
        "hostname": "different-a800-host",
        "system": "Linux",
        "release": "test",
        "machine": "x86_64",
        "machine_id_sha256": "a" * 64,
        "effective_uid": 1000,
        "effective_user": "runner",
        "registry_path": str(registry),
    }
    drifted_profile["fingerprint_hash"] = config_hash(drifted_profile)
    monkeypatch.setattr(
        "cognitive_console.experiments.iti_positive_control.designated_host_profile",
        lambda: drifted_profile,
    )
    with pytest.raises(PermissionError, match="host fingerprint mismatch"):
        _consume_authorization(path, tmp_path / "run-a")


@pytest.mark.parametrize(
    "section",
    [
        "generator",
        "gpu",
        "hardware_profile",
        "host_binding",
        "attention",
        "transformers_compatibility",
        "dependencies",
        "judges",
    ],
)
def test_test_execution_fingerprint_rejects_every_audited_dimension(section):
    preflight = {
        "generator_snapshot_identity": {"snapshot_hash": "a" * 64},
        "model_config_hash": "b" * 64,
        "tokenizer_class": "PinnedTokenizer",
        "tokenizer_vocab_size": 128256,
        "eos_token_mapping": {
            "eos_token_ids": [128001, 128009],
            "eos_token_strings": ["<|end_of_text|>", "<|eot_id|>"],
            "primary_eos_token_id": 128009,
        },
        "effective_generation_config": {"eos_token_id": [128001, 128009]},
        "gpu": {
            "cuda_device_order": "PCI_BUS_ID",
            "cuda_visible_devices": "1",
            "logical_index": 0,
            "selected_visible_token": "1",
            "physical_identity": {
                "uuid": "GPU-A800",
                "pci_bus_id": "00000000:65:00.0",
            },
        },
        "attention_implementation": "eager",
        "attention_layers": [{"layer": 0, "source_sha256": "c" * 64}],
        "hardware_profile": {"name": runner.DEFAULT_HARDWARE_PROFILE},
        "host_binding": {"fingerprint_hash": "host-a"},
        "transformers_compatibility": {
            "required_version": REQUIRED_TRANSFORMERS_VERSION
        },
        "environment": {"packages": {"transformers": "x"}},
    }
    current = runner._execution_fingerprint(
        preflight=preflight,
        judge_snapshot_identities={
            "truth": {"snapshot_hash": "d" * 64},
            "info": {"snapshot_hash": "f" * 64},
        },
        judge_runtime_fingerprints={
            "truth": {"source_sha256": "e" * 64},
            "info": {"source_sha256": "0" * 64},
        },
    )
    assert current["schema_version"] == runner.EXECUTION_FINGERPRINT_SCHEMA_VERSION
    runner._assert_execution_fingerprint_matches_dev(
        {"execution_fingerprint": current}, current
    )
    drifted = copy.deepcopy(current)
    drifted[section]["adversarial_drift"] = True
    unhashed = dict(drifted)
    unhashed.pop("fingerprint_hash")
    drifted["fingerprint_hash"] = config_hash(unhashed)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        runner._assert_execution_fingerprint_matches_dev(
            {"execution_fingerprint": current}, drifted
        )


@pytest.mark.parametrize(
    "field, changed",
    [
        ("uuid", "GPU-OTHER"),
        ("pci_bus_id", "00000000:B2:00.0"),
    ],
)
def test_execution_fingerprint_exactly_binds_physical_gpu(field, changed):
    preflight = {
        "generator_snapshot_identity": {"snapshot_hash": "a" * 64},
        "model_config_hash": "b" * 64,
        "tokenizer_class": "PinnedTokenizer",
        "tokenizer_vocab_size": 128256,
        "eos_token_mapping": {"eos_token_ids": [128001, 128009]},
        "effective_generation_config": {"eos_token_id": [128001, 128009]},
        "gpu": {
            "physical_identity": {
                "uuid": "GPU-A800",
                "pci_bus_id": "00000000:65:00.0",
            },
        },
        "attention_implementation": "eager",
        "attention_layers": [{"layer": 0, "source_sha256": "c" * 64}],
        "hardware_profile": {"name": runner.DEFAULT_HARDWARE_PROFILE},
        "host_binding": {"fingerprint_hash": "host-a"},
        "transformers_compatibility": {
            "required_version": REQUIRED_TRANSFORMERS_VERSION
        },
        "environment": {"packages": {"transformers": "x"}},
    }
    audited = runner._execution_fingerprint(
        preflight=preflight,
        judge_snapshot_identities={"truth": {}, "info": {}},
        judge_runtime_fingerprints={"truth": {}, "info": {}},
    )
    current = copy.deepcopy(audited)
    current["gpu"]["physical_identity"][field] = changed
    unhashed = dict(current)
    unhashed.pop("fingerprint_hash")
    current["fingerprint_hash"] = config_hash(unhashed)
    with pytest.raises(ValueError, match="physical GPU UUID/PCI"):
        runner._assert_execution_fingerprint_matches_dev(
            {"execution_fingerprint": audited},
            current,
        )


def test_gpu_identity_maps_cuda_logical_index_to_physical_uuid_and_pci(
    monkeypatch,
):
    monkeypatch.setenv("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "GPU-A,GPU-B")
    properties = SimpleNamespace(
        pci_bus_id="0000:65:00.0",
        uuid="GPU-B",
    )

    def fake_run(command, **kwargs):
        assert kwargs == {
            "capture_output": True,
            "text": True,
            "check": False,
        }
        assert command[1] == "--id=00000000:65:00.0"
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "3, GPU-B, 00000000:65:00.0, 570.1, "
                "NVIDIA A800 80GB PCIe, 81920, 8.0\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    identity = runner._selected_physical_gpu_identity(
        device_index=1,
        properties=properties,
    )
    assert identity["logical_index"] == 1
    assert identity["selected_visible_token"] == "GPU-B"
    assert identity["visible_device_tokens"] == ["GPU-A", "GPU-B"]
    assert identity["physical_identity"] == {
        "nvidia_smi_index": 3,
        "uuid": "GPU-B",
        "pci_bus_id": "00000000:65:00.0",
    }


def test_gpu_identity_uses_cuda_pci_not_numeric_visible_index(monkeypatch):
    monkeypatch.delenv("CUDA_DEVICE_ORDER", raising=False)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "1,0")
    properties = SimpleNamespace(
        pci_domain_id=0,
        pci_bus_id=0xB2,
        pci_device_id=0,
        uuid="GPU-PHYSICAL-ONE",
    )

    def fake_run(command, **kwargs):
        del kwargs
        assert command[1] == "--id=00000000:B2:00.0"
        assert "--id=1" not in command
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "1, GPU-PHYSICAL-ONE, 00000000:B2:00.0, 570.1, "
                "NVIDIA A800 80GB PCIe, 81920, 8.0\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    identity = runner._selected_physical_gpu_identity(
        device_index=0,
        properties=properties,
    )
    assert identity["selected_visible_token"] == "1"
    assert identity["physical_identity"]["nvidia_smi_index"] == 1
    assert identity["physical_identity"]["uuid"] == "GPU-PHYSICAL-ONE"


def _authorized_autodl_runtime():
    return {
        "cuda_name": "NVIDIA GeForce RTX 4080 SUPER",
        "physical_name": "NVIDIA GeForce RTX 4080 SUPER",
        "cuda_total_memory_bytes": 32760 * 1024**2,
        "physical_memory_mib": 32760,
        "cuda_device_count": 1,
        "visibility": {
            "cuda_visible_devices": "0",
            "visible_device_tokens": ["0"],
            "logical_index": 0,
            "selected_visible_token": "0",
        },
        "bf16_supported": True,
        "torch_version": "2.8.0+cu128",
        "torch_cuda": "12.8",
        "environment": {
            "python": "3.12.11",
            "packages": {
                "transformers": "4.44.2",
                "datasets": "2.21.0",
                "scikit-learn": "1.5.1",
                "accelerate": "0.34.2",
            },
        },
        "host_binding": {"fingerprint_hash": "authorized-autodl-host"},
    }


def test_owner_authorized_hardware_profiles_accept_a800_or_autodl():
    autodl = runner._validate_hardware_profile(
        runner.AUTODL_HARDWARE_PROFILE,
        runtime=_authorized_autodl_runtime(),
    )
    assert autodl["name"] == runner.AUTODL_HARDWARE_PROFILE
    a800_runtime = _authorized_autodl_runtime()
    a800_runtime.update(
        {
            "cuda_name": "NVIDIA A800 80GB PCIe",
            "physical_name": "NVIDIA A800 80GB PCIe",
            "cuda_total_memory_bytes": 80 * 1024**3,
            "physical_memory_mib": 81920,
        }
    )
    a800 = runner._validate_hardware_profile(
        runner.DEFAULT_HARDWARE_PROFILE,
        runtime=a800_runtime,
    )
    assert a800["name"] == runner.DEFAULT_HARDWARE_PROFILE


@pytest.mark.parametrize(
    "field, bad_value, error",
    [
        ("cuda_name", "NVIDIA RTX 4090", "allowlist"),
        ("cuda_device_count", 2, "one visible"),
        ("bf16_supported", False, "bf16"),
        ("torch_version", "2.7.1+cu126", "PyTorch 2.8"),
        ("torch_cuda", "11.8", "CUDA 12"),
    ],
)
def test_autodl_hardware_profile_rejects_unknown_or_drifted_runtime(
    field, bad_value, error
):
    runtime = _authorized_autodl_runtime()
    runtime[field] = bad_value
    with pytest.raises(RuntimeError, match=error):
        runner._validate_hardware_profile(
            runner.AUTODL_HARDWARE_PROFILE,
            runtime=runtime,
        )


def test_autodl_profile_binds_authorized_root_host_and_data_paths(monkeypatch):
    monkeypatch.setattr(
        runner.sys, "executable", "/root/miniconda3/bin/python"
    )
    host = {
        "system": "Linux",
        "effective_uid": 0,
        "effective_user": "root",
        "fingerprint_hash": "host-fingerprint",
    }
    binding = runner._assert_profile_host_paths(
        runner.AUTODL_HARDWARE_PROFILE,
        out_dir=Path("/root/autodl-tmp/runs/iti"),
        cache_root=Path("/root/autodl-tmp/hf"),
        host_profile=host,
    )
    assert binding["host_fingerprint"] == "host-fingerprint"
    with pytest.raises(RuntimeError, match="root user"):
        runner._assert_profile_host_paths(
            runner.AUTODL_HARDWARE_PROFILE,
            out_dir=Path("/root/autodl-tmp/runs/iti"),
            cache_root=Path("/root/autodl-tmp/hf"),
            host_profile={**host, "effective_uid": 1000},
        )


def _record(
    *,
    fold,
    condition,
    prompt_id,
    item_index,
    outcome,
    missing=False,
    truncated=False,
):
    job = GenerationJob(
        fold,
        "test",
        condition,
        prompt_id,
        f"item-{item_index}",
        item_index,
        0,
        10 + item_index,
    )
    return GenerationRecord.build(
        job,
        run_config_hash="cfg",
        output_text="ok",
        token_count=1,
        truncated=truncated,
        truth=bool(outcome) if not missing else None,
        informative=bool(outcome) if not missing else None,
        truth_raw="yes" if outcome else "no",
        info_raw="yes" if outcome else "no",
        missing=missing,
    )


def test_random_control_veto_and_missingness_gate_are_fail_closed():
    records = []
    for index in range(20):
        fold = index % 2
        winner = "winner"
        records.extend(
            [
                _record(
                    fold=fold,
                    condition="baseline",
                    prompt_id=OFFICIAL_BASE_PROMPT_ID,
                    item_index=index,
                    outcome=0,
                ),
                _record(
                    fold=fold,
                    condition="prompt",
                    prompt_id=winner,
                    item_index=index,
                    outcome=0,
                ),
                _record(
                    fold=fold,
                    condition="iti",
                    prompt_id=OFFICIAL_BASE_PROMPT_ID,
                    item_index=index,
                    outcome=1,
                ),
                _record(
                    fold=fold,
                    condition="random",
                    prompt_id=OFFICIAL_BASE_PROMPT_ID,
                    item_index=index,
                    outcome=1,
                ),
            ]
        )
    vetoed = adjudicate_test(
        records,
        fold_prompt_ids={0: "winner", 1: "winner"},
        k=1,
        bootstrap_seed=PRIMARY_BOOTSTRAP_SEED,
    )
    assert vetoed["status"] == "INVALID_RANDOM"
    assert vetoed["random_control"]["bootstrap_seed"] == RANDOM_BOOTSTRAP_SEED
    assert (
        vetoed["primary"]["bootstrap_rng_algorithm"]
        == NUMPY_RNG_ALGORITHM
    )
    assert (
        vetoed["primary"]["bootstrap_percentile_method"]
        == BOOTSTRAP_PERCENTILE_METHOD
    )
    with pytest.raises(ValueError, match="primary bootstrap seed"):
        adjudicate_test(
            records,
            fold_prompt_ids={0: "winner", 1: "winner"},
            k=1,
            bootstrap_seed=3,
        )

    missing_records = list(records)
    target = next(
        index
        for index, row in enumerate(missing_records)
        if row.condition == "iti"
    )
    row = missing_records[target]
    missing_records[target] = _record(
        fold=row.fold,
        condition=row.condition,
        prompt_id=row.prompt_id,
        item_index=row.item_index,
        outcome=0,
        missing=True,
    )
    invalid = adjudicate_test(
        missing_records,
        fold_prompt_ids={0: "winner", 1: "winner"},
        k=1,
        bootstrap_seed=PRIMARY_BOOTSTRAP_SEED,
    )
    assert invalid["status"] == "INVALID_MISSINGNESS_OR_TRUNCATION"


def test_dev_eligibility_fails_without_published_effect():
    records = []
    for index in range(10):
        fold = index % 2
        records.extend(
            [
                _record(
                    fold=fold,
                    condition="baseline",
                    prompt_id=OFFICIAL_BASE_PROMPT_ID,
                    item_index=index,
                    outcome=1,
                ),
                _record(
                    fold=fold,
                    condition="iti",
                    prompt_id=OFFICIAL_BASE_PROMPT_ID,
                    item_index=index,
                    outcome=0,
                ),
            ]
        )
    result = dev_eligibility(records, fold_prompt_ids={0: "x", 1: "x"}, k=1)
    assert result["status"] == "INVALID_SETUP"
    assert result["test_accessed"] is False


def test_hf_output_must_be_outside_source_repository(tmp_path):
    with pytest.raises(ValueError, match="outside the source repository"):
        runner._assert_external_hf_output(REPO / "results" / "bad")
    runner._assert_external_hf_output(tmp_path / "good")


def test_disk_limits_and_backend_phase_are_not_cli_overridable(
    tmp_path, monkeypatch
):
    assert runner.DISK_BUDGET_GB == 60.0
    assert runner.DISK_CEILING_GB == 70.0
    assert runner.PINNED_CONCURRENT_WORST_CASE_BYTES == 51615163245
    autodl = runner.HARDWARE_PROFILES[runner.AUTODL_HARDWARE_PROFILE]
    assert autodl.disk_budget_gib == 44.0
    assert autodl.disk_ceiling_gib == 47.0
    assert autodl.pinned_worst_case_bytes == 46246454125
    cache_variables = (
        "HF_HOME",
        "HF_HUB_CACHE",
        "HUGGINGFACE_HUB_CACHE",
        "HF_ASSETS_CACHE",
        "HF_XET_CACHE",
        "HF_DATASETS_CACHE",
        "HF_MODULES_CACHE",
        "TRANSFORMERS_CACHE",
        "XDG_CACHE_HOME",
        "TORCH_HOME",
    )
    for name in cache_variables:
        monkeypatch.setenv(name, "restore-after-test")
    cache_root = runner._configure_dedicated_caches(tmp_path / "external")
    for name in cache_variables:
        Path(os.environ[name]).resolve().relative_to(cache_root.resolve())
    parser = runner.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--backend",
                "hf",
                "--phase",
                "dev",
                "--disk-budget-gb",
                "10",
            ]
        )
    parsed = parser.parse_args(
        [
            "--backend",
            "hf",
            "--phase",
            "preflight",
            "--hardware-profile",
            runner.AUTODL_HARDWARE_PROFILE,
            "--activation-batch-size",
            "1",
        ]
    )
    assert parsed.hardware_profile == runner.AUTODL_HARDWARE_PROFILE


def test_pinned_worst_case_uses_standard_hub_cache_and_remains_fail_closed(
    tmp_path, monkeypatch
):
    revision = "a" * 40
    tiny_specs = {}
    for index, name in enumerate(
        ("generator", "truth_judge", "info_judge", "truthfulqa")
    ):
        repo_type = "dataset" if name == "truthfulqa" else "model"
        tiny_specs[name] = {
            "repo_id": f"owner/repo-{index}",
            "repo_type": repo_type,
            "revision": revision,
            "files": {"payload.bin": {"size": 10}},
        }
        monkeypatch.setitem(PINNED_SNAPSHOTS, name, tiny_specs[name])
        repo_folder = (
            f"{repo_type}s--"
            + str(tiny_specs[name]["repo_id"]).replace("/", "--")
        )
        snapshot = tmp_path / "hub" / repo_folder / "snapshots" / revision
        snapshot.mkdir(parents=True)
        (snapshot / "payload.bin").write_bytes(b"x" * 10)

    gib = 1024.0**3
    profile = runner.HardwareProfile(
        name="tiny-hub-cache",
        authorization_date="2026-08-12",
        activation_batch_size=1,
        disk_budget_gib=15 / gib,
        disk_ceiling_gib=100 / gib,
        artifact_reserve_bytes=10,
        require_dedicated_venv=False,
    )
    monkeypatch.setitem(runner.HARDWARE_PROFILES, profile.name, profile)
    monkeypatch.setattr(
        runner,
        "_disk_monitor",
        lambda *args, **kwargs: SimpleNamespace(total_gb=0.0),
    )
    monkeypatch.setattr(
        runner.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(free=100),
    )

    result = runner._assert_pinned_worst_case(
        tmp_path, tmp_path, profile.name
    )
    assert result["existing_by_snapshot"] == {
        name: 10 for name in tiny_specs
    }
    assert result["remaining_by_snapshot"] == {
        name: 0 for name in tiny_specs
    }
    assert cached_pinned_snapshot_bytes("generator", tmp_path) == 10
    assert resolve_pinned_snapshot_path("generator", tmp_path).name == revision

    missing = resolve_pinned_snapshot_path("generator", tmp_path) / "payload.bin"
    missing.unlink()
    with pytest.raises(RuntimeError, match="planning budget"):
        runner._assert_pinned_worst_case(tmp_path, tmp_path, profile.name)

    physical_profile = runner.HardwareProfile(
        name="tiny-physical-disk",
        authorization_date="2026-08-12",
        activation_batch_size=1,
        disk_budget_gib=100 / gib,
        disk_ceiling_gib=100 / gib,
        artifact_reserve_bytes=10,
        require_dedicated_venv=False,
    )
    monkeypatch.setitem(
        runner.HARDWARE_PROFILES, physical_profile.name, physical_profile
    )
    monkeypatch.setattr(
        runner.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(free=19),
    )
    with pytest.raises(RuntimeError, match="data disk cannot fit"):
        runner._assert_pinned_worst_case(
            tmp_path, tmp_path, physical_profile.name
        )


def test_per_row_judge_exception_becomes_missing_and_next_row_continues(
    tmp_path, monkeypatch
):
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )

    def fake_load(kind, model_id, revision, cache_dir):
        cache_dir.mkdir(parents=True, exist_ok=True)
        judge.snapshot_identities[kind] = {
            "name": kind,
            "revision": revision,
            "files": {},
        }
        judge.runtime_fingerprints[kind] = {
            "model_id": model_id,
            "revision": revision,
            "attention_implementation": "eager",
        }
        return object(), object()

    calls = {"count": 0}

    def fake_generate(model, tokenizer, prompt):
        calls["count"] += 1
        if "bad question" in prompt:
            raise RuntimeError("row failure")
        return "yes"

    monkeypatch.setattr(judge, "_load", fake_load)
    monkeypatch.setattr(judge, "_generate_label", fake_generate)
    scores = judge.score_many(
        [("bad question", "answer"), ("good question", "answer")],
        identities=["bad", "good"],
        checkpoint_root=tmp_path / "judge-checkpoints",
    )
    assert scores[0].valid is False
    assert scores[0].outcome == 0.0
    assert scores[0].truth_raw.startswith("ERROR:RuntimeError")
    assert scores[1].valid is True
    assert calls["count"] == 4


def test_resume_after_partial_final_checkpoint_keeps_full_judge_identity(tmp_path):
    items = [
        SimpleNamespace(item_id=f"item-{index}", index=index, question=f"Q{index}?")
        for index in range(2)
    ]
    jobs = [
        GenerationJob(
            0,
            "dev",
            "baseline",
            OFFICIAL_BASE_PROMPT_ID,
            item.item_id,
            item.index,
            0,
            100 + item.index,
        )
        for item in items
    ]
    run_hash = config_hash({"run": "stable"})
    binding = {"run_config_hash": run_hash, "fold_configs_hash": "a" * 64}

    class Generator:
        calls = 0

        def generate_with_metadata(self, prompt, **kwargs):
            del kwargs
            self.calls += 1
            return f"answer:{prompt}", 2, False

    class IdentityBoundJudge:
        calls = []

        def score_many(self, pairs, *, identities, checkpoint_root):
            del pairs
            checkpoint_root.mkdir(parents=True, exist_ok=True)
            identity_path = checkpoint_root / "ordered-identities.json"
            material = list(identities)
            if identity_path.exists():
                assert json.loads(identity_path.read_text(encoding="utf-8")) == material
            else:
                identity_path.write_text(json.dumps(material), encoding="utf-8")
            self.calls.append(material)
            return [runner.JudgeScore(True, True, "yes", "yes") for _ in material]

    generator = Generator()
    judge = IdentityBoundJudge()
    checkpoint = tmp_path / "dev.jsonl"
    records = runner._execute_jobs(
        jobs,
        checkpoint_path=checkpoint,
        run_config_hash=run_hash,
        items=items,
        prompts={OFFICIAL_BASE_PROMPT_ID: "Answer truthfully and informatively."},
        generator=generator,
        judge=judge,
        configs={},
        checkpoint_binding=binding,
    )
    assert len(records) == 2
    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    checkpoint.write_text(lines[0] + "\n", encoding="utf-8")
    manifest_path = checkpoint.with_suffix(".jsonl.manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["complete"] = False
    manifest["record_count"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    resumed = runner._execute_jobs(
        jobs,
        checkpoint_path=checkpoint,
        run_config_hash=run_hash,
        items=items,
        prompts={OFFICIAL_BASE_PROMPT_ID: "Answer truthfully and informatively."},
        generator=generator,
        judge=judge,
        configs={},
        checkpoint_binding=binding,
    )
    assert len(resumed) == 2
    assert generator.calls == 2
    assert judge.calls[0] == judge.calls[1]


def test_model_load_failure_writes_atomic_invalid_mechanics_record(
    tmp_path, monkeypatch
):
    out_dir = tmp_path / "external-run"
    monkeypatch.setattr(
        runner,
        "run_hf_dev",
        lambda args: (_ for _ in ()).throw(RuntimeError("load failed")),
    )
    rc = runner.main(
        [
            "--backend",
            "hf",
            "--phase",
            "dev",
            "--expected-code-commit",
            "abc",
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 2
    failure = json.loads(
        (out_dir / "failure_record.json").read_text(encoding="utf-8")
    )
    assert failure["status"] == "INVALID_MECHANICS"
    assert failure["error_type"] == "RuntimeError"
    failure_hash = json.loads(
        (out_dir / "failure_record.sha256.json").read_text(encoding="utf-8")
    )
    assert failure_hash["sha256"] == hashlib.sha256(
        (out_dir / "failure_record.json").read_bytes()
    ).hexdigest()


def test_artifact_hash_manifest_rejects_missing_required_file(tmp_path):
    present = tmp_path / "present.jsonl"
    present.write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="required artifact"):
        runner._artifact_hashes(
            tmp_path,
            [present, tmp_path / "missing.jsonl"],
        )
    manifest_path = tmp_path / "artifacts.json"
    manifest_path.write_text(
        json.dumps(runner._artifact_hashes(tmp_path, [present])),
        encoding="utf-8",
    )
    verified = runner._verify_artifact_hash_manifest(
        tmp_path, manifest_path, [present]
    )
    assert verified["files"]["present.jsonl"]["sha256"] == hashlib.sha256(
        present.read_bytes()
    ).hexdigest()
    present.write_text('{"tampered": true}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="size mismatch|SHA-256 mismatch"):
        runner._verify_artifact_hash_manifest(
            tmp_path, manifest_path, [present]
        )


def test_gpu_preflight_fails_closed_without_cuda(monkeypatch):
    torch = pytest.importorskip("torch")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="requires CUDA"):
        runner.gpu_preflight_assertions(
            object(), generator_snapshot_identity={"revision": "x"}
        )


def test_synthetic_end_to_end_smoke_is_non_evidence(tmp_path):
    rc = runner.main(
        [
            "--backend",
            "synthetic",
            "--phase",
            "smoke",
            "--out-dir",
            str(tmp_path / "smoke"),
            "--k",
            "2",
        ]
    )
    assert rc == 0
    payload = json.loads(
        (tmp_path / "smoke" / "synthetic_smoke_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["valid_for_paper"] is False
    assert payload["status"] == "SMOKE_PASS_PATH_EXERCISED"
    assert payload["experiment_id"] != EXPERIMENT_ID
    assert payload["backend"] == "synthetic"
    assert payload["phase"] == "smoke"
    assert "FULL_PC_PASS" not in json.dumps(payload)
    assert "ELIGIBLE" not in json.dumps(payload)
    assert payload["path_checks"]["current_grid_preserved"] is True
    for path in (tmp_path / "smoke").glob("synthetic_smoke_stage*.jsonl"):
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if path.name.endswith("_raw.jsonl"):
            continue
        assert {row["phase"] for row in rows} == {"smoke"}
    for path in (tmp_path / "smoke").glob("synthetic_smoke_stage*.manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        binding = manifest["checkpoint_binding"]
        assert binding["backend"] == "synthetic"
        assert binding["phase"] == "smoke"
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "smoke").iterdir()
        if path.is_file()
    )
    assert '"phase": "dev"' not in artifact_text
    assert '"phase": "test"' not in artifact_text
    assert "FULL_PC_" not in artifact_text
    assert "ELIGIBLE" not in artifact_text
