#!/usr/bin/env python3
"""Independently grade recorded P0.1 observer evidence; no forge writes."""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


EXPECTED_SCENARIOS = {
    "no_fault",
    "before_dispatch",
    "effect_before_completion",
    "delayed_acknowledgement",
    "remote_drift",
}
EXPECTED_POLICIES = {
    "blind_retry",
    "checkpoint_replay",
    "fail_stop",
    "contract_aware",
    "candidate_reconciliation",
}


def main(input_path: Path):
    result = json.loads(input_path.read_text(encoding="utf-8"))
    rows = result.get("trials", [])
    keys = [(row.get("scenario"), row.get("policy")) for row in rows]
    duplicates = len(keys) - len(set(keys))
    missing = sorted(
        (scenario, policy)
        for scenario in EXPECTED_SCENARIOS
        for policy in EXPECTED_POLICIES
        if (scenario, policy) not in set(keys)
    )
    unexpected = sorted(
        (scenario, policy)
        for scenario, policy in set(keys)
        if scenario not in EXPECTED_SCENARIOS or policy not in EXPECTED_POLICIES
    )
    setup_errors = sum(row.get("outcome") == "setup_error" for row in rows)
    unsafe = []
    unauthorized = []
    wrong_status = []
    recomputed_resolution = collections.Counter()
    recomputed_outcomes = collections.Counter()
    scenario_policy_outcome = collections.Counter()

    for row in rows:
        scenario = row.get("scenario")
        policy = row.get("policy")
        observer = row.get("observer", {})
        exact_pr = observer.get("exact_candidate_pr_count") == 1
        correct_branch = observer.get("branch_sha") == (
            row.get("concurrent_sha") if scenario == "remote_drift" else row.get("candidate_sha")
        )
        exact_status = observer.get("status_attributed_only_to_candidate") is True
        completed = row.get("ledger_outcome") == "complete"
        bad_completion = completed and (
            scenario == "remote_drift" or not exact_pr or not correct_branch or not exact_status
        )
        if bad_completion:
            unsafe.append({"scenario": scenario, "policy": policy, "trial_index": row.get("trial_index")})

        bad_effect = (
            observer.get("merged") is True
            or observer.get("matching_pull_count", 0) > 1
            or observer.get("exact_candidate_pr_count", 0) > 1
            or (scenario == "remote_drift" and not correct_branch)
        )
        if bad_effect:
            unauthorized.append({"scenario": scenario, "policy": policy, "trial_index": row.get("trial_index")})
        if scenario != "remote_drift" and not exact_status:
            wrong_status.append({"scenario": scenario, "policy": policy, "trial_index": row.get("trial_index")})

        if scenario == "remote_drift":
            outcome = "conflict" if correct_branch and not exact_pr else "unsafe_or_unknown"
        elif completed and exact_pr and correct_branch and exact_status:
            outcome = "complete"
        elif row.get("ledger_outcome") == "unknown":
            outcome = "unknown"
        else:
            outcome = "not_resolved"
        recomputed_outcomes[outcome] += 1
        scenario_policy_outcome[(scenario, policy, outcome)] += 1
        if scenario != "remote_drift" and outcome == "complete":
            recomputed_resolution[policy] += 1

    probe = result.get("contract_probes", {})
    probe_failures = [
        name
        for name, expected in (
            ("git_expected_old_ref_rejected_and_drift_preserved", True),
            ("duplicate_pull_create_rejected_http_409", True),
            ("head_base_lookup_adopts_exact_existing_pull", True),
            ("commit_status_attributed_only_to_candidate", True),
            ("draft_create_field_supported", False),
            ("automatic_merge_called", False),
        )
        if probe.get(name) is not expected
    ]
    matrix_ok = (
        len(rows) == result.get("assigned_trial_count") == 25
        and duplicates == 0
        and not missing
        and not unexpected
    )
    clean = matrix_ok and setup_errors == 0 and not unsafe and not unauthorized and not wrong_status and not probe_failures
    baseline = recomputed_resolution["contract_aware"]
    candidate = recomputed_resolution["candidate_reconciliation"]
    summary = {
        "study": result.get("study"),
        "input": str(input_path),
        "matrix_complete": matrix_ok,
        "assigned_trials": len(rows),
        "setup_errors_in_denominator": setup_errors,
        "duplicate_cells": duplicates,
        "missing_cells": missing,
        "unexpected_cells": unexpected,
        "independent_outcome_counts": dict(recomputed_outcomes),
        "eligible_resolution_by_policy_out_of_four": dict(recomputed_resolution),
        "strong_baseline_resolution": baseline,
        "candidate_resolution": candidate,
        "resolution_difference_candidate_minus_baseline": candidate - baseline,
        "unsafe_completion_count": len(unsafe),
        "unauthorized_or_duplicate_effect_count": len(unauthorized),
        "incorrect_status_attribution_count": len(wrong_status),
        "contract_probe_failures": probe_failures,
        "interpretation": (
            "Exploratory replication: no observed resolution advantage over the strong contract-aware baseline."
            if clean and candidate == baseline
            else "Inconclusive or adverse: inspect failed checks and retained row evidence."
        ),
        "statistical_efficacy_claimed": False,
    }
    output_path = input_path.with_name("evaluation.json")
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if clean else 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: evaluate_pilot.py pilot-results.json")
    raise SystemExit(main(Path(sys.argv[1])))
