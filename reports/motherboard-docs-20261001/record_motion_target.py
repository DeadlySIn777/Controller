from pathlib import Path
import hashlib,json,shutil
out=Path('reports/motherboard-docs-20261001/motion-target-2MHz-r01');out.mkdir(exist_ok=False)
files=[Path('docs/MOTION_EXPANSION_8_TO_12.md'),Path('docs/CURRENT_ACCEPTANCE_GATES.md')]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p)for p in files}
for p in files:shutil.copyfile(p,out/p.name)
motion='''**Additional user motion target, 1 October 2026:** qualify twelve simultaneously active STEP/DIR channels at up to 2 MHz per channel, independent per-channel STEP-high/low and DIR-setup/hold timing, polarity and maximum-rate profiles, atomic twelve-channel command updates in a deterministic 1 kHz LinuxCNC servo cycle, four ABZ encoder inputs in the base and qualified encoder expansion toward twelve that can coexist with all twelve motors. Each drive profile must clamp the commanded rate to its verified timing and electrical limits. This is a qualification target, not an implemented twelve-channel runtime, selected faster timing profile, electrical-rating increase or guarantee for every supported compute module. The one-motherboard architecture and all fitted interfaces remain unchanged.

The retained CNC3/IS-1 contract has separate 96-byte command and 176-byte feedback transactions. At the nominal 6.25 MHz host SPI ceiling, their 2,176 bits take 348.16 µs of ideal wire time; a 700 µs complete-exchange allocation leaves 351.84 µs theoretically for guards and software/transport overhead. This arithmetic does not prove loaded target latency or a 1 kHz real-time deadline. The legacy 50 MHz step generator requires `high + low + 1` ticks between STEP rises: merely raising MAX_RATE is invalid. An illustrative 12/12-tick profile gives a 25-tick period, with safe DDS increment at most `floor(2^32/25) = 171798691`; the ceiling increment can create a 24-tick interval and must be rejected. This example is analysis only. The existing historical default remains 195,312.5 pulses/s with six active channels. Qualification must cover all twelve pulse generators simultaneously, reversals, timing boundaries, atomic commit, encoder coexistence, watchdog/inhibit and actual output signal quality.

The earlier LinuxCNC 2.9.4 record reports that twelve- and sixteen-joint motion modules load and seventeen is rejected; it is a module-loading check, not a loaded machine, chosen kinematics, verified compute affinity or twelve-motor real-time proof. CPU affinity is module-specific commissioning work, not a guarantee. Exact attachment/source hashes and the unchanged historical record are archived in `reports/motherboard-docs-20261001/motion-target-2MHz-r01/receipt.json`.

'''
p=files[0];t=p.read_text();marker='## Historical eight-plus-four draft and review record';assert marker in t;t=t.replace(marker,motion+marker,1);p.write_text(t,encoding='utf8')
p=files[1];t=p.read_text();marker='Each gate needs exact input revision';assert marker in t
gates='''| G23 | Twelve simultaneous STEP/DIR channels at up to 2 MHz/channel with individually enforced STEP-high/low, DIR-setup/hold, polarity and maximum-rate profiles; atomic twelve-channel updates in a deterministic 1 kHz LinuxCNC servo cycle | Reviewed parameter/rate boundaries and protocol semantics; twelve-channel RTL simulation and vendor fit/timing; drive-specific electrical limits; loaded target transport/jitter tests; simultaneous physical pulse counts, reversal and fault/inhibit measurements | New user target, open. Historical six-channel 195,312.5 pulses/s evidence and analytical 25-tick timing do not qualify this target. No hardware rating or runtime limit is raised by recording it. |
| G24 | Four base ABZ encoder paths plus qualified expansion toward twelve ABZ channels, simultaneously with all twelve motor interfaces and preserved I/O/process functions | Exact expansion source/interface/resource and protected-supply limits; protocol freshness and configuration checks; vendor pin/resource fit; simultaneous loaded encoder/motor/IO timing and physical fault tests | Open expansion target. Four base receiving paths are represented in current source; source representation is distinct from four- or twelve-encoder runtime and physical qualification. No custom motor daughterboard is introduced. |

'''
t=t.replace(marker,gates+marker,1);p.write_text(t,encoding='utf8')
sources=[Path('C:/Users/Gluis/.codex/attachments/0e97ccf3-9250-4331-848f-bf6ef92e6dcf/Pasted text.txt'),Path('gateware/PROTOCOL.md'),Path('reports/audit-2026-09-30/CNC3_BRANCH_CHECKS/inputs/docs/interface-spec/01-protocol-and-schedule.md')]
receipt=dict(scope='Two motion/gates planning documents only; no electrical source/RTL/runtime changes',before=before,after={str(p):sha(p)for p in files},inputs={str(p):sha(p)for p in sources},new_runtime_implemented=False,new_electrical_ratings_qualified=False,physical_2MHz_qualified=False,all_historical_motion_text_preserved=True)
assert motion in files[0].read_text();assert files[0].read_text().replace(motion,'')==(out/files[0].name).read_text()
assert files[1].read_text().replace(gates,'')==(out/files[1].name).read_text()
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
