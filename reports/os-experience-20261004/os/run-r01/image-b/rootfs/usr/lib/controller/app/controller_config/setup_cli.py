"""Public adapter for the versioned disconnected IS-2 setup service."""
from pathlib import Path

from .service import export_json, read_json


def add_commands(commands):
    root = commands.add_parser("setup", help="IS-2 setup workbench; disconnected simulation only")
    root.add_argument("--directory", default=".controller-setup-demo", help="Separate setup state directory; never a machine configuration")
    sub = root.add_subparsers(dest="setup_operation", required=True)
    for name in ("capabilities", "schema", "profiles", "status", "init", "audit", "budget", "readiness"):
        sub.add_parser(name)
    rehearsal = sub.add_parser("self-check", help="Exercise the saved simulation configuration and backup; no motion test")
    rehearsal.add_argument("--expected-revision", type=int, required=True)
    intake = sub.add_parser("intake", help="Extract explicit supported facts locally; no API spend or settings write")
    intake.add_argument("--facts-file", required=True)
    intake.add_argument("--expected-revision", type=int, required=True)
    template = sub.add_parser("template")
    template.add_argument("profile_id")
    template.add_argument("--output")
    example = sub.add_parser("example", help="Explicit authored simulation example; never machine defaults")
    example.add_argument("profile_id")
    example.add_argument("--output")
    request = sub.add_parser("request-result")
    request.add_argument("request_id")
    restart = sub.add_parser("restart-epoch", help="Invalidate outstanding local previews; no hardware reset")
    restart.add_argument("--expected-revision", type=int, required=True)
    save = sub.add_parser("save")
    save.add_argument("file")
    save.add_argument("--expected-revision", type=int, required=True)
    save.add_argument("--expected-binding", help="JSON draft_binding from status; binds identity, epoch and original draft too")
    preview = sub.add_parser("preview")
    preview.add_argument("--file")
    preview.add_argument("--output")
    commit = sub.add_parser("commit")
    commit.add_argument("file")
    commit.add_argument("--request-id", required=True)
    restore = sub.add_parser("restore-preview")
    restore.add_argument("generation", type=int)
    restore.add_argument("--output")
    export = sub.add_parser("export")
    export.add_argument("output")
    diagnostics = sub.add_parser("diagnostics", help="Offline compressed recorder and fault reports; no hardware connection")
    diagnostic_ops = diagnostics.add_subparsers(dest="diagnostic_operation", required=True)
    diagnostic_ops.add_parser("status")
    diagnostic_ops.add_parser("state", help="Read the configuration-bound simulation machine state")
    diagnostic_ops.add_parser("state-schema", help="Typed observation contract; no discovery or measurements")
    observation = diagnostic_ops.add_parser("observation-example", help="Export a bound authored observation; never a measured machine sample")
    observation.add_argument("--output", required=True)
    diagnostic_ops.add_parser("example", help="Create a separate explicitly authored fault/history fixture")
    ingest = diagnostic_ops.add_parser("append", help="Record one declared simulation envelope outside real-time control")
    ingest.add_argument("file")
    report = diagnostic_ops.add_parser("report")
    report.add_argument("--incident-id")
    report.add_argument("--example", action="store_true")
    support = diagnostic_ops.add_parser("export")
    support.add_argument("output")
    support.add_argument("--example", action="store_true")
    package = sub.add_parser("package", help="Bounded tar+Zstd archive; importing never runs a job or firmware")
    package_ops = package.add_subparsers(dest="package_operation", required=True)
    backup = package_ops.add_parser("backup")
    backup.add_argument("output")
    inspect = package_ops.add_parser("inspect")
    inspect.add_argument("file")
    job = package_ops.add_parser("job", help="Package explicitly selected job assets; no machine execution")
    job.add_argument("output")
    job.add_argument("--entry", action="append", required=True, help="Portable member=source-file; repeat for each asset")
    restore_package = package_ops.add_parser("restore-preview")
    restore_package.add_argument("file")
    restore_package.add_argument("--source", choices=("active", "draft"), default="active")
    restore_package.add_argument("--output", required=True)
    serve = sub.add_parser("serve", help="Open local-only setup workbench; no hardware transport")
    serve.add_argument("--port", type=int, default=8766)
    serve.add_argument("--provider-config", help="Explicit administrator-approved optional paid AI configuration JSON")
    assist = sub.add_parser("assist", help="Local grounded setup guidance; no paid calls")
    assist.add_argument("--question", default="What remains to complete setup?")
    sub.add_parser("ai-capabilities")
    advise = sub.add_parser("advise", help="Optional paid extraction into a proposal; never saves or controls equipment")
    advise.add_argument("--facts-file", required=True)
    advise.add_argument("--provider-config", required=True)
    advise.add_argument("--expected-revision", type=int, required=True)
    advise.add_argument("--allow-paid", action="store_true", help="Explicitly authorize one bounded request using the supplied approved configuration")
    settle = sub.add_parser("budget-settle", help="Trusted operator billing reconciliation; requires actual charged amount and evidence")
    settle.add_argument("request_id")
    settle.add_argument("--actual-microdollars", type=int, required=True)
    settle.add_argument("--evidence-id", required=True)


def dispatch(args):
    from .setup_service import SetupService
    from .setup_budget import BudgetLedger
    directory = Path(args.directory).resolve()
    service = SetupService(directory / "setup.json")
    op = args.setup_operation
    if op in ("diagnostics", "package"):
        from .diagnostic_cli import dispatch_diagnostics
        return dispatch_diagnostics(args)
    if op in ("readiness", "self-check"):
        from .setup_readiness import ReadinessService
        readiness = ReadinessService(directory)
        return readiness.status() if op == "readiness" else readiness.rehearse(args.expected_revision)
    if op == "intake":
        from .setup_assistant import local_intake
        from .diagnostic_cli import bounded_read
        return local_intake(service, bounded_read(args.facts_file, 48_000).decode("utf-8"), expected_revision=args.expected_revision)
    if op == "serve":
        from .setup_web import serve
        return serve(directory, args.port, provider_config=read_json(args.provider_config) if args.provider_config else None)
    if op == "init":
        value = service.initialize(actor="cli")
        ledger = BudgetLedger(directory / "budget.json")
        if not ledger.path.exists():
            ledger.create(value["epoch"], cap_microdollars=15_000_000)
        return value
    if op == "budget":
        return BudgetLedger(directory / "budget.json").status()
    if op == "budget-settle":
        return BudgetLedger(directory / "budget.json").settle(args.request_id,
            actual_microdollars=args.actual_microdollars, evidence_id=args.evidence_id)
    if op == "ai-capabilities":
        from .setup_ai import AiSetupAdvisor
        return AiSetupAdvisor.capabilities()
    if op == "advise":
        from .setup_ai import AiSetupAdvisor
        advisor = AiSetupAdvisor(service, BudgetLedger(directory / "budget.json"), directory / "advice-cache",
                                 read_json(args.provider_config))
        return advisor.advise(Path(args.facts_file).read_text(encoding="utf-8"),
                              expected_revision=args.expected_revision, allow_paid=args.allow_paid)
    if op in ("capabilities", "schema", "profiles", "status", "audit"):
        return getattr(service, op)()
    if op == "assist":
        from .setup_assistant import local_guidance
        return local_guidance(service, args.question)
    if op == "request-result":
        return service.request_result(args.request_id)
    if op == "restart-epoch":
        return service.restart_epoch(args.expected_revision, actor="cli")
    if op in ("template", "example"):
        value = service.draft_template(args.profile_id) if op == "template" else service.example_draft(args.profile_id)
    elif op == "save":
        return service.save_draft(read_json(args.file), args.expected_revision, actor="cli",
                                  expected_binding=read_json(args.expected_binding) if args.expected_binding else None)
    elif op == "preview":
        value = service.preview(read_json(args.file) if args.file else None)
    elif op == "commit":
        return service.commit(read_json(args.file), args.request_id, actor="cli")
    elif op == "restore-preview":
        value = service.restore_preview(args.generation)
    elif op == "export":
        value = service.status()
    else:
        raise ValueError("Unknown setup operation")
    if getattr(args, "output", None):
        export_json(args.output, value)
        return {"written": args.output, "simulation_only": True}
    return value
