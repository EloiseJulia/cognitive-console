import json
from pathlib import Path

import pytest

from scripts import run_uncertainty_format_recheck as R


def test_confidence_parse_none_sets_noncompliant_and_frozen_imputation():
    item = {"id": "u1", "prompt": "Capital of France?", "answer": "Paris"}
    rec = R.score_uncertainty_record("Answer: Paris.", item)
    assert rec["parse_confidence"] is None
    assert rec["format_compliant"] is False
    assert rec["item_is_correct"] == 1
    assert rec["imputed_confidence"] == 0.5
    assert rec["per_item_1minus_brier"] == pytest.approx(0.75)


def test_compliant_only_reanalysis_uses_only_paired_compliant_samples():
    records = [
        _row("it1", 0, "prompt", True, 0.80),
        _row("it1", 0, "steer", True, 0.60),
        _row("it1", 1, "prompt", True, 0.70),
        _row("it1", 1, "steer", False, 0.75),  # excluded: steer dropped format
        _row("it2", 0, "prompt", True, 0.50),
        _row("it2", 0, "steer", True, 0.90),
        _row("it2", 1, "prompt", False, 0.75),  # excluded: prompt dropped format
        _row("it2", 1, "steer", True, 0.95),
    ]
    out = R.reanalyse(records, bootstrap_b=200, seed=7)["test_split_only"]["caa__qwen2.5-7b"]
    assert out["format_compliant_only_delta_steer_minus_prompt"]["n_compliant_sample_pairs"] == 2
    assert out["format_compliant_only_delta_steer_minus_prompt"]["n_items"] == 2
    # item means: it1=(0.60-0.80)=-0.20; it2=(0.90-0.50)=+0.40; mean=+0.10
    assert out["format_compliant_only_delta_steer_minus_prompt"]["point"] == pytest.approx(0.10)
    assert out["conditions"]["steer"]["format_compliance_rate"] == pytest.approx(3 / 4)
    assert out["conditions"]["prompt"]["format_compliance_rate"] == pytest.approx(3 / 4)


def test_synthetic_smoke_writes_compliance_and_delta_fields(tmp_path):
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen")
    out_dir = tmp_path / "e0013"
    rc = R.main([
        "--backend", "synthetic",
        "--frozen-root", str(frozen_root),
        "--out-dir", str(out_dir),
        "--cells", "caa__qwen2.5-7b",
        "--splits", "test",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])
    assert rc == 0
    payload = json.loads((out_dir / "reanalysis.json").read_text(encoding="utf-8"))
    cell = payload["test_split_only"]["caa__qwen2.5-7b"]
    assert "format_compliance_rate" in cell["conditions"]["steer"]
    assert "frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed" in cell
    assert "format_compliant_only_delta_steer_minus_prompt" in cell
    sample = json.loads((out_dir / "samples.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert sample["synthetic_proxy"] is True
    assert sample["format_compliant"] is True
    assert sample["parse_confidence"] is not None
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic_proxy"] is True
    assert manifest["generation_identity"]["model_by_cell"]["caa__qwen2.5-7b"] == "frozen-qwen"
    assert manifest["generation_identity"]["effective_model_by_cell"]["caa__qwen2.5-7b"] == "frozen-qwen"
    assert (
        manifest["generation_identity"]["resolved_model_identity_by_cell"]
        ["caa__qwen2.5-7b"]["kind"]
        == "synthetic_offline"
    )


def test_legacy_model_label_key_normalizes_historical_references_only():
    qwen_autodl = "/root/autodl-tmp/models/Qwen2.5-7B-Instruct"
    qwen_hf = "Qwen/Qwen2.5-7B-Instruct"
    llama_autodl = "/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct"
    llama_hf = "meta-llama/Meta-Llama-3-8B-Instruct"

    assert R._legacy_model_label_key(qwen_autodl) == R._legacy_model_label_key(qwen_hf)
    assert R._legacy_model_label_key(llama_autodl) == R._legacy_model_label_key(llama_hf)
    assert R._legacy_model_label_key(qwen_hf) != R._legacy_model_label_key(llama_hf)


def test_validate_generation_identity_allows_same_model_different_reference():
    cfg = _frozen_cell(
        model_id="/root/autodl-tmp/models/Qwen2.5-7B-Instruct",
        model_label="qwen2.5-7b",
    )
    args = R.build_parser().parse_args(["--backend", "synthetic"])

    effective = R._validate_generation_identity(
        args,
        frozen_cell=cfg,
        requested_model="Qwen/Qwen2.5-7B-Instruct",
    )

    assert effective == "Qwen/Qwen2.5-7B-Instruct"


def test_local_model_identity_rejects_same_basename_different_content(tmp_path):
    approved = _write_model_snapshot(tmp_path / "approved" / "same-name", "qwen2")
    attacker = _write_model_snapshot(
        tmp_path / "attacker" / "same-name", "qwen2", weight=b"attacker"
    )
    expected_manifest = _snapshot_manifest(approved)

    with pytest.raises(RuntimeError, match="snapshot file identity mismatch"):
        R._hash_model_snapshot(
            attacker,
            model_label="qwen2.5-7b",
            expected_manifest=expected_manifest,
        )


def test_model_snapshot_missing_required_file_fails_closed(tmp_path):
    snapshot = _write_model_snapshot(tmp_path / "snapshot", "qwen2")
    expected_manifest = _snapshot_manifest(snapshot)
    (snapshot / "generation_config.json").unlink()

    with pytest.raises(RuntimeError, match="snapshot file set mismatch"):
        R._hash_model_snapshot(
            snapshot,
            model_label="qwen2.5-7b",
            expected_manifest=expected_manifest,
        )


def test_committed_model_manifests_bind_exact_files_and_chat_templates():
    protocol = json.loads(
        (
            R._REPO
            / "docs"
            / "research"
            / "2026-08-11-uncertainty-grid-recheck"
            / "frozen-manifest.json"
        ).read_text(encoding="utf-8")
    )
    policies = protocol["execution"]["model_identity"]
    qwen = R._load_model_snapshot_manifest(
        policies["qwen2.5-7b"], model_label="qwen2.5-7b"
    )
    llama = R._load_model_snapshot_manifest(
        policies["llama3-8b"], model_label="llama3-8b"
    )
    assert qwen["aggregate_sha256"] == (
        "94e27571b6d46e0bcddf1769e5ed9c8f1b3abb77540d34aeb667cd0d3f5a5997"
    )
    assert llama["aggregate_sha256"] == (
        "dfbfb454047cacd028913f3c23bca28786013e0e0720e20fb0a5ef20aa3fdf5c"
    )
    assert qwen["chat_template"]["sha256"] == (
        "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f"
    )
    assert llama["chat_template"]["sha256"] == (
        "ba03a121d097859c7b5b9cd03af99aafe95275210d2876f642ad9929a150f122"
    )
    assert all(row["sha256"] for row in qwen["files"] + llama["files"])


def test_hf_direct_runner_requires_manifest_audit_sha_and_authorization(
    tmp_path, monkeypatch
):
    out_dir = tmp_path / "out"
    with pytest.raises(RuntimeError, match="protocol-manifest is mandatory"):
        R.main(["--backend", "hf", "--out-dir", str(out_dir)])
    assert not out_dir.exists()
    protocol = tmp_path / "protocol.json"
    protocol.write_text(
        json.dumps(
            {
                "execution": {
                    "authorization_id": "approved",
                    "authorization_scope": "test",
                    "model_identity": {},
                    "resource_guards": {},
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="authorization is mandatory"):
        R.main(
            [
                "--backend",
                "hf",
                "--out-dir",
                str(out_dir),
                "--protocol-manifest",
                str(protocol),
                "--expected-code-commit",
                "a" * 40,
                "--scratch-dir",
                str(tmp_path / "scratch"),
            ]
        )
    committed_protocol = (
        R._REPO
        / "docs"
        / "research"
        / "2026-08-11-uncertainty-grid-recheck"
        / "frozen-manifest.json"
    )
    args = R.build_parser().parse_args(
        [
            "--backend",
            "hf",
            "--protocol-manifest",
            str(committed_protocol),
            "--expected-code-commit",
            R.git_commit(str(R._REPO)),
            "--authorization",
            "owner-2026-08-11-e0013-grid-recheck-after-hostile-audit",
            "--scratch-dir",
            str(tmp_path / "scratch"),
        ]
    )
    monkeypatch.setattr(R, "_git_status_rows", lambda: [" M scripts/runner.py"])
    with pytest.raises(RuntimeError, match="clean tree"):
        R._prepare_hf_execution_guard(args, raw_argv=[])


def test_manifest_records_frozen_effective_and_identity_key_for_override(tmp_path):
    frozen_model = "/root/autodl-tmp/models/Qwen2.5-7B-Instruct"
    effective_model = "Qwen/Qwen2.5-7B-Instruct"
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen", model=frozen_model)
    out_dir = tmp_path / "e0013"

    rc = R.main([
        "--backend", "synthetic",
        "--frozen-root", str(frozen_root),
        "--out-dir", str(out_dir),
        "--cells", "caa__qwen2.5-7b",
        "--qwen-model", effective_model,
        "--splits", "test",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])

    assert rc == 0
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    identity = manifest["generation_identity"]
    assert identity["frozen_model_by_cell"]["caa__qwen2.5-7b"] == frozen_model
    assert identity["effective_model_by_cell"]["caa__qwen2.5-7b"] == effective_model
    assert (
        identity["resolved_model_identity_by_cell"]["caa__qwen2.5-7b"]
        ["configured_ref"]
        == effective_model
    )
    cell = manifest["cells"]["caa__qwen2.5-7b"]
    assert cell["frozen_model_id"] == frozen_model
    assert cell["effective_model_ref"] == effective_model
    assert cell["resolved_model_identity"]["kind"] == "synthetic_offline"


def test_checkpoint_resume_reuses_completed_test_without_generation(
    tmp_path, monkeypatch
):
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen")
    out_dir = tmp_path / "e0013"
    argv = [
        "--backend", "synthetic",
        "--frozen-root", str(frozen_root),
        "--out-dir", str(out_dir),
        "--cells", "caa__qwen2.5-7b",
        "--splits", "dev", "test",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ]
    assert R.main(argv) == 0
    original_samples_sha = R._sha256_file(out_dir / "samples.jsonl")
    test_seal = json.loads(
        (out_dir / "checkpoints" / "test_complete.json")
        .read_text(encoding="utf-8")
    )
    assert test_seal["jobs"] == 45
    assert len(test_seal["checkpoint_files"]) == 3

    for name in ("samples.jsonl", "reanalysis.json", "run_manifest.json"):
        (out_dir / name).unlink()

    def fail_if_generated(*args, **kwargs):
        raise AssertionError("completed checkpoint batch was regenerated")

    monkeypatch.setattr(
        R.SyntheticC2bTaskBackend, "generate", fail_if_generated
    )
    assert R.main([*argv, "--resume-incomplete"]) == 0
    assert R._sha256_file(out_dir / "samples.jsonl") == original_samples_sha
    manifest = json.loads(
        (out_dir / "run_manifest.json").read_text(encoding="utf-8")
    )
    checkpoint = manifest["cells"]["caa__qwen2.5-7b"]["checkpoint"]
    assert checkpoint["records_generated"] == 0
    assert checkpoint["records_reused"] == 60
    assert checkpoint["test_use_policy"] == R.TEST_USE_POLICY


def test_test_complete_seal_refuses_missing_test_checkpoint(tmp_path):
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen")
    out_dir = tmp_path / "e0013"
    argv = [
        "--backend", "synthetic",
        "--frozen-root", str(frozen_root),
        "--out-dir", str(out_dir),
        "--cells", "caa__qwen2.5-7b",
        "--splits", "dev", "test",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ]
    assert R.main(argv) == 0
    checkpoint_dir = out_dir / "checkpoints"
    test_seal = json.loads(
        (checkpoint_dir / "test_complete.json").read_text(encoding="utf-8")
    )
    missing = tmp_path / "unused"
    for row in test_seal["checkpoint_files"]:
        candidate = Path(row["path"])
        if not candidate.is_absolute():
            candidate = R._REPO / candidate
        if candidate.exists():
            missing = candidate
            break
    assert missing.exists()
    missing.unlink()
    for name in ("samples.jsonl", "reanalysis.json", "run_manifest.json"):
        (out_dir / name).unlink()
    with pytest.raises(RuntimeError, match="TEST seal exists"):
        R.main([*argv, "--resume-incomplete"])


def test_old_or_dirty_execution_checkpoint_is_rejected(tmp_path):
    path = tmp_path / "batch.json"
    clean_binding = {"dirty_tree": False, "code_commit": "a" * 40}
    dirty_binding = {"dirty_tree": True, "code_commit": "a" * 40}
    R._atomic_write_json(
        path,
        {
            "schema_version": R.CHECKPOINT_SCHEMA_VERSION,
            "checkpoint_identity_sha256": "identity",
            "execution_binding": dirty_binding,
            "jobs_sha256": R._canonical_hash([]),
            "records_sha256": R._canonical_hash([]),
            "records": [],
        },
    )
    with pytest.raises(RuntimeError, match="execution identity mismatch"):
        R._load_checkpoint_batch(
            path,
            identity_sha256="identity",
            jobs=[],
            cfg=_frozen_cell("frozen-qwen", "qwen2.5-7b"),
            items_by_id={},
            model_id="synthetic-offline",
            experiment_id="E-0013-test",
            instruction="",
            requested_alpha=0.0,
            effective_alpha=0.0,
            backend_name="synthetic",
            execution_binding=clean_binding,
            model_identity_sha256="model",
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = "e0013-format-replay-checkpoint-v1"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="unsupported checkpoint schema"):
        R._load_checkpoint_batch(
            path,
            identity_sha256="identity",
            jobs=[],
            cfg=_frozen_cell("frozen-qwen", "qwen2.5-7b"),
            items_by_id={},
            model_id="synthetic-offline",
            experiment_id="E-0013-test",
            instruction="",
            requested_alpha=0.0,
            effective_alpha=0.0,
            backend_name="synthetic",
            execution_binding=clean_binding,
            model_identity_sha256="model",
        )


def test_resume_reuses_checkpoints_with_external_activation_cache(
    tmp_path, monkeypatch
):
    cfg = _frozen_cell("approved-model", "qwen2.5-7b")
    item = {
        "id": "u1",
        "prompt": "Capital of France?",
        "answer": "Paris",
        "aliases": [],
    }
    out_dir = tmp_path / "out"
    activation_cache = tmp_path / "external-scratch" / "activations"
    calls = {"generated": 0, "cache_seen": 0}

    class Backend:
        def generate_batch(self, prompts, steer, **kwargs):
            calls["generated"] += len(prompts)
            return ["Answer: Paris. Confidence: 80%."] * len(prompts)

    def derive(cfg, model_id, cache_dir, n_extraction, seed, model_identity):
        cache_dir.mkdir(parents=True, exist_ok=True)
        marker = cache_dir.parent / "resume.marker"
        if marker.exists():
            calls["cache_seen"] += 1
        marker.write_text("stable", encoding="utf-8")
        cache_path = cache_dir / f"{'a' * 64}.npy"
        if not cache_path.exists():
            R.np.save(cache_path, R.np.ones(8, dtype=R.np.float32))
        return R.np.ones(8), {"direction_source": "test"}

    monkeypatch.setattr(R, "_make_backend", lambda *args, **kwargs: Backend())
    monkeypatch.setattr(R, "_derive_hf_direction", derive)
    kwargs = {
        "backend_name": "hf",
        "model_id": "approved-model",
        "items_by_split": {"test": [item]},
        "splits": ["test"],
        "out_dir": out_dir,
        "max_new_tokens": 64,
        "temperature": 0.7,
        "seed": R.DEFAULT_SEED,
        "batch_size": 16,
        "raw_text_max_chars": 8000,
        "n_extraction": R.DEFAULT_N_EXTRACTION,
        "experiment_id": "E-0013-test",
        "protocol_identity": {"sha256": "manifest"},
        "item_identity": {"sha256": "items"},
        "model_identity": {
            "kind": "test",
            "model_label": "qwen2.5-7b",
            "resolved_path": "approved-model",
            "content_sha256": "model",
        },
        "execution_binding": {"dirty_tree": False, "argv": ["same"]},
        "activation_cache_dir": activation_cache,
        "resource_guard": lambda stage: {"stage": stage},
    }
    first, _ = R.generate_cell_samples(cfg, **kwargs)
    assert len(first) == 15
    generated = calls["generated"]
    activation_cache.mkdir(parents=True, exist_ok=True)
    (activation_cache / "orphan.npy.tmp").write_bytes(b"incomplete")

    class PoisonBackend:
        def generate_batch(self, *args, **kwargs):
            raise AssertionError("resume regenerated a completed batch")

    monkeypatch.setattr(
        R, "_make_backend", lambda *args, **kwargs: PoisonBackend()
    )
    second, meta = R.generate_cell_samples(cfg, **kwargs)
    assert len(second) == 15
    assert calls["generated"] == generated
    assert calls["cache_seen"] == 1
    assert not (activation_cache / "orphan.npy.tmp").exists()
    assert meta["checkpoint"]["records_reused"] == 15
    assert activation_cache.is_dir()
    assert not (out_dir / "activations").exists()


def test_activation_cache_tamper_fails_before_direction_resume(
    tmp_path, monkeypatch
):
    cfg = _frozen_cell("approved-model", "qwen2.5-7b")
    item = {
        "id": "u1",
        "prompt": "Capital of France?",
        "answer": "Paris",
        "aliases": [],
    }
    out_dir = tmp_path / "out"
    activation_cache = tmp_path / "external-scratch" / "activations"
    calls = {"derive": 0}

    class Backend:
        def generate_batch(self, prompts, steer, **kwargs):
            return ["Answer: Paris. Confidence: 80%."] * len(prompts)

    def derive(cfg, model_id, cache_dir, n_extraction, seed, model_identity):
        calls["derive"] += 1
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{'b' * 64}.npy"
        if not cache_path.exists():
            R.np.save(cache_path, R.np.ones(8, dtype=R.np.float32))
        return R.np.ones(8), {"direction_source": "test"}

    monkeypatch.setattr(R, "_make_backend", lambda *args, **kwargs: Backend())
    monkeypatch.setattr(R, "_derive_hf_direction", derive)
    kwargs = {
        "backend_name": "hf",
        "model_id": "approved-model",
        "items_by_split": {"test": [item]},
        "splits": ["test"],
        "out_dir": out_dir,
        "max_new_tokens": 64,
        "temperature": 0.7,
        "seed": R.DEFAULT_SEED,
        "batch_size": 16,
        "raw_text_max_chars": 8000,
        "n_extraction": R.DEFAULT_N_EXTRACTION,
        "experiment_id": "E-0013-test",
        "protocol_identity": {"sha256": "manifest"},
        "item_identity": {"sha256": "items"},
        "model_identity": {
            "kind": "test",
            "model_label": "qwen2.5-7b",
            "resolved_path": "approved-model",
            "content_sha256": "model",
        },
        "execution_binding": {"dirty_tree": False, "argv": ["same"]},
        "activation_cache_dir": activation_cache,
        "resource_guard": lambda stage: {"stage": stage},
    }
    R.generate_cell_samples(cfg, **kwargs)
    assert calls["derive"] == 1
    R.np.save(
        activation_cache / f"{'b' * 64}.npy",
        R.np.zeros(8, dtype=R.np.float32),
    )

    with pytest.raises(RuntimeError, match="content inventory mismatch"):
        R.generate_cell_samples(cfg, **kwargs)
    assert calls["derive"] == 1


def test_activation_cache_added_file_tamper_fails_closed(tmp_path):
    cache_dir = tmp_path / "scratch" / "cache"
    model_identity = {"content_sha256": "model"}
    execution_binding = {"argv": ["same"]}
    prepared = R._prepare_activation_cache(
        cache_dir,
        model_identity=model_identity,
        execution_binding=execution_binding,
    )
    assert prepared["inventory"] == []
    cache_dir.mkdir(parents=True, exist_ok=True)
    R.np.save(
        cache_dir / f"{'c' * 64}.npy",
        R.np.ones(2, dtype=R.np.float32),
    )
    with pytest.raises(RuntimeError, match="content inventory mismatch"):
        R._prepare_activation_cache(
            cache_dir,
            model_identity=model_identity,
            execution_binding=execution_binding,
        )


def test_cuda_and_disk_cache_guards_fail_closed(tmp_path, monkeypatch):
    good_probe = {
        "platform": "test",
        "python": "3.12",
        "torch": "test",
        "transformers": "test",
        "torch_cuda_runtime": "12.1",
        "cuda_device_count": 1,
        "cuda_device_index": 0,
        "cuda_device_name": "NVIDIA A800 80GB PCIe",
        "cuda_total_memory_bytes": 80 * 1024**3,
        "cuda_capability": [8, 0],
        "selected_device": "cuda",
        "selected_dtype": "float16",
    }
    monkeypatch.setattr(R, "_probe_cuda_environment", lambda: dict(good_probe))
    out_dir = tmp_path / "out"
    scratch = tmp_path / "scratch"
    activation = scratch / "activations"
    hf_cache = tmp_path / "hf"
    for path in (out_dir, activation, hf_cache):
        path.mkdir(parents=True)
    policy = {
        "device": "cuda",
        "dtype": "float16",
        "gpu_name_contains": "A800",
        "min_free_disk_bytes": 0,
        "max_scratch_bytes": 1024,
        "max_activation_cache_bytes": 1024,
        "max_hf_cache_bytes": 1024,
    }
    assert R._assert_resource_guards(
        policy,
        out_dir=out_dir,
        scratch_dir=scratch,
        activation_cache_dir=activation,
        hf_cache_dir=hf_cache,
        stage="test",
    )["selected_dtype"] == "float16"

    monkeypatch.setattr(
        R,
        "_probe_cuda_environment",
        lambda: {**good_probe, "cuda_device_name": "NVIDIA H100"},
    )
    with pytest.raises(RuntimeError, match="expected A800"):
        R._assert_resource_guards(
            policy,
            out_dir=out_dir,
            scratch_dir=scratch,
            activation_cache_dir=activation,
            hf_cache_dir=hf_cache,
            stage="wrong-gpu",
        )

    monkeypatch.setattr(R, "_probe_cuda_environment", lambda: dict(good_probe))
    (activation / "too-large.bin").write_bytes(b"x" * 32)
    with pytest.raises(RuntimeError, match="activation-cache budget exceeded"):
        R._assert_resource_guards(
            {**policy, "max_activation_cache_bytes": 8},
            out_dir=out_dir,
            scratch_dir=scratch,
            activation_cache_dir=activation,
            hf_cache_dir=hf_cache,
            stage="cache-budget",
        )


def _row(item_id, sample_index, condition, compliant, score):
    return {
        "cell": "caa__qwen2.5-7b",
        "split": "test",
        "item_id": item_id,
        "sample_index": sample_index,
        "condition": condition,
        "format_compliant": compliant,
        "per_item_1minus_brier": score,
    }


def _frozen_cell(model_id, model_label):
    return R.FrozenCellConfig(
        cell_key=f"caa__{model_label}",
        method="caa",
        model_label=model_label,
        model_id=model_id,
        layer=3,
        frozen_alpha=8.0,
        best_prompt_id="unc-test",
        best_prompt_text="Answer and state confidence.",
        neutral_prompt="Neutral.",
        sigma=1.0,
        source_result_file="synthetic",
        source_config_fingerprint="abc123",
        source_mean_diff=-0.1,
    )


def _write_minimal_frozen_root(root, model="frozen-qwen"):
    path = root / "cell_caa__qwen2.5-7b"
    path.mkdir(parents=True)
    payload = {
        "backend": "hf",
        "steering_method": "caa",
        "model": model,
        "config_fingerprint": "abc123",
        "frozen_params": {"k_samples": 5},
        "c1_layer_info": {"uncertainty_awareness": {"sigma": 1.0}},
        "axes": [{
            "axis": "uncertainty_awareness",
            "layer": 3,
            "mean_diff": -0.1,
            "dev_selection": {
                "best_prompt_id": "unc-test",
                "best_prompt_text": "Answer and state confidence.",
                "frozen_alpha": 8.0,
            },
        }],
    }
    (path / "c2b_adjudication_results.json").write_text(json.dumps(payload), encoding="utf-8")
    return root


def _write_model_snapshot(root, model_type, weight=b"approved"):
    root.mkdir(parents=True)
    (root / "model.safetensors").write_bytes(weight)
    (root / "model.safetensors.index.json").write_text("{}", encoding="utf-8")
    (root / "config.json").write_text(
        json.dumps({"model_type": model_type}), encoding="utf-8"
    )
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text(
        json.dumps({"chat_template": "template {{ messages }}"}),
        encoding="utf-8",
    )
    (root / "generation_config.json").write_text("{}", encoding="utf-8")
    return root


def _snapshot_manifest(root):
    rows = []
    for path in sorted(root.iterdir(), key=lambda value: value.name):
        category = R._model_identity_category(path.name)
        if category is None:
            continue
        rows.append(
            {
                "path": path.name,
                "category": category,
                "size_bytes": path.stat().st_size,
                "sha256": R._sha256_file(path),
            }
        )
    template = json.loads(
        (root / "tokenizer_config.json").read_text(encoding="utf-8")
    )["chat_template"]
    return {
        "files": rows,
        "aggregate_sha256": R._canonical_hash(rows),
        "chat_template": {
            "source": "tokenizer_config.json:chat_template",
            "utf8_bytes": len(template.encode("utf-8")),
            "sha256": R._sha256_text(template),
        },
    }
