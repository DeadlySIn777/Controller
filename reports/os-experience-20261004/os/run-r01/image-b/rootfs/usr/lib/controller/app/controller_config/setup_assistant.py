"""Grounded, non-actuating setup guidance. Paid advice is an optional separate adapter.

There is intentionally no motion/output transport or execution tool in this module.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import math
import re

from .model import ConfigurationError
from .service import digest
from .setup_facts import FIELDS, inspect_facts


FACT_DESCRIPTIONS = {
    "motor_steps_per_revolution": ("Full motor steps per revolution", "Full-step motor count; do not confuse it with microsteps or encoder counts."),
    "microsteps": ("Selected microsteps per full step", "Use the actual drive switch or configuration selection; an advertised maximum is not the selected value."),
    "gear_motor_revolutions": ("Motor revolutions in the mechanical ratio", "State the motor-side count and load-side count separately to avoid reversing the ratio."),
    "gear_load_revolutions": ("Load revolutions in the mechanical ratio", "The paired motor/load counts determine mechanical reduction; do not infer a direct drive."),
    "travel_per_load_revolution": ("Travel per load revolution", "Use each motor's selected mm or inch unit; distinguish screw lead from pitch on a multi-start screw."),
    "max_velocity_units_per_second": ("Requested maximum travel speed", "State mm/s or in/s explicitly. This is an operating request, not a verified hardware rating."),
}


def intake_groups(draft, missing):
    """Group only the validator's missing mechanical facts; never infer answers."""
    missing_paths = {fact["path"] for fact in missing}
    groups = []
    saved = []
    for field in FIELDS:
        members = []
        for index, motor in enumerate(draft["motors"]):
            path = f"$.motors[{index}].{field}"
            unit = motor["unit"] + ("/s" if field == "max_velocity_units_per_second" else "") if field in FIELDS[-2:] else "dimensionless"
            if path in missing_paths:
                members.append({"path": path, "logical_motor_id": motor["id"], "unit": unit})
            elif motor[field] is not None:
                saved.append({"path": path, "logical_motor_id": motor["id"], "value": motor[field], "unit": unit, "source": "saved_user_selection_not_physical_verification"})
        if members:
            label, why = FACT_DESCRIPTIONS[field]
            groups.append({"field": field, "label": label, "why": why, "members": members,
                           "question": f"{label} for {', '.join(member['logical_motor_id'] for member in members)}? {why}"})
    return groups, saved


def local_intake(service, facts, *, expected_revision):
    """Create a grounded review candidate without writes, network or actuation.

    Supported intake is deliberately exact: one positive, motor-specific fact
    per statement, with configured units on travel/velocity. Saved values are
    retained. A conflicting value needs an ordinary explicit field edit.
    """
    if type(facts) is not str or not facts.strip() or len(facts) > 12_000 or any(ord(c) < 32 and c not in "\r\n\t" for c in facts):
        raise ConfigurationError("INTAKE_FACTS", "Use nonempty mechanical facts of at most 12000 characters")
    status = service.status()
    if type(expected_revision) is not int or expected_revision != status.get("current_revision"):
        raise ConfigurationError("INTAKE_STALE", "Setup changed; refresh the saved draft before interpreting facts")
    draft = status.get("draft")
    if status.get("initialized") is not True or draft is None:
        raise ConfigurationError("INTAKE_NO_DRAFT", "Select and save a simulation profile before entering motor-specific facts")
    packet = inspect_facts(facts, draft)
    candidate, accepted, retained = deepcopy(draft), [], []
    conflicts = deepcopy(packet["issues"])
    blocked = {issue["path"] for issue in conflicts}
    for path, records in packet["records"].items():
        if path in blocked:
            continue
        source = records[0]
        motor_index = next(i for i, motor in enumerate(draft["motors"]) if motor["id"] == source["motor_id"])
        current = draft["motors"][motor_index][source["field"]]
        try:
            parsed = Decimal(source["value_text"])
            if current is not None:
                if Decimal(str(current)) != parsed:
                    conflicts.append({"code": "INTAKE_SAVED_CONFLICT", "path": path, "message": "The new statement differs from an already saved value. The saved value was retained; review an explicit field edit to change it.", "saved_value": current, "source_quotes": [record["statement"] for record in records]})
                else:
                    retained.append({"path": path, "value": current, "source_quotes": [record["statement"] for record in records]})
                continue
            # Service bounds are far smaller than this parser conversion bound.
            # Reject enormous exponents before integer/float allocation.
            if not parsed.is_finite() or parsed.copy_abs() > Decimal("1000000"):
                raise ValueError("outside mechanical bound")
            if source["field"] in FIELDS[:2]:
                if parsed != parsed.to_integral_value():
                    raise ValueError("integer required")
                value = int(parsed)
            else:
                value = float(parsed)
                if not math.isfinite(value):
                    raise ValueError("nonfinite")
            single = deepcopy(candidate)
            single["motors"][motor_index][source["field"]] = value
            service.validate_draft(single)
        except (ConfigurationError, InvalidOperation, ValueError, OverflowError) as error:
            conflicts.append({"code": error.code if isinstance(error, ConfigurationError) else "INTAKE_VALUE", "path": path, "message": "The explicit value fails mechanical schema validation; the field was retained.", "source_quotes": [record["statement"] for record in records]})
            continue
        candidate = single
        accepted.append({"path": path, "value": value, "source_quote": source["statement"],
                         "source_quotes": [record["statement"] for record in records],
                         "logical_motor_id": source["motor_id"], "unit": source["unit"],
                         "provenance": "unverified_user_statement_requires_review"})
    validation = service.validate_draft(candidate)
    binding = {"store_id": status["store_id"], "epoch": status["epoch"], "revision": status["current_revision"],
               "profile_id": draft["profile_id"], "draft_sha256": digest(draft),
               "catalog_sha256": digest({"capabilities": service.capabilities(), "profiles": service.profiles(), "equipment": service.equipment_profiles()})}
    # Recheck the saved context after validation. A concurrently changed store
    # cannot return a candidate labelled as the new current revision.
    after = service.status()
    if (after.get("store_id"), after.get("epoch"), after.get("current_revision"), digest(after.get("draft"))) != (binding["store_id"], binding["epoch"], binding["revision"], binding["draft_sha256"]):
        raise ConfigurationError("INTAKE_STALE", "Setup changed while interpreting facts; preserve the text and refresh the draft")
    return {"schema_version": 1, "mode": "deterministic_offline_intake", "status": "facts_need_review" if conflicts or validation["blockers"] else "candidate" if accepted else "no_new_supported_facts",
            "facts_text": facts, "proposed_draft": candidate, "validation": validation, "accepted_facts": accepted,
            "conflicts": conflicts, "unknowns": packet["unknown_statements"], "known_facts_retained": retained,
            "configuration_binding": binding, "supported_syntax": packet["supported_syntax"],
            "simulation_only": True, "physical_commissioning_complete": False, "motion_authorized": False,
            "outputs_inhibited": True, "homed": False, "paid_calls": 0, "provider_requests": 0,
            "machine_commands": [], "executed": False}


def local_guidance(service, question="What remains to complete setup?"):
    if type(question) is not str or not question.strip() or len(question) > 2000:
        raise ConfigurationError("QUESTION", "Use a nonempty question of at most 2000 characters")
    status = service.status()
    draft = status.get("draft")
    blockers = []
    groups, saved = [], []
    if draft is None:
        message = "Choose a simulation machine profile first. Then enter the known drive and mechanical values. I can explain setup, but I cannot home, jog, start a job or energize outputs."
        missing = []
    else:
        validation = service.validate_draft(draft)
        missing = validation["missing_facts"]
        blockers = validation["blockers"]
        groups, saved = intake_groups(draft, missing)
        if blockers:
            message = "Resolve these configuration checks before review:\n" + "\n".join(f"• {item['message']} ({item['path']})" for item in blockers[:12])
            if missing:
                message += f"\n{len(missing)} mechanical details also remain unanswered."
        elif missing:
            message = "Answer these grouped mechanical questions for the listed logical motor IDs:\n" + "\n".join(f"• {group['question']}" for group in groups)
            message += "\nAlready saved values will not be requested again. Use the labeled simulation example only to explore the workflow."
        else:
            message = "Your draft has all required mechanical facts. Choose Check my setup to calculate scales and validate timing, rates and assignments, then review the exact changes. Physical wiring, direction, homing and qualification remain unverified."
        lower = question.lower()
        if re.search(r"\b(?:scale|microsteps?|ratio|steps|lead)\b", lower):
            message = "Scale = motor full steps × microsteps × (motor revolutions / load revolutions) ÷ travel per load revolution. The backend calculates it in your selected distance unit and checks the resulting pulse rate.\n\n" + message
        if re.search(r"\b(?:home|homing|jog|spindle|run|stop)\b", lower):
            message = "No machine command was sent. This disconnected setup guide has no motion, spindle or job controls.\n\n" + message
    return {"schema_version": 1, "mode": "deterministic_offline_guidance", "message": message,
            "missing_facts": missing, "blockers": blockers, "configuration_revision": status.get("current_revision", 0),
            "intake_groups": groups, "saved_facts": saved,
            "simulation_only": True, "paid_calls": 0, "machine_commands": [], "executed": False}
