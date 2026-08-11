import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from cognitive_console.eval.truthfulqa_positive_control import (
    LocalTruthInfoJudge,
    OFFICIAL_BASE_PROMPT_ID,
    PROMPT_BANK_SHA256,
    TruthfulQAItem,
    load_prompt_bank,
    official_twofold_splits,
    parse_binary_judge,
)
from cognitive_console.experiments.iti_positive_control import (
    GenerationJob,
    GenerationRecord,
    JsonlCheckpoint,
    TEST_AUTHORIZATION,
    acquire_test_once_lock,
    adjudicate_test,
    config_hash,
    dev_eligibility,
    deterministic_sample_seed,
)
from cognitive_console.steering.official_iti import (
    ITIHeadSpec,
    OfficialITIConfig,
    OfficialITIHFBackend,
    fit_official_iti,
    hook_bite_metrics,
    matched_random_config,
)
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
    assert frozen["method"]["top_k_heads"] == 48
    assert frozen["method"]["alpha"] == 15.0
    assert frozen["generation"]["k"] == 5
    assert frozen["statistics"]["ci_level"] == pytest.approx(1.0 - 0.05 / 3.0)
    assert frozen["current_grid_preservation"].endswith("0/12")


def test_official_twofold_is_deterministic_disjoint_and_covers_all_items():
    first = official_twofold_splits()
    second = official_twofold_splits()
    assert first == second
    assert sorted(index for fold in first for index in fold.test) == list(range(817))
    for split in first:
        assert set(split.inner_train).isdisjoint(split.inner_dev)
        assert set(split.outer_train).isdisjoint(split.test)
        assert set(split.inner_train) | set(split.inner_dev) == set(split.outer_train)


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


def test_judges_load_sequentially_and_purge_dedicated_caches(tmp_path, monkeypatch):
    judge = LocalTruthInfoJudge.from_pretrained(
        device="cpu",
        dtype="float32",
        cache_root=tmp_path / "judges",
    )
    events = []

    def fake_load(model_id, revision, cache_dir):
        assert not any(
            child.is_dir() and child != cache_dir
            for child in judge.cache_root.glob("*")
        )
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "weight.bin").write_bytes(b"x")
        events.append(("load", model_id, revision, cache_dir.name))
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
    assert [row[3] for row in events] == ["truth", "info"]
    assert not list(judge.cache_root.glob("*"))
    resumed = judge.score_many(
        [("Question?", "Answer.")],
        identities=["job-1"],
        checkpoint_root=tmp_path / "judge-checkpoints",
    )
    assert resumed == scores
    assert [row[3] for row in events] == ["truth", "info"]


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


def test_checkpoint_resume_rejects_unknown_and_preserves_order(tmp_path):
    jobs = [
        GenerationJob(0, "dev", "baseline", OFFICIAL_BASE_PROMPT_ID, "a", 0, i, 7 + i)
        for i in range(2)
    ]
    cfg = config_hash({"x": 1})
    checkpoint = JsonlCheckpoint(tmp_path / "records.jsonl", run_config_hash=cfg, jobs=jobs)
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
    resumed = JsonlCheckpoint(tmp_path / "records.jsonl", run_config_hash=cfg, jobs=jobs)
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


def test_common_random_seed_is_condition_independent():
    seed = deterministic_sample_seed(3, fold=1, item_id="x", sample_index=2)
    assert seed == deterministic_sample_seed(3, fold=1, item_id="x", sample_index=2)
    assert seed != deterministic_sample_seed(3, fold=1, item_id="x", sample_index=3)


def test_test_once_lock_requires_exact_authorization_and_is_idempotent(tmp_path):
    with pytest.raises(PermissionError):
        acquire_test_once_lock(
            tmp_path,
            authorization="wrong",
            run_config_hash="cfg",
            dev_manifest_hash="dev",
        )
    first = acquire_test_once_lock(
        tmp_path,
        authorization=TEST_AUTHORIZATION,
        run_config_hash="cfg",
        dev_manifest_hash="dev",
    )
    second = acquire_test_once_lock(
        tmp_path,
        authorization=TEST_AUTHORIZATION,
        run_config_hash="cfg",
        dev_manifest_hash="dev",
    )
    assert first == second
    with pytest.raises(ValueError):
        acquire_test_once_lock(
            tmp_path,
            authorization=TEST_AUTHORIZATION,
            run_config_hash="other",
            dev_manifest_hash="dev",
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
        records, fold_prompt_ids={0: "winner", 1: "winner"}, k=1, bootstrap_seed=3
    )
    assert vetoed["status"] == "INVALID_RANDOM"

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
        bootstrap_seed=3,
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


def test_synthetic_end_to_end_smoke_is_non_evidence(tmp_path):
    rc = runner.main(
        [
            "--backend",
            "synthetic",
            "--phase",
            "full",
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
    assert payload["eligibility"]["status"] == "ELIGIBLE"
    assert payload["status"] == "FULL_PC_PASS"
    assert payload["adjudication"]["current_grid_preservation"].endswith(
        "must not be rewritten as 1/13."
    )
