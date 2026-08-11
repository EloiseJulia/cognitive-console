import json
from pathlib import Path

import pytest

from scripts import run_prompt_steer_composition as R


def _authorize(template_path: Path, auth_path: Path) -> None:
    payload = json.loads(template_path.read_text(encoding="utf-8"))
    payload.update(
        {
            "authorization_id": "audit-pass-test",
            "authorized_by": "hostile-auditor",
            "authorized_at": "2026-08-11T12:00:00Z",
            "hostile_audit_verdict": "PASS",
            "budget_status": "approved",
            "test_authorized": True,
        }
    )
    auth_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _paths(out_dir: Path):
    return R._run_paths(out_dir, "synthetic")


def test_parser_requires_explicit_phase():
    with pytest.raises(SystemExit):
        R.build_parser().parse_args([])


def test_external_unsealed_selection_override_is_rejected(tmp_path):
    out_dir = tmp_path / "out"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    external = tmp_path / "external-dev-selection.json"
    external.write_bytes(
        (paths.dev_sealed / "dev_selection.json").read_bytes()
    )
    with pytest.raises(SystemExit):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--out-dir",
                str(out_dir),
                "--selection-json",
                str(external),
            ]
        )


def test_test_rejects_selection_hash_not_matching_seal_identity(tmp_path):
    out_dir = tmp_path / "seal-identity"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    seal_path = paths.dev_sealed / "SEAL.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["identity"]["selection_hash"] = "sha256:" + ("0" * 64)
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    with pytest.raises(SystemExit, match="verified seal identity"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--out-dir",
                str(out_dir),
                "--test-authorization-file",
                str(paths.backend_root / "unused.json"),
            ]
        )


def test_test_rejects_unapproved_template(tmp_path):
    out_dir = tmp_path / "composition_locked"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    with pytest.raises(SystemExit, match="authorization invalid"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--bootstrap-b",
                "100",
                "--out-dir",
                str(out_dir),
                "--test-authorization-file",
                str(paths.dev_sealed / "test_authorization.template.json"),
            ]
        )


def test_synthetic_dev_then_authorized_test_once(tmp_path):
    out_dir = tmp_path / "composition_e2e"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "200",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    assert selection["test_seen"] is False
    assert selection["eligible_axes"] == list(R.comp.AXES)
    assert selection["scientific_status"] == "SMOKE_ONLY"

    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    argv = [
        "--phase",
        "test",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "200",
        "--out-dir",
        str(out_dir),
        "--test-authorization-file",
        str(auth_path),
    ]
    assert R.main(argv) == 0

    result = json.loads(
        (paths.test_sealed / "composition_test_results.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["phase"] == "TEST"
    assert result["valid_for_paper"] is False
    assert result["validation_status"] == "SMOKE_ONLY"
    assert result["overall_verdict"] == "SMOKE_ONLY"
    assert len(result["axes"]) == 3
    for axis in result["axes"]:
        assert set(axis["condition_means"]) == {
            "neutral",
            "prompt",
            "steer",
            "prompt_steer",
        }
        assert "primary_steer_at_prompt" in axis["estimands"]
        assert "interaction" in axis["estimands"]
        assert "does not establish" in axis["interaction_scope"]
        assert axis["verdict"] == "SMOKE_ONLY"

    assert not (paths.test_sealed / "composition_results.manifest.yaml").exists()
    registry = R.ExperimentRegistry(str(paths.registry)).load()
    smoke_records = [
        row for row in registry if row["experiment_id"].startswith("e0017-composition-smoke")
    ]
    assert len(smoke_records) == 1
    assert smoke_records[0]["type"] == "diagnostic"
    assert smoke_records[0]["claim_ids"] == []
    assert R.main(argv) == 0
    assert len(R.ExperimentRegistry(str(paths.registry)).load()) == len(registry)


def test_authorization_cannot_move_to_another_out_dir(tmp_path):
    out_dir = tmp_path / "composition_source"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    R.validate_test_authorization(auth_path, selection)
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(
        auth_path, selection, paths.backend_root, fingerprint
    )
    assert marker.exists()
    with pytest.raises(SystemExit, match="backend directory differs"):
        R.reserve_test_once(
            auth_path,
            selection,
            tmp_path / "other",
            fingerprint,
        )


def test_authorization_copy_cannot_bypass_fixed_out_dir_marker(tmp_path):
    out_dir = tmp_path / "copy"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    copied_auth = paths.backend_root / "copied_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    copied_auth.write_bytes(auth_path.read_bytes())
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(
        auth_path, selection, paths.backend_root, fingerprint
    )
    R.update_test_marker(marker, "completed")

    with pytest.raises(SystemExit, match="already completed"):
        R.reserve_test_once(
            copied_auth, selection, paths.backend_root, fingerprint
        )


def test_bootstrap_is_part_of_test_once_identity(tmp_path):
    out_dir = tmp_path / "fp"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    R.reserve_test_once(
        auth_path,
        selection,
        paths.backend_root,
        R.test_config_fingerprint(selection, 100),
    )
    with pytest.raises(ValueError, match="DEV-sealed value"):
        R.test_config_fingerprint(selection, 200)


def test_synthetic_dev_resume_is_idempotent(tmp_path):
    out_dir = tmp_path / "resume"
    argv = [
        "--phase",
        "dev",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "100",
        "--out-dir",
        str(out_dir),
    ]
    assert R.main(argv) == 0
    paths = _paths(out_dir)
    first = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    raw_path = paths.dev_attempt / "checkpoints" / "raw_generations.jsonl"
    first_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert R.main(argv) == 0
    second = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    second_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert second["selection_hash"] == first["selection_hash"]
    assert second["direction_artifact"]["sha256"] == first["direction_artifact"]["sha256"]
    assert second_raw_lines == first_raw_lines


def test_operational_limits_are_frozen_and_not_cli_overridable():
    parser = R.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--phase", "dev", "--stall-timeout", "1"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--phase", "dev", "--disk-budget-gb", "1"])
    limits = R.frozen_operational_limits()
    assert limits["disk_budget_gb"] == 60.0
    assert limits["disk_ceiling_gb"] == 70.0
    assert limits["stall_timeout_seconds"] == 600.0
    assert limits["generation_retry_budget_per_backend_call"] == 1


@pytest.mark.parametrize(
    ("name", "total_gib", "expected"),
    [
        ("NVIDIA A800 80GB PCIe", 79.1, "nvidia-a800-80gb"),
        (
            "NVIDIA GeForce RTX 4080 SUPER",
            31.473,
            "autodl-rtx4080-super-32gb",
        ),
    ],
)
def test_authorized_hardware_profiles_accept_frozen_hosts(
    name, total_gib, expected
):
    assert (
        R.select_authorized_hardware_profile(name, total_gib).profile_id
        == expected
    )


@pytest.mark.parametrize(
    ("name", "total_gib"),
    [
        ("NVIDIA GeForce RTX 4080 SUPER", 30.999),
        ("NVIDIA GeForce RTX 4090", 23.9),
        ("NVIDIA A100-SXM4-80GB", 79.1),
    ],
)
def test_hardware_profile_rejects_smaller_or_unapproved_cards(
    name, total_gib
):
    with pytest.raises(ValueError, match="unauthorized GPU hardware profile"):
        R.select_authorized_hardware_profile(name, total_gib)


def test_torch_smi_memory_tolerance_accepts_autodl_reserved_gap():
    result = R.validate_torch_smi_total_memory(31.473, 31.992)
    assert result["gap_gib"] == pytest.approx(0.519)
    assert result["allowed_gap_gib"] == pytest.approx(0.95976)


@pytest.mark.parametrize(
    ("torch_total", "smi_total"),
    [
        (30.0, 31.992),
        (32.1, 31.992),
        (float("nan"), 31.992),
    ],
)
def test_torch_smi_memory_tolerance_rejects_genuine_mismatch(
    torch_total, smi_total
):
    with pytest.raises(ValueError):
        R.validate_torch_smi_total_memory(torch_total, smi_total)


def test_autodl_profile_pins_runtime_memory_and_disk_guards():
    profile = next(
        row
        for row in R.AUTHORIZED_HARDWARE_PROFILES
        if row.profile_id == "autodl-rtx4080-super-32gb"
    )
    assert profile.min_total_vram_gib == 31.0
    assert profile.min_free_before_load_gib == 24.0
    assert profile.min_free_after_load_gib == 10.0
    assert profile.disk_budget_gb == 40.0
    assert profile.disk_ceiling_gb == 45.0
    assert profile.required_hf_home == R.AUTODL_HF_HOME
    assert profile.required_output_root == R.AUTODL_OUTPUT_ROOT
    assert profile.required_transformers == "4.44.2"
    identity = R.hardware_profile_identity(profile)
    assert json.loads(json.dumps(identity)) == identity


def test_profile_disk_guard_normal_path_uses_shutil(tmp_path, monkeypatch):
    profile = R.HardwareProfile(
        profile_id="unit-disk",
        accepted_name_fragments=("GPU",),
        min_total_vram_gib=1.0,
        max_total_vram_gib=None,
        min_free_before_load_gib=1.0,
        min_free_after_load_gib=1.0,
        disk_budget_gb=1.0,
        disk_ceiling_gb=2.0,
        filesystem_free_reserve_gib=0.5,
    )
    paths = R._run_paths(tmp_path / "run", "hf")
    layout = R._cache_layout(paths, str(tmp_path / "hf"))
    guard_paths = R._guarded_growth_paths(paths, layout, None)
    monkeypatch.setattr(
        R.shutil,
        "disk_usage",
        lambda path: type(
            "Usage",
            (),
            {
                "total": int(50 * 1024**3),
                "used": int(10 * 1024**3),
                "free": int(40 * 1024**3),
            },
        )(),
    )
    result = R.check_profile_disk_guard(
        profile,
        guard_paths,
        layout,
        paths,
        stage="unit",
    )
    assert result["managed_usage"]["status"] == "ok"
    assert result["filesystems"][0]["free_gib"] == pytest.approx(40.0)


def test_profile_disk_guard_rejects_low_filesystem_free_space(
    tmp_path, monkeypatch
):
    profile = R.HardwareProfile(
        profile_id="unit-disk-floor",
        accepted_name_fragments=("GPU",),
        min_total_vram_gib=1.0,
        max_total_vram_gib=None,
        min_free_before_load_gib=1.0,
        min_free_after_load_gib=1.0,
        disk_budget_gb=1.0,
        disk_ceiling_gb=2.0,
        filesystem_free_reserve_gib=0.5,
    )
    paths = R._run_paths(tmp_path / "run", "hf")
    layout = R._cache_layout(paths, str(tmp_path / "hf"))
    monkeypatch.setattr(
        R.shutil,
        "disk_usage",
        lambda path: type(
            "Usage",
            (),
            {"total": 1024**3, "used": 1024**3, "free": 0},
        )(),
    )
    with pytest.raises(ValueError, match="filesystem free space"):
        R.check_profile_disk_guard(
            profile,
            R._guarded_growth_paths(paths, layout, None),
            layout,
            paths,
            stage="unit",
        )


def test_preflight_only_is_restricted_to_hf_dev():
    with pytest.raises(SystemExit, match="requires --phase dev --backend hf"):
        R.main(["--phase", "test", "--backend", "hf", "--preflight-only"])
    with pytest.raises(SystemExit, match="requires --phase dev --backend hf"):
        R.main(
            ["--phase", "dev", "--backend", "synthetic", "--preflight-only"]
        )


def test_preflight_only_dispatches_without_starting_dev(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(R, "_run_preflight", lambda args: 17)
    monkeypatch.setattr(
        R,
        "_run_dev",
        lambda args: pytest.fail("DEV must not start during preflight"),
    )
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "hf",
            "--preflight-only",
            "--out-dir",
            str(tmp_path),
        ]
    ) == 17


def test_all_hf_growth_roots_are_disk_guarded(tmp_path):
    paths = R._run_paths(tmp_path / "run", "hf")
    default_layout = R._cache_layout(paths, None)
    default_guarded = [
        Path(path) for path in R._guarded_growth_paths(paths, default_layout, None)
    ]
    assert default_guarded == [paths.backend_root.resolve()]
    for growth_path in (
        paths.dev_attempt,
        paths.dev_sealed,
        paths.test_attempt,
        paths.test_sealed,
        paths.registry,
        Path(default_layout["activation_cache"]),
        Path(default_layout["datasets_cache"]),
        Path(default_layout["hub_cache"]),
        Path(default_layout["transformers_cache"]),
    ):
        assert any(
            growth_path.resolve().is_relative_to(root)
            for root in default_guarded
        )

    external_home = tmp_path / "external-hf-home"
    external_layout = R._cache_layout(paths, str(external_home))
    external_guarded = {
        Path(path) for path in R._guarded_growth_paths(paths, external_layout, None)
    }
    assert external_guarded == {
        paths.backend_root.resolve(),
        external_home.resolve(),
    }
    assert Path(external_layout["activation_cache"]).is_relative_to(
        external_home.resolve()
    )


def test_hf_bootstrap_is_exact_and_authorization_bound(tmp_path):
    for bad_b in (R.comp.BOOTSTRAP_B - 1, R.comp.BOOTSTRAP_B + 1):
        with pytest.raises(SystemExit, match="bootstrap-b =="):
            R.main(
                [
                    "--phase",
                    "dev",
                    "--backend",
                    "hf",
                    "--bootstrap-b",
                    str(bad_b),
                    "--out-dir",
                    str(tmp_path / f"hf-{bad_b}"),
                ]
            )

    out_dir = tmp_path / "auth-bootstrap"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    seal = json.loads(
        (paths.dev_sealed / "SEAL.json").read_text(encoding="utf-8")
    )
    assert selection["bootstrap_b"] == 100
    assert seal["identity"]["bootstrap_b"] == 100
    auth_path = paths.backend_root / "bad-bootstrap-authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    auth["bootstrap_b"] = 101
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(SystemExit, match="authorization invalid: bootstrap_b"):
        R.validate_test_authorization(auth_path, selection)


def test_dev_registry_write_failure_recovers_from_seal(tmp_path, monkeypatch):
    out_dir = tmp_path / "dev-registry-recovery"
    paths = _paths(out_dir)
    original_append = R.ExperimentRegistry.append
    calls = {"count": 0}

    def fail_first_append(self, record):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("injected DEV registry write failure")
        return original_append(self, record)

    monkeypatch.setattr(R.ExperimentRegistry, "append", fail_first_append)
    argv = [
        "--phase",
        "dev",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "100",
        "--out-dir",
        str(out_dir),
    ]
    assert R.main(argv) == 5
    assert paths.dev_sealed.exists()
    assert (paths.dev_sealed / "experiment_record.json").exists()
    failure = json.loads(
        (paths.dev_attempt / "finalization_failure.json").read_text(
            encoding="utf-8"
        )
    )
    assert "injected DEV registry write failure" in failure["failure_reason"]

    assert R.main(argv) == 0
    records = R.ExperimentRegistry(str(paths.registry)).load()
    dev_records = [
        row
        for row in records
        if row["experiment_id"].startswith("e0017-composition-dev-")
        and row["status"] == "done"
    ]
    assert len(dev_records) == 1
    finalization_failures = [
        row
        for row in records
        if row["experiment_id"].startswith(
            "e0017-composition-dev-finalization-"
        )
        and row["status"] == "failed"
    ]
    assert len(finalization_failures) == 1
    assert R.main(argv) == 0
    assert len(R.ExperimentRegistry(str(paths.registry)).load()) == len(records)


def test_condition_shared_sample_rng_ignores_condition_and_alpha():
    sampler = object.__new__(R.CompositionTranscriptOutcomeSampler)
    sampler.seed = R.comp.SEED
    item = {"id": "paired-item"}
    assert sampler._call_seed("deliberation", item, 0.0, 3) == sampler._call_seed(
        "deliberation", item, 24.0, 3
    )
    assert sampler._call_seed("deliberation", item, 0.0, 3) != sampler._call_seed(
        "deliberation", item, 0.0, 4
    )


def test_physical_generation_budget_counts_retries_and_hard_caps(tmp_path):
    state = tmp_path / "budget.json"
    budget = R.PhysicalGenerationBudget(
        logical_limit=3,
        retry_budget=1,
        state_path=state,
        config_fingerprint="cfg",
    )
    budget.consume(3, retry=False)
    budget = R.PhysicalGenerationBudget(
        logical_limit=3,
        retry_budget=1,
        state_path=state,
        config_fingerprint="cfg",
    )
    budget.consume(3, retry=True)
    assert budget.to_dict()["physical_generations"] == 6
    assert budget.to_dict()["retry_backend_calls"] == 1
    with pytest.raises(RuntimeError, match="physical-generation cap exceeded"):
        budget.consume(1, retry=True)


def test_shared_parser_records_missing_fields_and_token_cap(tmp_path):
    collector = R.PersistentTranscriptCollector(
        tmp_path / "raw.jsonl",
        "cfg",
        model="m",
        method="caa",
        backend="hf",
        fresh=False,
    )
    item = {"id": "u1", "answer": "Paris", "aliases": ["Paris"]}
    diag = collector._parse_diag(
        "uncertainty_awareness",
        item,
        "Paris. Confidence: 80%",
        64,
        {
            "generated_token_count": 64,
            "finish_reason": "length",
            "contains_eos_token": False,
            "hit_max_new_tokens": True,
        },
    )
    assert diag["axis_parse_failed"] is True
    assert diag["missing_fields"] == ["answer"]
    assert diag["maybe_truncated"] is True
    not_capped = collector._parse_diag(
        "uncertainty_awareness",
        item,
        "Answer: Paris. Confidence: 80% " + ("word " * 100),
        64,
        {
            "generated_token_count": 12,
            "finish_reason": "eos_token",
            "contains_eos_token": True,
            "hit_max_new_tokens": False,
        },
    )
    assert not_capped["axis_parse_failed"] is False
    assert not_capped["maybe_truncated"] is False


def test_sealed_dev_directory_detects_tampering(tmp_path):
    out_dir = tmp_path / "sealed"
    argv = [
        "--phase",
        "dev",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "100",
        "--out-dir",
        str(out_dir),
    ]
    assert R.main(argv) == 0
    paths = _paths(out_dir)
    selection_path = paths.dev_sealed / "dev_selection.json"
    selection_path.write_text(
        selection_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="sealed directory was modified"):
        R.main(argv)


def test_test_head_must_equal_dev_commit(tmp_path, monkeypatch):
    out_dir = tmp_path / "head"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    changed = {
        "commit": "different-commit",
        "dirty": selection["dirty_tree_at_start"],
        "source_hashes": selection["source_hashes"],
    }
    monkeypatch.setattr(R, "_code_identity", lambda: changed)
    with pytest.raises(SystemExit, match="TEST HEAD must exactly equal"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--out-dir",
                str(out_dir),
                "--test-authorization-file",
                str(paths.backend_root / "unused.json"),
            ]
        )


def test_finalization_failure_is_recorded_and_resumable(tmp_path, monkeypatch):
    out_dir = tmp_path / "finalize"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    original = R._publish_sealed_directory

    def fail_test_publish(staging, sealed, **kwargs):
        if sealed == paths.test_sealed:
            raise OSError("injected finalization failure")
        return original(staging, sealed, **kwargs)

    monkeypatch.setattr(R, "_publish_sealed_directory", fail_test_publish)
    rc = R.main(
        [
            "--phase",
            "test",
            "--backend",
            "synthetic",
            "--out-dir",
            str(out_dir),
            "--test-authorization-file",
            str(auth_path),
        ]
    )
    assert rc == 5
    failure = json.loads(
        (paths.test_attempt / "finalization_failure.json").read_text(
            encoding="utf-8"
        )
    )
    assert "injected finalization failure" in failure["failure_reason"]
    marker = json.loads(
        (paths.backend_root / "test" / "test_authorization.used.json").read_text(
            encoding="utf-8"
        )
    )
    assert marker["status"] == "failed"
    assert not paths.test_sealed.exists()
    monkeypatch.setattr(R, "_publish_sealed_directory", original)
    assert R.main(
        [
            "--phase",
            "test",
            "--backend",
            "synthetic",
            "--out-dir",
            str(out_dir),
            "--test-authorization-file",
            str(auth_path),
        ]
    ) == 0
    assert paths.test_sealed.exists()


def test_test_phase_forbids_fresh_checkpoint_deletion(tmp_path):
    with pytest.raises(SystemExit, match="--fresh is forbidden"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--fresh",
                "--out-dir",
                str(tmp_path / "never_started"),
            ]
        )
