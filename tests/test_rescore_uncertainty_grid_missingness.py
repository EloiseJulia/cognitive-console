from scripts import rescore_uncertainty_grid_missingness as R


def _row(condition, item, sample, compliant, score):
    return {
        "condition": condition,
        "item_id": item,
        "sample_index": sample,
        "format_compliant": compliant,
        "per_item_1minus_brier": score,
    }


def test_complete_case_and_itemwise_available_case_are_distinct():
    records = [
        _row("prompt", "i1", 0, True, 0.8),
        _row("steer", "i1", 0, False, 0.75),
        _row("prompt", "i1", 1, False, 0.75),
        _row("steer", "i1", 1, True, 0.4),
        _row("prompt", "i2", 0, True, 0.9),
        _row("steer", "i2", 0, True, 0.6),
    ]

    paired, paired_counts = R.paired_sample_complete_case(records)
    available, available_counts = R.no_impute_itemwise_available_case(records)

    assert paired == [-0.30000000000000004]
    assert paired_counts["retained_items"] == 1
    assert available == [-0.4, -0.30000000000000004]
    assert available_counts["retained_items"] == 2


def test_adversarial_endpoints_use_score_bounds_not_half_imputation():
    records = [
        _row("prompt", "i1", 0, False, 0.75),
        _row("steer", "i1", 0, True, 0.4),
        _row("prompt", "i2", 0, True, 0.8),
        _row("steer", "i2", 0, False, 0.75),
    ]

    lower = R.adversarial_endpoint_diffs(
        records, steer_missing_score=0.0, prompt_missing_score=1.0
    )
    upper = R.adversarial_endpoint_diffs(
        records, steer_missing_score=1.0, prompt_missing_score=0.0
    )

    assert lower == [-0.6, -0.8]
    assert upper == [0.4, 0.19999999999999996]


def test_no_parsable_condition_reports_calibration_unavailable():
    records = [
        _row("steer", "i1", 0, False, 0.75),
        _row("steer", "i2", 0, False, 0.75),
    ]

    summary = R.condition_summary(
        records,
        "steer",
        bootstrap_b=20,
        seed=7,
        ci_level=0.95,
    )

    assert summary["generation_quality"]["format_compliance_exact"] == "0/2"
    assert (
        summary["calibration_among_parsable_only"]["estimand_available"] is False
    )
    assert summary["calibration_among_parsable_only"]["point"] is None
