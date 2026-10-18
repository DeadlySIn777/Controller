"""Add explicit per-feature evidence boundaries to the preserved proposal trace."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE/'requirements-feature-trace.json').read_text(encoding='utf-8-sig'))
related = {
 'F001': ('reports/CONFIGURATION_DEMO.md', 'Virtual profiles generate illustrative wiring; exact physical component catalogue and wire checks absent.'),
 'F003': ('reports/CONFIGURATION_DEMO.md', 'Virtual drive/electrical profile validation exists; physical drive setup translator not qualified.'),
 'F004': ('reports/CNC1_INTEGRATION.md', 'Explicit simulation homing/motion exists; guided first-motion UI and novice acceptance absent.'),
 'F022': ('reports/CNC1_INTEGRATION.md', 'Actual LinuxCNC executes through simulated six/two RTL; complete registered job/geometry simulation absent.'),
 'F029': ('reports/PERSISTENT_RUNTIME.md', 'Stopped XYZ scale changes invalidate home; complete setup-object dependency invalidation absent.'),
 'F031': ('reports/CNC1_INTEGRATION.md', 'Local actual LinuxCNC jobs work in the disconnected simulation environment; fitted target physical execution absent.'),
 'F032': ('reports/CNC1_INTEGRATION.md', 'CRC/session/fault/rearm and duplicate-command behavior tested for historical six/two; expanded physical product unqualified.'),
 'F034': ('reports/PERSISTENT_RUNTIME.md', 'Persistent scale recovery refuses invalid authority and does not restore live home/job authority; full power-loss assessment UI/physical storage absent.'),
 'F039': ('reports/CONFIGURATION_DEMO.md', 'Configuration transactions/restore are related foundations; firmware/Linux transactional update and rollback feature absent.'),
 'F040': ('reports/ESP_SERVICE_BUILD.md', 'Target-compiled diagnostic firmware exists; independent rescue/provisioning/reset authority absent.'),
 'F043': ('reports/CNC1_INTEGRATION.md', 'Returned counters/feedback are tested; requested commanded-versus-measured visual dashboard absent.'),
 'F059': ('reports/MODULE_REPLACEMENT_DEMO.md', 'Authored virtual inventory and identity/compatibility recovery exist; live physical discovery absent. Unmerged IS-1 adds a specification.'),
 'F098': ('docs/CURRENT_ACCEPTANCE_GATES.md', 'Timing studies and explicit target gates exist; built-in measured physical real-time qualification feature absent.'),
 'F100': ('reports/RECOVERY_CLI.md', 'Host file-backed cartridge/export/replacement prototype exists; complete physical machine backup and production mirror authority absent.'),
 'F132': ('reports/ENCODER_POWER.md', 'Encoder supply limiters and entry protection are related circuit work; individually protected general-output feature and acquisition absent.'),
 'F195': ('reports/RUNTIME_CONFIGURATION.md', 'Bounded stopped XYZ configuration experiment path is implemented in simulation; broad controlled machine experiments absent.'),
 'F197': ('reports/audit-2026-09-30/check-results.json', 'Source/netlist/host regressions run reproducibly; automated physical regression fixtures and acceptance absent.'),
 'F199': ('docs/CURRENT_ACCEPTANCE_GATES.md', 'IS-1 module and service contracts are design input; expansion-module SDK/qualified developer kit absent.'),
 'F200': ('reports/CNC1_INTEGRATION.md', 'Six/two capability discovery and unmerged CNC3 host/model are related foundations; capability-bound job exchange absent.'),
}
output = []
for row in rows:
    evidence, boundary = related.get(row['id'], (None, 'No implementation acceptance evidence for this complete feature was found in the audited main checkout and separate IS-1 worktree. Retained proposal/specification is design input.'))
    output.append({'id':row['id'], 'title':row['title'], 'source_path':row['source_path'], 'source_line':row['source_line'],
                   'proposal_preserved':True, 'end_to_end_accepted':False, 'installed_capability_claim':False,
                   'audit_state':'related_foundation_only' if evidence else 'proposal_without_implementation_acceptance',
                   'related_evidence':evidence, 'boundary':boundary})
assert len(output)==200 and len({r['id'] for r in output})==200
(HERE/'feature-implementation-map.json').write_text(json.dumps({'schema_version':1, 'scope':'Per-feature complete-capability acceptance; related foundation is explicitly not full feature completion',
    'review_date':'2026-09-30', 'features':output},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'features':200, 'related_foundations':len(related), 'complete_feature_acceptance_claims':0}))
