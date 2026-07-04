"""Strict validators for the artifacts that models are allowed to author.

These validators intentionally reject plausible prose that is not tied to the same
question registry, hashes, identities, and evidence surface.
"""
from __future__ import annotations

from typing import Any, Iterable

from .errors import ValidationError
from .util import require_clean_text, require_keys, unique_ids

SCHEMA_VERSION = 1
PUSH_VERDICTS = {"PROCEED", "STOP", "PIVOT", "INSUFFICIENT_QUORUM"}
CRITERION_VERDICTS = {"PASS", "FAIL", "UNKNOWN"}
FINDING_SEVERITIES = {"critical", "high", "medium", "low", "note"}
FINDING_DISPOSITIONS = {"ACT_ON", "CONSIDER", "NOTED", "DISMISSED", "OUT_OF_SCOPE"}
FORBIDDEN_ARBITRATION = {"vote", "majority", "confidence", "model_brand", "authority", "consensus"}
ALLOWED_ARBITRATION = {"experiment", "existing_evidence", "locked_spec", "user_decision"}


def _expect_list(value: Any, context: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{context} must be a list")
    if nonempty and not value:
        raise ValidationError(f"{context} must not be empty")
    return value


def _expect_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{context} must be an object")
    return value


def _expect_string_list(value: Any, context: str, *, nonempty: bool = False) -> list[str]:
    items = _expect_list(value, context, nonempty=nonempty)
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(require_clean_text(item, f"{context}[{index}]"))
    if len(result) != len(set(result)):
        raise ValidationError(f"{context} contains duplicates")
    return result


def validate_identity(value: Any, context: str) -> dict[str, str]:
    identity = _expect_object(value, context)
    require_keys(identity, ("participant_id", "provider", "model", "context_id"), context)
    result = {
        key: require_clean_text(identity[key], f"{context}.{key}")
        for key in ("participant_id", "provider", "model", "context_id")
    }
    return result


def validate_spec(spec: dict[str, Any], *, mission_id: str, goal_sha256: str) -> dict[str, Any]:
    require_keys(
        spec,
        (
            "schema_version",
            "mission_id",
            "goal_sha256",
            "requirements",
            "acceptance_criteria",
            "non_goals",
            "constraints",
            "stop_conditions",
            "max_iterations",
        ),
        "spec",
    )
    if spec["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("spec.schema_version must be 1")
    if spec["mission_id"] != mission_id:
        raise ValidationError("spec.mission_id does not match the active mission")
    if spec["goal_sha256"] != goal_sha256:
        raise ValidationError("spec.goal_sha256 does not match GOAL.txt")

    requirements = _expect_list(spec["requirements"], "spec.requirements", nonempty=True)
    requirement_ids = unique_ids(requirements, "spec.requirements")
    must_ids: set[str] = set()
    for index, requirement in enumerate(requirements):
        context = f"spec.requirements[{index}]"
        require_keys(requirement, ("id", "statement", "priority", "source"), context)
        require_clean_text(requirement["statement"], f"{context}.statement", minimum=8)
        if requirement["priority"] not in {"must", "should", "could"}:
            raise ValidationError(f"{context}.priority must be must, should, or could")
        if requirement["source"] not in {"user", "constraint", "derived"}:
            raise ValidationError(f"{context}.source must be user, constraint, or derived")
        if requirement["priority"] == "must":
            must_ids.add(requirement["id"])

    criteria = _expect_list(spec["acceptance_criteria"], "spec.acceptance_criteria", nonempty=True)
    acceptance_ids = unique_ids(criteria, "spec.acceptance_criteria")
    mapped_requirements: set[str] = set()
    for index, criterion in enumerate(criteria):
        context = f"spec.acceptance_criteria[{index}]"
        require_keys(criterion, ("id", "requirement_ids", "observable", "oracle"), context)
        linked = set(_expect_string_list(criterion["requirement_ids"], f"{context}.requirement_ids", nonempty=True))
        unknown = linked - requirement_ids
        if unknown:
            raise ValidationError(f"{context} refers to unknown requirements: {', '.join(sorted(unknown))}")
        mapped_requirements.update(linked)
        require_clean_text(criterion["observable"], f"{context}.observable", minimum=8)
        oracle = _expect_object(criterion["oracle"], f"{context}.oracle")
        require_keys(oracle, ("type", "description"), f"{context}.oracle")
        if oracle["type"] not in {"command", "inspection", "human", "external"}:
            raise ValidationError(f"{context}.oracle.type is invalid")
        require_clean_text(oracle["description"], f"{context}.oracle.description", minimum=5)

    unmapped_must = must_ids - mapped_requirements
    if unmapped_must:
        raise ValidationError(
            "every must requirement needs an acceptance criterion; missing: "
            + ", ".join(sorted(unmapped_must))
        )
    _expect_string_list(spec["non_goals"], "spec.non_goals")
    _expect_string_list(spec["constraints"], "spec.constraints")
    _expect_string_list(spec["stop_conditions"], "spec.stop_conditions", nonempty=True)
    max_iterations = spec["max_iterations"]
    if not isinstance(max_iterations, int) or not 1 <= max_iterations <= 25:
        raise ValidationError("spec.max_iterations must be an integer from 1 to 25")
    return {
        "requirement_ids": requirement_ids,
        "acceptance_ids": acceptance_ids,
        "max_iterations": max_iterations,
    }


def push_conflicts(advisors: list[dict[str, Any]]) -> set[str]:
    verdicts = {advisor["verdict"] for advisor in advisors}
    if len(verdicts) > 1:
        return {"verdict-split"}
    return set()


def validate_push(
    push: dict[str, Any],
    *,
    mission_id: str,
    expected_hashes: dict[str, str],
) -> dict[str, Any]:
    require_keys(push, ("schema_version", "mission_id", "artifact_hashes", "advisors", "decision"), "push")
    if push["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("push.schema_version must be 1")
    if push["mission_id"] != mission_id:
        raise ValidationError("push.mission_id does not match the active mission")
    hashes = _expect_object(push["artifact_hashes"], "push.artifact_hashes")
    for key, expected in expected_hashes.items():
        if hashes.get(key) != expected:
            raise ValidationError(f"push.artifact_hashes.{key} does not match the reviewed artifact")

    advisors = _expect_list(push["advisors"], "push.advisors")
    identities: list[dict[str, str]] = []
    normalized_advisors: list[dict[str, Any]] = []
    for index, advisor_value in enumerate(advisors):
        context = f"push.advisors[{index}]"
        advisor = _expect_object(advisor_value, context)
        require_keys(
            advisor,
            ("identity", "independent_first_round", "verdict", "route", "falsifiable_criteria", "risk", "first_move", "cut"),
            context,
        )
        identity = validate_identity(advisor["identity"], f"{context}.identity")
        if advisor["independent_first_round"] is not True:
            raise ValidationError(f"{context} must attest independent_first_round=true")
        if advisor["verdict"] not in {"PROCEED", "STOP", "PIVOT"}:
            raise ValidationError(f"{context}.verdict is invalid")
        require_clean_text(advisor["route"], f"{context}.route", minimum=8)
        criteria_values = _expect_list(advisor["falsifiable_criteria"], f"{context}.falsifiable_criteria", nonempty=True)
        falsifiable_criteria: list[str] = []
        for criterion_index, criterion_value in enumerate(criteria_values):
            falsifiable_criteria.append(
                require_clean_text(
                    criterion_value,
                    f"{context}.falsifiable_criteria[{criterion_index}]",
                    minimum=8,
                )
            )
        if len(falsifiable_criteria) != len(set(falsifiable_criteria)):
            raise ValidationError(f"{context}.falsifiable_criteria contains duplicates")
        require_clean_text(advisor["risk"], f"{context}.risk", minimum=5)
        require_clean_text(advisor["first_move"], f"{context}.first_move", minimum=4)
        require_clean_text(advisor["cut"], f"{context}.cut", minimum=3)
        identities.append(identity)
        normalized_advisors.append({**advisor, "identity": identity, "falsifiable_criteria": falsifiable_criteria})

    participant_ids = [identity["participant_id"] for identity in identities]
    context_ids = [identity["context_id"] for identity in identities]
    if len(participant_ids) != len(set(participant_ids)):
        raise ValidationError("push participant_id values must be unique")
    if len(context_ids) != len(set(context_ids)):
        raise ValidationError("push context_id values must be unique; duplicate contexts are not independent")

    decision = _expect_object(push["decision"], "push.decision")
    require_keys(decision, ("verdict", "rationale", "conflict_resolutions", "first_slice", "chair"), "push.decision")
    verdict = decision["verdict"]
    if verdict not in PUSH_VERDICTS:
        raise ValidationError("push.decision.verdict is invalid")
    require_clean_text(decision["rationale"], "push.decision.rationale", minimum=8)
    chair = validate_identity(decision["chair"], "push.decision.chair")
    if chair["participant_id"] in set(participant_ids):
        raise ValidationError("Push chair must not impersonate or count as an advisor")
    if verdict != "INSUFFICIENT_QUORUM" and len(advisors) < 2:
        raise ValidationError("Push requires at least two independent advisors")
    if verdict == "INSUFFICIENT_QUORUM" and len(advisors) >= 2:
        raise ValidationError("INSUFFICIENT_QUORUM is invalid when two independent advisors are present")
    if verdict == "PROCEED":
        require_clean_text(decision["first_slice"], "push.decision.first_slice", minimum=5)

    conflicts = push_conflicts(normalized_advisors)
    resolutions_value = _expect_list(decision["conflict_resolutions"], "push.decision.conflict_resolutions")
    resolutions: dict[str, dict[str, Any]] = {}
    for index, resolution_value in enumerate(resolutions_value):
        context = f"push.decision.conflict_resolutions[{index}]"
        resolution = _expect_object(resolution_value, context)
        require_keys(resolution, ("topic", "basis", "evidence", "conclusion"), context)
        topic = require_clean_text(resolution["topic"], f"{context}.topic")
        if topic in resolutions:
            raise ValidationError(f"duplicate Push conflict resolution: {topic}")
        basis = resolution["basis"]
        if basis in FORBIDDEN_ARBITRATION or basis not in ALLOWED_ARBITRATION:
            raise ValidationError(f"{context}.basis must be evidence, not votes, confidence, or model authority")
        require_clean_text(resolution["evidence"], f"{context}.evidence", minimum=5)
        require_clean_text(resolution["conclusion"], f"{context}.conclusion", minimum=5)
        resolutions[topic] = resolution
    unresolved = conflicts - set(resolutions)
    if verdict in {"PROCEED", "STOP", "PIVOT"} and unresolved:
        raise ValidationError("material Push conflicts are unresolved: " + ", ".join(sorted(unresolved)))
    return {
        "verdict": verdict,
        "advisor_count": len(advisors),
        "conflicts": sorted(conflicts),
        "resolved_conflicts": sorted(set(resolutions) & conflicts),
        "chair": chair,
    }


def validate_contract(
    contract: dict[str, Any],
    *,
    mission_id: str,
    iteration: int,
    spec_requirement_ids: set[str],
    spec_acceptance_ids: set[str],
) -> dict[str, Any]:
    require_keys(
        contract,
        (
            "schema_version",
            "mission_id",
            "iteration",
            "title",
            "builder",
            "requirements",
            "acceptance_criteria",
            "allowed_paths",
            "forbidden_paths",
            "exempt_paths",
            "budgets",
            "verification",
            "final",
        ),
        "contract",
    )
    if contract["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("contract.schema_version must be 1")
    if contract["mission_id"] != mission_id or contract["iteration"] != iteration:
        raise ValidationError("contract mission_id or iteration does not match the active slice")
    require_clean_text(contract["title"], "contract.title", minimum=5)
    builder = validate_identity(contract["builder"], "contract.builder")
    requirements = set(_expect_string_list(contract["requirements"], "contract.requirements", nonempty=True))
    acceptance = set(_expect_string_list(contract["acceptance_criteria"], "contract.acceptance_criteria", nonempty=True))
    if requirements - spec_requirement_ids:
        raise ValidationError("contract contains requirements outside the locked spec")
    if acceptance - spec_acceptance_ids:
        raise ValidationError("contract contains acceptance criteria outside the locked spec")
    allowed_paths = _expect_string_list(contract["allowed_paths"], "contract.allowed_paths", nonempty=True)
    forbidden_paths = _expect_string_list(contract["forbidden_paths"], "contract.forbidden_paths")
    exempt_paths = _expect_string_list(contract["exempt_paths"], "contract.exempt_paths")
    for pattern in allowed_paths + forbidden_paths + exempt_paths:
        if pattern.startswith("/") or ".." in pattern.split("/"):
            raise ValidationError(f"contract path glob must stay inside the repository: {pattern}")
    if any(pattern.startswith(".signoff") for pattern in allowed_paths):
        raise ValidationError("contract may not authorize product work inside .signoff")
    budgets = _expect_object(contract["budgets"], "contract.budgets")
    require_keys(budgets, ("production_files", "changed_lines"), "contract.budgets")
    for key in ("production_files", "changed_lines"):
        if not isinstance(budgets[key], int) or budgets[key] < 1:
            raise ValidationError(f"contract.budgets.{key} must be a positive integer")
    if budgets["production_files"] > 100 or budgets["changed_lines"] > 20_000:
        raise ValidationError("contract budget is unbounded; split the slice or record a Push pivot")

    checks = _expect_list(contract["verification"], "contract.verification", nonempty=True)
    check_ids = unique_ids(checks, "contract.verification")
    covered: set[str] = set()
    for index, check in enumerate(checks):
        context = f"contract.verification[{index}]"
        require_keys(check, ("id", "command", "timeout_seconds", "working_directory", "acceptance_ids"), context)
        command = _expect_string_list(check["command"], f"{context}.command", nonempty=True)
        if command[0].lower() in {"sh", "bash", "zsh", "cmd", "powershell", "pwsh"}:
            # Shells are allowed only when explicitly named; no implicit shell=True interpretation exists.
            pass
        timeout = check["timeout_seconds"]
        if not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            raise ValidationError(f"{context}.timeout_seconds must be from 1 to 3600")
        workdir = require_clean_text(check["working_directory"], f"{context}.working_directory")
        if workdir.startswith("/") or ".." in workdir.split("/"):
            raise ValidationError(f"{context}.working_directory escapes the project")
        linked = set(_expect_string_list(check["acceptance_ids"], f"{context}.acceptance_ids", nonempty=True))
        if linked - acceptance:
            raise ValidationError(f"{context} covers acceptance criteria outside this slice")
        covered.update(linked)
    if acceptance - covered:
        raise ValidationError("every active acceptance criterion needs an executable verification command")
    if not isinstance(contract["final"], bool):
        raise ValidationError("contract.final must be true or false")
    return {
        "builder": builder,
        "requirements": requirements,
        "acceptance": acceptance,
        "allowed_paths": allowed_paths,
        "forbidden_paths": forbidden_paths,
        "exempt_paths": exempt_paths,
        "budgets": budgets,
        "check_ids": check_ids,
        "final": contract["final"],
    }


def validate_review(
    review: dict[str, Any],
    *,
    mission_id: str,
    iteration: int,
    hashes: dict[str, str],
    acceptance_ids: set[str],
) -> dict[str, Any]:
    require_keys(review, ("schema_version", "mission_id", "iteration", "reviewer", "artifact_hashes", "read_only", "criteria", "findings", "overall"), "review")
    if review["schema_version"] != SCHEMA_VERSION or review["mission_id"] != mission_id or review["iteration"] != iteration:
        raise ValidationError("review schema_version, mission_id, or iteration is wrong")
    reviewer = validate_identity(review["reviewer"], "review.reviewer")
    artifact_hashes = _expect_object(review["artifact_hashes"], "review.artifact_hashes")
    for key, expected in hashes.items():
        if artifact_hashes.get(key) != expected:
            raise ValidationError(f"review was not sealed against the active {key} hash")
    if review["read_only"] is not True:
        raise ValidationError("reviewer must attest read_only=true")
    criteria = _expect_list(review["criteria"], "review.criteria", nonempty=True)
    seen: set[str] = set()
    verdicts: dict[str, str] = {}
    for index, criterion_value in enumerate(criteria):
        context = f"review.criteria[{index}]"
        criterion = _expect_object(criterion_value, context)
        require_keys(criterion, ("acceptance_id", "verdict", "evidence_refs", "reason"), context)
        acceptance_id = criterion["acceptance_id"]
        if acceptance_id not in acceptance_ids:
            raise ValidationError(f"{context} answers an acceptance criterion outside the slice")
        if acceptance_id in seen:
            raise ValidationError(f"review answers acceptance criterion twice: {acceptance_id}")
        seen.add(acceptance_id)
        if criterion["verdict"] not in CRITERION_VERDICTS:
            raise ValidationError(f"{context}.verdict is invalid")
        _expect_string_list(criterion["evidence_refs"], f"{context}.evidence_refs")
        require_clean_text(criterion["reason"], f"{context}.reason", minimum=5)
        verdicts[acceptance_id] = criterion["verdict"]
    missing = acceptance_ids - seen
    if missing:
        raise ValidationError("review skipped acceptance criteria: " + ", ".join(sorted(missing)))

    findings = _expect_list(review["findings"], "review.findings")
    finding_ids = unique_ids(findings, "review.findings") if findings else set()
    for index, finding_value in enumerate(findings):
        context = f"review.findings[{index}]"
        finding = _expect_object(finding_value, context)
        require_keys(finding, ("id", "severity", "acceptance_ids", "claim", "evidence", "falsifier", "recommended_disposition"), context)
        if finding["severity"] not in FINDING_SEVERITIES:
            raise ValidationError(f"{context}.severity is invalid")
        linked = set(_expect_string_list(finding["acceptance_ids"], f"{context}.acceptance_ids"))
        if linked - acceptance_ids:
            raise ValidationError(f"{context} links to acceptance criteria outside the slice")
        require_clean_text(finding["claim"], f"{context}.claim", minimum=5)
        require_clean_text(finding["evidence"], f"{context}.evidence", minimum=3)
        require_clean_text(finding["falsifier"], f"{context}.falsifier", minimum=5)
        if finding["recommended_disposition"] not in FINDING_DISPOSITIONS:
            raise ValidationError(f"{context}.recommended_disposition is invalid")
    if review["overall"] not in {"PASS", "REWORK", "BLOCKED"}:
        raise ValidationError("review.overall must be PASS, REWORK, or BLOCKED")
    return {"reviewer": reviewer, "verdicts": verdicts, "finding_ids": finding_ids, "findings": findings}


def validate_pull(
    reviews: list[dict[str, Any]],
    judgment: dict[str, Any],
    *,
    mission_id: str,
    iteration: int,
    hashes: dict[str, str],
    acceptance_ids: set[str],
    builder: dict[str, str],
    evidence_check_ids: set[str],
) -> dict[str, Any]:
    if len(reviews) < 2:
        raise ValidationError("Pull requires at least two substantive independent reviews")
    normalized = [
        validate_review(
            review,
            mission_id=mission_id,
            iteration=iteration,
            hashes=hashes,
            acceptance_ids=acceptance_ids,
        )
        for review in reviews
    ]
    participant_ids = [item["reviewer"]["participant_id"] for item in normalized]
    context_ids = [item["reviewer"]["context_id"] for item in normalized]
    if len(participant_ids) != len(set(participant_ids)) or len(context_ids) != len(set(context_ids)):
        raise ValidationError("reviewers need unique participant_id and context_id values")
    if builder["participant_id"] in participant_ids or builder["context_id"] in context_ids:
        raise ValidationError("the builder cannot count as an independent reviewer")

    require_keys(judgment, ("schema_version", "mission_id", "iteration", "judge", "artifact_hashes", "decision", "criterion_decisions", "finding_dispositions", "conflict_resolutions", "rationale"), "judgment")
    if judgment["schema_version"] != SCHEMA_VERSION or judgment["mission_id"] != mission_id or judgment["iteration"] != iteration:
        raise ValidationError("judgment schema_version, mission_id, or iteration is wrong")
    judge = validate_identity(judgment["judge"], "judgment.judge")
    if judge["participant_id"] == builder["participant_id"] or judge["context_id"] == builder["context_id"]:
        raise ValidationError("the builder cannot be the lead judge")
    if judge["participant_id"] in participant_ids or judge["context_id"] in context_ids:
        raise ValidationError("the lead judge must be independent of the counted reviewers")
    judgment_hashes = _expect_object(judgment["artifact_hashes"], "judgment.artifact_hashes")
    for key, expected in hashes.items():
        if judgment_hashes.get(key) != expected:
            raise ValidationError(f"judgment was not sealed against the active {key} hash")
    if judgment["decision"] not in {"PASS", "REWORK", "BLOCKED"}:
        raise ValidationError("judgment.decision must be PASS, REWORK, or BLOCKED")
    require_clean_text(judgment["rationale"], "judgment.rationale", minimum=8)

    criterion_decisions_value = _expect_list(judgment["criterion_decisions"], "judgment.criterion_decisions", nonempty=True)
    criterion_decisions: dict[str, str] = {}
    for index, decision_value in enumerate(criterion_decisions_value):
        context = f"judgment.criterion_decisions[{index}]"
        decision = _expect_object(decision_value, context)
        require_keys(decision, ("acceptance_id", "verdict", "reason"), context)
        acceptance_id = decision["acceptance_id"]
        if acceptance_id not in acceptance_ids or acceptance_id in criterion_decisions:
            raise ValidationError(f"{context}.acceptance_id is invalid or duplicated")
        if decision["verdict"] not in CRITERION_VERDICTS:
            raise ValidationError(f"{context}.verdict is invalid")
        require_clean_text(decision["reason"], f"{context}.reason", minimum=5)
        criterion_decisions[acceptance_id] = decision["verdict"]
    if set(criterion_decisions) != acceptance_ids:
        raise ValidationError("judgment must decide every active acceptance criterion")

    conflicts: set[str] = set()
    nonpass: set[str] = set()
    for acceptance_id in acceptance_ids:
        verdict_set = {item["verdicts"][acceptance_id] for item in normalized}
        if len(verdict_set) > 1:
            conflicts.add(acceptance_id)
        if verdict_set != {"PASS"}:
            nonpass.add(acceptance_id)

    resolutions_value = _expect_list(judgment["conflict_resolutions"], "judgment.conflict_resolutions")
    resolutions: dict[str, dict[str, Any]] = {}
    for index, resolution_value in enumerate(resolutions_value):
        context = f"judgment.conflict_resolutions[{index}]"
        resolution = _expect_object(resolution_value, context)
        require_keys(resolution, ("acceptance_id", "basis", "evidence_ref", "conclusion"), context)
        acceptance_id = resolution["acceptance_id"]
        if acceptance_id not in acceptance_ids or acceptance_id in resolutions:
            raise ValidationError(f"{context}.acceptance_id is invalid or duplicated")
        basis = resolution["basis"]
        if basis in FORBIDDEN_ARBITRATION or basis not in ALLOWED_ARBITRATION:
            raise ValidationError(f"{context}.basis cannot be vote, confidence, consensus, or model authority")
        evidence_ref = require_clean_text(resolution["evidence_ref"], f"{context}.evidence_ref")
        if basis in {"experiment", "existing_evidence"} and evidence_ref not in evidence_check_ids:
            raise ValidationError(f"{context}.evidence_ref must name a passed verification check")
        require_clean_text(resolution["conclusion"], f"{context}.conclusion", minimum=5)
        resolutions[acceptance_id] = resolution

    if judgment["decision"] == "PASS":
        if any(value != "PASS" for value in criterion_decisions.values()):
            raise ValidationError("PASS judgment cannot contain FAIL or UNKNOWN criterion decisions")
        unresolved = nonpass - set(resolutions)
        if unresolved:
            raise ValidationError(
                "review disagreement or uncertainty cannot be promoted to PASS without evidence-based resolution: "
                + ", ".join(sorted(unresolved))
            )

    all_findings: dict[str, dict[str, Any]] = {}
    for item in normalized:
        for finding in item["findings"]:
            finding_id = finding["id"]
            if finding_id in all_findings:
                raise ValidationError(f"finding ids must be globally unique across reviewers: {finding_id}")
            all_findings[finding_id] = finding
    disposition_values = _expect_list(judgment["finding_dispositions"], "judgment.finding_dispositions")
    dispositions: dict[str, dict[str, Any]] = {}
    for index, disposition_value in enumerate(disposition_values):
        context = f"judgment.finding_dispositions[{index}]"
        disposition = _expect_object(disposition_value, context)
        require_keys(disposition, ("finding_id", "disposition", "rationale", "evidence_ref"), context)
        finding_id = disposition["finding_id"]
        if finding_id not in all_findings or finding_id in dispositions:
            raise ValidationError(f"{context}.finding_id is invalid or duplicated")
        if disposition["disposition"] not in FINDING_DISPOSITIONS:
            raise ValidationError(f"{context}.disposition is invalid")
        require_clean_text(disposition["rationale"], f"{context}.rationale", minimum=5)
        evidence_ref = disposition["evidence_ref"]
        if not isinstance(evidence_ref, str):
            raise ValidationError(f"{context}.evidence_ref must be text (empty is allowed for non-dismissals)")
        finding = all_findings[finding_id]
        if disposition["disposition"] == "DISMISSED" and finding["severity"] in {"critical", "high"}:
            if evidence_ref not in evidence_check_ids:
                raise ValidationError("critical/high finding dismissal requires a passed evidence check reference")
        dispositions[finding_id] = disposition
    if set(dispositions) != set(all_findings):
        missing = set(all_findings) - set(dispositions)
        raise ValidationError("judgment silently dropped findings: " + ", ".join(sorted(missing)))
    act_on = [finding_id for finding_id, item in dispositions.items() if item["disposition"] == "ACT_ON"]
    if judgment["decision"] == "PASS" and act_on:
        raise ValidationError("PASS judgment cannot retain ACT_ON findings")

    providers = {(item["reviewer"]["provider"], item["reviewer"]["model"]) for item in normalized}
    proof_level = "diverse-reviewed" if len(providers) >= 2 else "peer-reviewed"
    return {
        "decision": judgment["decision"],
        "reviewer_count": len(normalized),
        "proof_level": proof_level,
        "conflicts": sorted(conflicts),
        "resolved_nonpass": sorted(nonpass & set(resolutions)),
        "act_on": act_on,
        "judge": judge,
    }
