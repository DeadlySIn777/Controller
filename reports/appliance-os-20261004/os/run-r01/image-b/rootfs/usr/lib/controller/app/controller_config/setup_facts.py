"""Bounded explicit mechanical intake, independent of a model or machine.

Only complete, positively stated facts with a logical ``m0``-style identity
are supported. Unrecognized wording remains unresolved. This is not a general
manual parser and cannot establish equipment approval or physical verification.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re


FIELDS = ("motor_steps_per_revolution", "microsteps", "gear_motor_revolutions",
          "gear_load_revolutions", "travel_per_load_revolution", "max_velocity_units_per_second")
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
IDENTITY = re.compile(r"\s*(?:(?i:motor)\s+)?(?P<motor>m\d+)\b\s*(?P<body>.*)")
# Retain decimal dots while separating independent statements and lines.
STATEMENTS = re.compile(r"[^;\r\n!?]+?(?:\.(?=\s+[A-Z]|\s*$)|[;\r\n!?]|$)")
MARKERS = {
    "motor_steps_per_revolution": r"full\s+steps\s+per\s+(?:motor\s+)?revolution",
    "microsteps": r"microsteps?(?:\s+per\s+full\s+step)?",
    "gear_motor_revolutions": r"motor\s+revolutions?",
    "gear_load_revolutions": r"load\s+revolutions?",
    "travel_per_load_revolution": r"travel\s+per\s+load\s+revolution",
    "max_velocity_units_per_second": r"(?:maximum|max)\s+velocity",
}


def _decimal(value):
    try:
        parsed = Decimal(value)
        return parsed if parsed.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _formats(field):
    number = f"(?P<value>{NUMBER})"
    unit = r"(?P<unit>mm|in|inch|inches)"
    key = re.escape(field)
    if field == "motor_steps_per_revolution":
        return [rf"(?:has|uses|:)\s*{number}\s+{MARKERS[field]}",
                rf"{key}\s*[=:]\s*{number}(?:\s+{MARKERS[field]})?"]
    if field == "microsteps":
        return [rf"(?:has|uses|:)\s*{number}\s+{MARKERS[field]}",
                rf"{key}\s*[=:]\s*{number}(?:\s+microsteps?(?:\s+per\s+full\s+step)?)?"]
    if field in ("gear_motor_revolutions", "gear_load_revolutions"):
        return [rf"(?:{key}|{MARKERS[field]})\s*[=:]\s*{number}(?:\s+revolutions?)?"]
    if field == "travel_per_load_revolution":
        return [rf"(?:{key}|{MARKERS[field]})\s*[=:]\s*{number}\s*{unit}",
                rf"(?:has|:)\s*{number}\s*{unit}\s+{MARKERS[field]}"]
    return [rf"{key}\s*[=:]\s*{number}\s*{unit}\s*/\s*s",
            rf"{MARKERS[field]}\s*(?:is|[=:])\s*{number}\s*{unit}\s*/\s*s"]


def inspect_facts(facts, draft):
    """Associate explicit statements with one exact configured logical motor.

    A field is usable only when every relevant recognized statement is complete,
    unambiguous, in the configured unit, and agrees. Duplicate identical facts
    are harmless; contradictory, negated and conditional wording is unresolved.
    Every accepted quote still describes a user statement, never measured fact.
    """
    records, issues, referenced, unknowns = {}, [], {}, []
    motors = {motor["id"]: (i, motor) for i, motor in enumerate(draft["motors"])}
    for segment in STATEMENTS.finditer(facts):
        statement = segment.group().strip().rstrip(".;!?\r\n ")
        identity = IDENTITY.fullmatch(statement)
        if not statement:
            continue
        if identity is None or identity["motor"] not in motors:
            unknowns.append({"statement": statement, "reason": "Use one explicit fact for a configured logical motor ID m0, m1, etc.; unsupported wording remains unresolved."})
            continue
        index, motor = motors[identity["motor"]]
        body = identity["body"]
        spans = [(field, match.span()) for field in FIELDS
                 for match in re.finditer(rf"\b(?:{re.escape(field)}|{MARKERS[field]})\b", body, re.I)]
        # 'Travel per load revolution' describes travel, not the denominator
        # count as well. Prefer a complete field phrase over a nested fragment.
        referenced_fields = {field for field, span in spans
                             if not any(other != field and outer[0] <= span[0] and span[1] <= outer[1] and outer != span
                                        for other, outer in spans)}
        recognized = False
        for field in FIELDS:
            if field not in referenced_fields:
                continue
            path = f"$.motors[{index}].{field}"
            recognized = True
            referenced.setdefault(path, []).append(statement)
            matched = next((match for pattern in _formats(field)
                            if (match := re.fullmatch(pattern, body, re.I)) is not None), None)
            if matched is None:
                issues.append({"code": "AI_FACT_AMBIGUOUS", "path": path,
                               "message": "State one positive motor-specific fact with its field and unit; conditional, negated or mixed wording stays unresolved."})
                continue
            raw = matched["value"]
            value = _decimal(raw)
            if value is None:
                issues.append({"code": "AI_SOURCE_VALUE", "path": path, "message": "The explicitly stated number cannot be represented."})
                continue
            stated_unit = matched.groupdict().get("unit")
            if stated_unit and ("in" if stated_unit.lower() in ("in", "inch", "inches") else "mm") != motor["unit"]:
                issues.append({"code": "AI_FACT_UNIT", "path": path,
                               "message": f"The stated unit differs from configured {motor['unit']}; select or convert units explicitly before review."})
                continue
            records.setdefault(path, []).append({"value_text": raw, "statement": statement,
                                                 "source": "unverified_user_statement",
                                                 "motor_id": motor["id"], "field": field,
                                                 "unit": motor["unit"] + ("/s" if field == "max_velocity_units_per_second" else "") if stated_unit else "dimensionless"})
        if not recognized:
            unknowns.append({"statement": statement, "reason": "No supported mechanical field was explicitly identified; equipment, timing and commissioning are never inferred."})
    for path, rows in records.items():
        if len({_decimal(row["value_text"]) for row in rows}) > 1:
            issues.append({"code": "AI_FACT_CONFLICT", "path": path,
                           "message": "Different values were stated for this motor and field; resolve the conflict before proposing it."})
    # Keep per-field conflicts/ambiguities rather than silently preferring the
    # last or the first source. Exact repeated problems are grouped once.
    issues = list({(issue["code"], issue["path"]): issue for issue in issues}.values())
    for issue in issues:
        issue["source_quotes"] = list(referenced.get(issue["path"], []))
    return {"schema_version": 1, "records": records, "issues": issues,
            "referenced_paths": list(referenced), "unknown_statements": unknowns, "source": "unverified_user_statements",
            "supported_syntax": "One statement per line: Motor m0 motor_steps_per_revolution = 200; Motor m0 microsteps = 16; Motor m0 travel_per_load_revolution = 5 mm; Motor m0 max_velocity_units_per_second = 10 mm/s. m0 is the logical ID, not the M1 panel label."}


def proposal_evidence(packet, path, value, quote):
    """Return a deterministic error or the exact associated source statement."""
    relevant = [issue for issue in packet["issues"] if issue["path"] == path]
    if relevant:
        return relevant[0], None
    for record in packet["records"].get(path, []):
        if (_decimal(record["value_text"]) == _decimal(str(value)) and
                quote in record["statement"] and
                # A number alone cannot identify its mechanical meaning.
                re.search(rf"\b(?:{re.escape(record['field'])}|{MARKERS[record['field']]})\b", quote, re.I)):
            return None, deepcopy(record)
    return {"code": "AI_FACT_ASSOCIATION", "path": path,
            "message": "The quote does not prove this exact logical motor, mechanical field, value and unit. Restate one explicit fact before review."}, None
