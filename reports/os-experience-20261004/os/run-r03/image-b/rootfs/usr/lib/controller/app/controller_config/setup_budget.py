"""Durable, disconnected USD budget gate for a single assisted-setup session.

Only a *new*, durably committed reservation grants ``dispatch_allowed``. Repeating
an ID is a lookup, never permission to repeat a paid operation. A trusted billing
adapter must supply approved prices, finite usage bounds, and billing evidence;
this module neither authenticates invoices nor calls a provider or a machine.

Amounts are integer microdollars (1 USD = 1,000,000). Token limits count uncached
input, cached input and output separately. Output includes billed reasoning.
Tool prices are fixed worst-case USD charges per call; unbounded/unknown pricing
cannot be represented. Locks coordinate processes on one local filesystem, not
independent computers editing a cloud-synchronized copy of the ledger.
"""

from contextlib import contextmanager
from copy import deepcopy
import errno
import os
from pathlib import Path
import re

from .model import ConfigurationError
from .service import atomic_write, digest, read_json


MAX_CAP_MICRODOLLARS = 15_000_000
MAX_INTEGER = (1 << 63) - 1
# Bounds leave space under the shared 2 MB document limit for settlement evidence
# of every outstanding request, including the largest allowed usage/tool map.
MAX_REQUESTS = 100
TOKEN_KINDS = ("input_tokens", "cached_input_tokens", "output_tokens")
NO_CHARGE_DISPOSITIONS = ("provider_confirmed_no_charge", "cancelled_before_dispatch")


class BudgetError(ConfigurationError):
    """Structured budget error, compatible with the shared service errors."""


def _require(condition, code, message):
    if not condition:
        raise BudgetError(code, message)


def _keys(value, keys, code="BUDGET_INPUT"):
    _require(type(value) is dict and set(value) == set(keys), code, "Unexpected budget document fields")


def _integer(value, name, maximum=MAX_INTEGER):
    _require(type(value) is int and 0 <= value <= maximum, "BUDGET_INPUT", f"{name} must be a nonnegative bounded integer, not a float or boolean")
    return value


def _label(value, name):
    _require(type(value) is str and bool(value.strip()) and len(value) <= 128 and all(32 <= ord(c) < 127 for c in value), "BUDGET_INPUT", f"{name} must be a nonempty printable ASCII label of at most 128 characters")
    return value


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "BUDGET_INPUT", "payload_sha256 must be a lowercase SHA-256 digest; do not persist prompts or secrets")
    return value


def _usage(value, prices=None):
    _keys(value, (*TOKEN_KINDS, "tool_calls"))
    for key in TOKEN_KINDS:
        _integer(value[key], key)
    calls = value["tool_calls"]
    _require(type(calls) is dict and len(calls) <= 16, "BUDGET_INPUT", "tool_calls must contain at most 16 priced tools")
    for name, count in calls.items():
        _label(name, "tool")
        if prices is not None:
            _require(name in prices, "BUDGET_PRICING_UNKNOWN", f"No USD price for tool {name}")
        _integer(count, "tool call limit")


def estimate_microdollars(pricing, limits):
    """Compute a conservative ceiling per token category plus bounded tool fees.

    ``*_tokens`` prices are microdollars per million tokens. ``tool_calls``
    prices are microdollars per call. These values require a trusted caller.
    """
    _keys(pricing, ("currency", "version", "microdollars_per_million_tokens", "microdollars_per_tool_call"))
    _require(pricing["currency"] == "USD", "BUDGET_CURRENCY", "Only explicit USD prices are supported; unknown exchange costs block spending")
    _label(pricing["version"], "price-table version")
    rates = pricing["microdollars_per_million_tokens"]
    _keys(rates, TOKEN_KINDS)
    for key in TOKEN_KINDS:
        _integer(rates[key], key + " price")
    tools = pricing["microdollars_per_tool_call"]
    _require(type(tools) is dict and len(tools) <= 16, "BUDGET_INPUT", "At most 16 fixed-price tools are supported")
    for name, price in tools.items():
        _label(name, "tool")
        _integer(price, "tool price")
    _usage(limits, tools)
    amount = sum((limits[k] * rates[k] + 999_999) // 1_000_000 for k in TOKEN_KINDS)
    amount += sum(count * tools[name] for name, count in limits["tool_calls"].items())
    return _integer(amount, "reservation cost")


def budget_schema():
    """Bounded discovery contract; no pricing, provider or machine is inferred."""
    integer = {"type": "integer", "minimum": 0, "maximum": MAX_INTEGER}
    label = {"type": "string", "minLength": 1, "maxLength": 128, "pattern": "^(?=.*[^ ])[ -~]+$"}
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    usage = obj({**{key: deepcopy(integer) for key in TOKEN_KINDS}, "tool_calls": {"type": "object", "maxProperties": 16, "additionalProperties": deepcopy(integer)}})
    pricing = obj({"currency": {"const": "USD"}, "version": deepcopy(label), "microdollars_per_million_tokens": obj({key: deepcopy(integer) for key in TOKEN_KINDS}), "microdollars_per_tool_call": {"type": "object", "maxProperties": 16, "additionalProperties": deepcopy(integer)}})
    return {"schema_version": 1, "currency": "USD", "unit": "microdollar", "microdollars_per_USD": 1_000_000,
            "maximum_session_cap_microdollars": MAX_CAP_MICRODOLLARS, "maximum_requests": MAX_REQUESTS,
            "authority": "local budget only; no network, secrets or machine authority",
            "trusted_adapter_required": ["approved provider/model/version pricing", "worst-case token/reasoning/tool limits", "authoritative billing or no-charge disposition"],
            "operations": ["create", "status", "reserve", "mark_unknown", "settle", "resolve_no_charge", "freeze"],
            "pricing": pricing, "limits_and_usage": usage,
            "reservation": obj({"request_id": deepcopy(label), "payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "provider": deepcopy(label), "model": deepcopy(label), "model_version": deepcopy(label), "pricing": pricing, "limits": usage}),
            "no_charge_dispositions": list(NO_CHARGE_DISPOSITIONS),
            "duplicate_dispatch_allowed": False, "unknown_charge_releases_reservation": False,
            "over_reservation_charge": "record actual spend and permanently block new reservations"}


class BudgetLedger:
    """One immutable-cap setup session per directory or explicit .json file.

    Construction/read never initializes or resets spending. ``create`` is
    explicit and cannot replace an existing session. The file is checksummed
    for accidental corruption, not signed against a hostile local account.
    """

    def __init__(self, path):
        target = Path(path).expanduser().resolve()
        self.path = target if target.suffix.lower() == ".json" and not target.is_dir() else target / "budget.json"

    @staticmethod
    def schema():
        return budget_schema()

    @staticmethod
    def discovery():
        return budget_schema()

    @contextmanager
    def _lock(self):
        """OS lock is released after process death; never unlink a live lock file."""
        _require(self.path.parent.is_dir(), "BUDGET_NOT_FOUND", "Budget directory does not exist; explicitly create a session first")
        handle = None
        acquired = False
        try:
            handle = os.open(str(self.path) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
            os.lseek(handle, 0, os.SEEK_SET)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as error:
                if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise BudgetError("BUDGET_BUSY", "Another process holds the budget ledger; no dispatch was authorized") from error
                raise
            # Initialize the stable lock byte after ownership. Writing it
            # before the Windows byte-range lock races a concurrent owner and
            # can incorrectly surface BUDGET_IO during first-session creation.
            if os.fstat(handle).st_size == 0:
                os.write(handle, b"\0")
            yield
        except OSError as error:
            raise BudgetError("BUDGET_IO", "Budget persistence failed; do not dispatch or assume a reservation was released") from error
        finally:
            if handle is not None:
                try:
                    if acquired:
                        os.lseek(handle, 0, os.SEEK_SET)
                        if os.name == "nt":
                            import msvcrt
                            msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(handle, fcntl.LOCK_UN)
                finally:
                    os.close(handle)

    @staticmethod
    def _binding(payload_sha256, provider, model, model_version, pricing, limits):
        _hash(payload_sha256)
        for value, name in ((provider, "provider"), (model, "model"), (model_version, "model_version")):
            _label(value, name)
        estimate_microdollars(pricing, limits)
        return deepcopy(dict(payload_sha256=payload_sha256, provider=provider, model=model, model_version=model_version, pricing=pricing, limits=limits))

    def _read(self):
        _require(self.path.is_file(), "BUDGET_NOT_FOUND", "No budget session exists; explicitly create one first")
        try:
            sealed = read_json(self.path)
            _keys(sealed, ("schema_version", "kind", "session_id", "currency", "cap_microdollars", "revision", "requests", "administrative_hold", "sha256"))
            value = {k: v for k, v in sealed.items() if k != "sha256"}
            _require(sealed["sha256"] == digest(value), "BUDGET_CORRUPT", "Budget checksum mismatch; do not recreate the ledger or release funds")
            _require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "setup-budget" and value["currency"] == "USD", "BUDGET_CORRUPT", "Unsupported budget document")
            _label(value["session_id"], "session_id")
            _integer(value["cap_microdollars"], "cap", MAX_CAP_MICRODOLLARS)
            _integer(value["revision"], "revision")
            if value["administrative_hold"] is not None:
                _label(value["administrative_hold"], "administrative_hold")
            _require(type(value["requests"]) is dict and len(value["requests"]) <= MAX_REQUESTS, "BUDGET_CORRUPT", "Invalid request inventory")
            for request_id, row in value["requests"].items():
                _label(request_id, "request_id")
                _keys(row, ("binding", "binding_sha256", "reserved_microdollars", "state", "settlement"))
                _keys(row["binding"], ("payload_sha256", "provider", "model", "model_version", "pricing", "limits"))
                binding = self._binding(**row["binding"])
                _integer(row["reserved_microdollars"], "reservation")
                _require(row["binding_sha256"] == digest(binding) and row["reserved_microdollars"] == estimate_microdollars(binding["pricing"], binding["limits"]), "BUDGET_CORRUPT", "Reservation binding or cost mismatch")
                _require(row["state"] in ("reserved", "unknown", "settled", "no_charge"), "BUDGET_CORRUPT", "Invalid reservation state")
                if row["state"] in ("reserved", "unknown"):
                    _require(row["settlement"] is None, "BUDGET_CORRUPT", "Outstanding request contains a settlement")
                else:
                    settlement = row["settlement"]
                    _keys(settlement, ("actual_microdollars", "evidence_id", "usage", "disposition"))
                    _integer(settlement["actual_microdollars"], "actual charge")
                    _label(settlement["evidence_id"], "billing evidence")
                    if settlement["usage"] is not None:
                        _usage(settlement["usage"])
                    if row["state"] == "no_charge":
                        _require(settlement["actual_microdollars"] == 0 and settlement["usage"] is None and settlement["disposition"] in NO_CHARGE_DISPOSITIONS, "BUDGET_CORRUPT", "Invalid no-charge disposition")
                    else:
                        _require(settlement["actual_microdollars"] > 0 and settlement["disposition"] == "provider_charge", "BUDGET_CORRUPT", "Invalid charge disposition")
            summary = self._summary(value)
            _require(summary["spent_microdollars"] + summary["outstanding_microdollars"] <= value["cap_microdollars"] or bool(summary["overrun_request_ids"]), "BUDGET_CORRUPT", "Unexplained budget cap violation")
            return value
        except ConfigurationError as error:
            if error.code in ("BUDGET_CORRUPT", "IO_ERROR"):
                raise
            raise BudgetError("BUDGET_CORRUPT", "Invalid persisted budget; retain the file and reconcile it before spending") from error
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise BudgetError("BUDGET_CORRUPT", "Invalid persisted budget; no dispatch authorized") from error

    def _write(self, value):
        value["revision"] += 1
        atomic_write(self.path, {**value, "sha256": digest(value)})

    @staticmethod
    def _summary(value):
        rows = value["requests"].values()
        spent = sum(r["settlement"]["actual_microdollars"] for r in rows if r["state"] in ("settled", "no_charge"))
        outstanding = sum(r["reserved_microdollars"] for r in rows if r["state"] in ("reserved", "unknown"))
        overruns = [key for key, r in value["requests"].items() if r["state"] == "settled" and r["settlement"]["actual_microdollars"] > r["reserved_microdollars"]]
        return {"schema_version": 1, "session_id": value["session_id"], "currency": "USD", "unit": "microdollar", "revision": value["revision"],
                "cap_microdollars": value["cap_microdollars"], "spent_microdollars": spent, "outstanding_microdollars": outstanding,
                "remaining_microdollars": max(0, value["cap_microdollars"] - spent - outstanding), "blocked": bool(overruns or value["administrative_hold"]),
                "blocked_reason": "reservation_overrun" if overruns else value["administrative_hold"], "overrun_request_ids": overruns,
                "request_count": len(value["requests"]), "machine_authority": False}

    def _receipt(self, value, request_id, *, dispatch=False, idempotent=False):
        return {"request_id": request_id, **deepcopy(value["requests"][request_id]), "dispatch_allowed": dispatch, "idempotent": idempotent, "budget": self._summary(value)}

    def create(self, session_id, cap_microdollars=MAX_CAP_MICRODOLLARS):
        _label(session_id, "session_id")
        _integer(cap_microdollars, "cap_microdollars", MAX_CAP_MICRODOLLARS)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise BudgetError("BUDGET_IO", "Cannot create budget directory") from error
        with self._lock():
            if self.path.exists():
                value = self._read()
                _require(value["session_id"] == session_id and value["cap_microdollars"] == cap_microdollars, "BUDGET_EXISTS", "Existing session/cap cannot be replaced or topped up")
                return self._summary(value)
            value = dict(schema_version=1, kind="setup-budget", session_id=session_id, currency="USD", cap_microdollars=cap_microdollars, revision=0, requests={}, administrative_hold=None)
            self._write(value)
            return self._summary(value)

    def status(self):
        with self._lock():
            value = self._read()
            return {**self._summary(value), "requests": deepcopy(value["requests"])}

    def reserve(self, request_id, *, payload_sha256, provider, model, model_version, pricing, limits):
        _label(request_id, "request_id")
        binding = self._binding(payload_sha256, provider, model, model_version, pricing, limits)
        amount = estimate_microdollars(pricing, limits)
        with self._lock():
            value = self._read()
            if request_id in value["requests"]:
                _require(value["requests"][request_id]["binding_sha256"] == digest(binding), "BUDGET_REQUEST_CONFLICT", "Request ID already belongs to a different payload, model, pricing or usage bound")
                return self._receipt(value, request_id, idempotent=True)
            current = self._summary(value)
            _require(not current["blocked"], "BUDGET_BLOCKED", "A reservation overrun blocks further paid operations")
            _require(len(value["requests"]) < MAX_REQUESTS, "BUDGET_REQUEST_LIMIT", "Session request inventory is full; existing reservations still require reconciliation")
            _require(amount <= current["remaining_microdollars"], "BUDGET_EXHAUSTED", "Worst-case charge exceeds unreserved session allowance")
            value["requests"][request_id] = dict(binding=binding, binding_sha256=digest(binding), reserved_microdollars=amount, state="reserved", settlement=None)
            self._write(value)
            return self._receipt(value, request_id, dispatch=True)

    def mark_unknown(self, request_id):
        """Timeout/unknown billing consumes no additional allowance and frees none."""
        _label(request_id, "request_id")
        with self._lock():
            value = self._read()
            _require(request_id in value["requests"], "BUDGET_REQUEST_UNKNOWN", "No such reserved request")
            row = value["requests"][request_id]
            if row["state"] != "reserved":
                return self._receipt(value, request_id, idempotent=True)
            row["state"] = "unknown"
            self._write(value)
            return self._receipt(value, request_id)

    def freeze(self, reason):
        """Permanently block new calls after contradictory/over-limit usage.

        Outstanding charges can still be reconciled. There is deliberately no
        automatic unfreeze or cap reset operation.
        """
        _label(reason, "reason")
        with self._lock():
            value = self._read()
            if value["administrative_hold"] is None:
                value["administrative_hold"] = reason
                self._write(value)
            return self._summary(value)

    def _settle(self, request_id, settlement, state):
        _label(request_id, "request_id")
        _label(settlement["evidence_id"], "billing evidence")
        _integer(settlement["actual_microdollars"], "actual charge")
        with self._lock():
            value = self._read()
            _require(request_id in value["requests"], "BUDGET_REQUEST_UNKNOWN", "Cannot settle a request without its reservation")
            row = value["requests"][request_id]
            if settlement["usage"] is not None:
                # Actual billed tools can differ from the approved envelope.
                # Their known final USD charge must still be recorded.
                _usage(settlement["usage"])
            if row["state"] in ("settled", "no_charge"):
                _require(row["state"] == state and digest(row["settlement"]) == digest(settlement), "BUDGET_SETTLEMENT_CONFLICT", "A settled request cannot be charged or released again with different evidence")
                return self._receipt(value, request_id, idempotent=True)
            # A provider overrun MUST be persisted even when it exceeds the cap.
            # _summary then permanently blocks new reservations; outstanding
            # requests remain accounted for and can still be reconciled.
            row["state"], row["settlement"] = state, deepcopy(settlement)
            self._write(value)
            return self._receipt(value, request_id)

    def settle(self, request_id, *, actual_microdollars, evidence_id, usage=None):
        """Record the authoritative final USD charge, including paid tools.

        No estimate is substituted for unknown billing. An exact replay is
        idempotent; conflicting final settlements require external accounting
        review and are rejected. Overruns return a persisted blocked status.
        """
        _integer(actual_microdollars, "actual charge")
        _require(actual_microdollars > 0, "BUDGET_DISPOSITION", "Use an explicit authoritative no-charge disposition to release a zero-charge request")
        return self._settle(request_id, dict(actual_microdollars=actual_microdollars, evidence_id=evidence_id, usage=usage, disposition="provider_charge"), "settled")

    def resolve_no_charge(self, request_id, *, evidence_id, disposition):
        """Trusted adapter only: authoritative no-charge or proven never sent."""
        _require(disposition in NO_CHARGE_DISPOSITIONS, "BUDGET_DISPOSITION", "Timeout, retry exhaustion and local cancellation do not prove no charge")
        return self._settle(request_id, dict(actual_microdollars=0, evidence_id=evidence_id, usage=None, disposition=disposition), "no_charge")
