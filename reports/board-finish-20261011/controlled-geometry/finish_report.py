"""Freeze final source-only geometry proposal/report and exact output identities."""
from pathlib import Path
import json
import plan_geometry as p

H=Path(__file__).resolve().parent

def main():
    records=p.read_inputs();g=json.loads((H/"geometry.json").read_text())
    native=json.loads((H/"native-check-r3/receipt.json").read_text())
    tests=json.loads((H/"host-receipt.json").read_text());nt=json.loads((H/"native-host-receipt.json").read_text())
    if native["verdict"]!="PASS_NATIVE_EFFECTIVE_CLASSES_ONLY" or tests["verdict"]!="PASS" or nt["verdict"]!="PASS":raise ValueError("required result incomplete")
    rows=[]
    for cls,r in g["F.Cu"].items():
        worst=max(abs(c[z]/r["target_ohm"]-1)*100 for c in r["corners"] for z in ("A_ohm","B_ohm"))
        rows.append(f'{cls:10} {r["w_mm"]:.3f}  {r["s_mm"] if r["s_mm"] is not None else "-":>5}  {r["nominal"]["A_ohm"]:6.2f}  {r["nominal"]["B_ohm"]:6.2f}  {worst:5.2f}%')
    inner=[]
    for cls,r in g["In3.Cu"].items():
        if "field_nominal_refined" not in r:
            inner.append(f'{cls}: HELD; B separated-pair upper bound {r["B_separated_pair_upper_bound_ohm"]:.2f} ohm, below108 ohm lower120 tolerance limit.');continue
        inner.append(f'{cls}: w{r["w_mm"]:.3f}, gap{r["s_mm"] if r["s_mm"] is not None else "-"}; B{r["nominal"]["B_ohm"]:.2f}, C refined{r["field_nominal_refined"]["C_ohm"]:.2f} ohm; two-mesh maximum shift{r["mesh_convergence"]["two_mesh_max_change_pct"]:.3f}%. HELD_REFERENCE_RETURN.')
    report="""ROOT106 exact c05 provisional controlled-geometry proposal

SCOPE: isolated source/model/settings proposal only; not installed, not routing/SI/fabrication qualified.
The original live r07/r08, exact c05 proof sources, current measurement inputs and experimental bundle were not changed.

Exact original c05 board: 95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d.
Original project:82bbd7114aa2e6f2d200252cfde3f69d2a1f3905212e6b14437e62ff742d780b.
Original rules:159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4.

Actual stackup is35um copper on ALL six layers, dielectric0.22/0.33/0.22/0.33/0.22mm,
Dk4.45/4.6/4.45/4.6/4.45. Copper plus dielectric1.53mm, masks included1.55mm;
general nominal thickness1.60mm. The0.05mm mismatch is pending fabricator resolution.
Old ROOT104 outer70um geometries were not reused. Unknown mask Dk, frequency dependence,
roughness, process tolerances, real neighboring copper and continuous reference returns remain open.

Conditional outer F.Cu/B.Cu geometry in mm, impedances in ohm:
class      width   gap       A       B     worst A/B band deviation
"""+"\n".join(rows)+"""
Nominal A/B agreement is <=5%; both valid formula models and all +/-0.010mm width/gap
corners lie inside +/-10% target. Width/gap grid0.005mm, width minimum0.20mm, gap minimum0.15mm.
These are mathematical exploratory bands, not guaranteed fabricator tolerances.

In3 geometry mathematics:
"""+"\n".join(inner)+"""
IPC stripline range guard rejects every legal >=0.20mm In3 width; matching extrapolated
IPC numbers are not accepted as a second valid method. B uses the mixed-offset
Cohn/Wheeler approximation; C is an independent rectangular-conductor finite-volume
Laplace solver, one numerical thread, max96096 nodes, two nominal/corner meshes.
The finite-box/model limitations remain even with sub0.1% mesh changes.

ALL CONTROLLED In3 ROUTING IS HELD: current In2 source zone polygons contain ONLY /IO_3V3;
In4 contains separate logic/analog/comms/field domain returns. These are polygon inventories,
not filled continuity proof. The assumed two equipotential reference planes are not established
for any candidate net, particularly AO1_DAC_SCLK on DOM_AO1. Future planner controlled layers
are only F.Cu/B.Cu, still conditional on continuous own-domain reference and return proof.
In1/In2/In4 controlled routing is not modelled or enabled by this proposal.

Policy correspondence:204 historical target nets match current native-matched pad nets uniquely:
100IMP_50,96DIFF_100,6DIFF_90,2DIFF_120. Exact current {slash}/slash spelling is preserved.
All reciprocal differential partners and one existing domain membership per selected net checked.
Historical ROOT104 route lengths, reference samples, timing, rise/load estimates and settling
conclusions remain historical. Current electrical-length/edge/bus/return audit is required.
AO1_DAC_SCLK has current real U14623.15 ISO7761FDWR -> U14626.6 AD5683RBRMZ-3 net correspondence;
this is not proof of present length, SCLK timing or load/current/return behavior.

future-copy-proposal contains reviewable .kicad_pro.proposed and .kicad_dru.proposed files;
there is no automatic installer. Original28 class objects, domain/exact net patterns, other project
settings, copper and original rule byte prefix are preserved. Four new classes supply geometry
plus explicit preserved0.15mm clearance, with priority-2; vias/other properties inherit original values.
Only204 exact list-valued label assignments are extended. Original .6mm cross-domain rules
remain untouched. Appended rules supply outer min/opt/max width and recognized coupled gap;
literal original U1001 narrow-neck eligibility is excluded exactly, not enlarged.
There is no new skew/uncoupled-length/current/reference proof or controlled In3 geometry rule.

Native actual settings check: PASS_NATIVE_EFFECTIVE_CLASSES_ONLY, KiCad10.0.4,
existing shared heavy.sh slot,94.677seconds; LoadBoard original and isolated proposal copies only.
All2385 named effective nets checked;204 selected geometries correct; all28 original declared
classes and all unselected effective classes unchanged.32 total proposal classes. All selected
effective clearance/via values and every observed global minimum are preserved; aggregate
smallest clearance remains150000nm. Both complete input directories remained byte-exact.
No refill, Save, DRC, router interaction or GUI. Custom-rule full parse/condition enforcement
is UNCONFIRMED (not exposed through SWIG; native rule-init has a silent-catch limitation).

Important preserved failed attempts: native-check-r1 records the opaque SWIG constituent-vector
diagnostic and unchanged directories. native-check-r2 retains the initial unset-clearance proposal,
exact producer scripts, observed report and immutable board/project/rules identities. Its real
aggregate smallest clearance was-1nm while all204 individual effective clearances remained150000nm.
This was FAIL, not relabelled PASS. The final explicit0.15mm classes correct that issue.

Validation:12 host preservation/rejection controls PASS,20 frozen calculator closed-form controls
PASS (11 field tests deliberately deselected),7 native-report replay/rejection controls PASS.
All scoped original input hashes remain unchanged. See primary-provenance.json for primary
formula/CM5/KiCad references and the limits of accessible original-paper text.

Open before any migration: fabricator-confirmed finished stackup/process; current net-policy
qualification; actual own-domain reference/return and adjacent copper; native custom-rule/router
behavior; fresh DRC and connection-preservation gate under changed settings/copper; extracted SI,
length/skew/termination/bus timing, current/power/thermal/fault and physical measurement.
Applying a proposal would require separate evidence for existing copper; current c05 proof does
not qualify proposed settings. Current c05 itself remains an experimental branch, +20/-0 vsr06,
and +21/-13 vs live r07/r08; direct live adoption remains withheld and manufacturing is open.
"""
    for old,new in {
        "stackup is35um":"stackup is 35 um", "dielectric0.22":"dielectric 0.22",
        "mm,\nDk4.45":"mm,\nDk 4.45", "dielectric1.53mm":"dielectric 1.53 mm",
        "included1.55mm":"included 1.55 mm", "thickness1.60mm":"thickness 1.60 mm",
        "The0.05mm":"The 0.05 mm", "outer70um":"outer 70 um",
        "grid0.005mm":"grid 0.005 mm", "minimum0.20mm":"minimum 0.20 mm",
        "minimum0.15mm":"minimum 0.15 mm", "below108 ohm lower120":"below 108 ohm lower 120",
        "max96096 nodes":"max 96,096 nodes", "sub0.1%":"sub 0.1%",
        "correspondence:204":"correspondence: 204", "100IMP_50,96DIFF_100,6DIFF_90,2DIFF_120":"100 IMP_50, 96 DIFF_100, 6 DIFF_90, 2 DIFF_120",
        "Original28 class":"Original 28 class", "preserved0.15mm":"preserved 0.15 mm",
        "priority-2":"priority -2", "Only204":"Only 204", "Original .6mm":"Original 0.6 mm",
        "KiCad10.0.4":"KiCad 10.0.4", "slot,94.677seconds":"slot, 94.677 seconds",
        "All2385":"All 2,385", ";204":"; 204", "all28":"all 28", "unchanged.32":"unchanged. 32",
        "remains150000nm":"remains 150,000 nm", "was-1nm":"was -1 nm", "all204":"all 204",
        "remained150000nm":"remained 150,000 nm", "explicit0.15mm":"explicit 0.15 mm",
        "Validation:12":"Validation: 12", "PASS,20":"PASS, 20", "PASS,7":"PASS, 7",
        "vsr06":"vs r06", "shift0.":"shift 0.",
    }.items(): report=report.replace(old,new)
    (H/"REPORT.txt").write_text(report,encoding="utf-8")
    files={}
    for path in H.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.name!="manifest.json":
            files[path.relative_to(H).as_posix()]={"sha256":p.sha(path.read_bytes()),"bytes":path.stat().st_size}
    p.write(H/"manifest.json",{"scope":"isolated provisional controlled geometry proposal; final native class observation only","installed":False,"board_sha256":records["board"]["sha256"],"files":files})
    print(json.dumps({"verdict":"FROZEN_PROVISIONAL_PROPOSAL", "files":len(files),"manifest_sha256":p.sha((H/"manifest.json").read_bytes()),"report_sha256":p.sha((H/"REPORT.txt").read_bytes())}))

if __name__=="__main__":main()
