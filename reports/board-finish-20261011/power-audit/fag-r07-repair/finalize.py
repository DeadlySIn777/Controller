"""Freeze small source/host receipt for staged experimental return repair."""
import json
import hashlib
from pathlib import Path
from datetime import datetime,timezone
import construct as C
P=C.P
HERE=Path(__file__).resolve().parent

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
 report=HERE/'REPORT.txt';manifest=HERE/'manifest.json'
 if report.exists() or manifest.exists():raise ValueError('separate immutable final receipt required')
 packet=json.loads(C.AUDIT.read_bytes());construction=json.loads((HERE/'staged/construction.json').read_bytes())
 for receipt in(packet,construction):
  for path,expected in receipt['source_files_sha256'].items():
   if sha(Path(path).read_bytes())!=expected:raise ValueError('source differs:'+path)
 original=P.R.composition.inventory(P.I.DONOR.read_bytes());flags=[]
 for uid,h in packet['retained250_chunks_sha256'].items():
  ch=original[4][uid]
  if P.R.composition.pcbtext.chunk_kind(ch)!='via':continue
  if sha(ch)!=h or b'(layers "F.Cu" "B.Cu")' not in ch:raise ValueError('via layer flag identity differs')
  if any(term in ch for term in(b'remove_unused_layers',b'keep_end_layers',b'start_end_only',b'zone_layer_connections',b'padstack',b'via blind',b'via micro')):
   raise ValueError('retained donor annulus source default unsupported')
  flags.append({'uuid':uid,'chunk_sha256':h,'native_chunk':ch.decode(),
                'ordinary_through_endpoints':['F.Cu','B.Cu'],'unused_annulus_removal_flags_present':False,
                'source_mode':'ordinary KEEP_ALL default; no suppression override',
                'final_native_flash_gate':'OPEN: verify exact combined candidate actual annuli before acceptance'})
 if len(flags)!=4:raise ValueError('retained via count differs')
 flagreceipt={'schema':'fag-retained-donor-layer-source-flags-v1','verdict':'PASS_SOURCE_FLAGS_NATIVE_FINAL_OPEN',
              'native_donor_sha256':packet['donor_sha256'],'whole_group_audit_sha256':C.AUDIT_SHA,'rows':flags,
              'official_KiCad_10_0_4_sources':[
                {'url':'https://gitlab.com/kicad/code/kicad/-/raw/10.0.4/pcbnew/padstack.cpp',
                 'fact':'PADSTACK constructor initializes unconnected-layer mode to KEEP_ALL'},
                {'url':'https://gitlab.com/kicad/code/kicad/-/raw/10.0.4/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp',
                 'fact':'via parser changes removal mode only upon explicit remove_unused_layers or start_end_only tokens'}],
              'evidence_class':'exact retained source flags and official implementation inspection, no new native API flash measurement'}
 (HERE/'retained-via-source-flags.json').write_text(json.dumps(flagreceipt,indent=1)+'\n',encoding='utf-8')
 unique_pairs={(r['item_uuid'],r['hole_uuid']) for r in packet['inherited_same_net_provenance']}
 testreceipt={'schema':'fag-r07-host-controls-v1','tests':13,'subtest_executions':7,'failures':0,'errors':0,'skips':0,
              'exit_code':0,'reported_unittest_seconds':5.438,
              'test_code_sha256':sha((HERE/'test_controls.py').read_bytes()),
              'constructor_sha256':sha((HERE/'construct.py').read_bytes()),'whole_group_audit_sha256':C.AUDIT_SHA,
              'evidence_class':'host unit rejection controls and source reconstruction only',
              'native_jobs':0,'gpu_jobs':0,'recorded_utc':datetime.now(timezone.utc).isoformat()}
 (HERE/'host-controls-receipt.json').write_text(json.dumps(testreceipt,indent=1)+'\n',encoding='utf-8')
 text=f'''Partial FIELD_A return repair on actual r07 and frozen four-path branch

PASS source/host only; fresh combined native measurement is OPEN.
Combined source SHA {construction['combined_sha256']}
Donor-on-r07 source SHA {construction['donor_sha256']}
Construction SHA {sha((HERE/'staged/construction.json').read_bytes())}
Whole-group r3 audit SHA {C.AUDIT_SHA}

Scope is the original partial 0.096 A FIELD_A return, exact native net
/motherboard_motors{{slash}}FIELD_GND. Full field load, source anchoring,
sharing, thermal, fault and transient proof remain OPEN. No live adoption,
GPU/native jobs, filled-board save or manufacturing-ready claim.

Preserves every actual r07 native item and all18 frozen four-path additions.
Only11 original donor-owned blockers are omitted:4vias and7tracks. The other
250 donor chunks are byte-exact. Final donor269items=264segments/5vias:
246 retained segments/4 retainedvias plus18replacementsegments/1newvia.
Four close vias are replaced using two exact old FIELD_GND .6/.3 vias:
48bb17dc-e15c-4500-87b2-9784faa6bd96 at353.45,202.4 and
cdb3618a-92a8-464f-b748-d76db21e7598 at381.85,186.5.
353.3 retained .8mm stub already physically overlaps48bb;381.4 sites have
two .8mm In3 ties. No existing .5/.2via is assumed to carry this return.

Seven blocked segments form4connected owned networks. Three have bounded
.3mm In3 detours. The lower fault network's two anchors are in distinct
continuous free-space components at8/10/12mm window growth. A single dive
and return solves it in the original8mm window:358.8,203 onIn3 to one new
.6/.3 throughvia at357.05,201.25; .3mm F.Cu detour to existing48bb; retained
In3 stub reaches353.3,203.2. One new via, one old via, three layer segments.
The new connector's penultimate vertex was moved from353.4,201.9 to
353.4,201.8 to obey the unrelated portion's stricthole envelope; no masks
or native items changed.

Strict newly generated copper passes .25mm hole, .6mm cross-domain,
.15mm same-domain clearance plus.025mm margin; every new via obeys .8mm
ordinary spacing and conservative all-layer holes/foreign fills/barriers/
reservations. Retained r06 foreign fills are conservative obstacles, not
a claim of fresh r07 storage or source-root equivalence.

28 inherited same-net hole observations are {len(unique_pairs)} unique unchanged pairs,
across8 retained donor items. They remain visible in the audit. Acceptance
of those OLD geometry pairs is bound to exact donor a10803..., raw native
DRC0, identical original hole/footprint/copper chunks and original project/
rules; it cannot extend to any new copper, foreign hole, domain clearance
or via-spacing exception. Physical contact versus old proximity remains
visible via item geometry, not a universal same-net-hole waiver.

Layer-specific physical graph preserves1477surviving keys across313prior
components,0lost relationships,3989old/3982new nodes. No fill contacts are
included. Exact native FlashLayer evidence is bound for478 unchanged FIELD
vias:467all6,10F/In1/In4,1In1/In4. Suppressed annuli are excluded from the
graph; the clearance overlay conservatively retains extra annuli. Four
retained donor vias are ordinary KEEP_ALL-default source flags, pinned in
retained-via-source-flags.json; final actual native flash remains OPEN.

First repair plan and r1wholeaudit are preserved WITHHELD. Observed r2
continuity result is preserved but superseded because its overlay had
projected unused native annuli. Only r3 closure is used by construction.
13hostcontrols plus7subtest executions passed,0failures/errors/skips.
Independent proof_audit reviewed the final graph, inherited pair bounds,
native flashed filter and retained donor source flags with no blocker.

Four-path target SHA {construction['four_path_sha256']},18 additions unchanged.
Minimum shared-layer FIELD-to-four owned copper gap {construction['minimum_owned_to_four_path_shared_layer_gap_mm']:.6f}mm;
all new FIELD via footprints were checked against all6original foreign
fill/copper layers. Fresh prospective reference/return masks and actual
combined pad partition/DRC/fill/source-root proof remain native gates.
Use original frozen source hierarchy for this actualr07 branch; no silent
C11061-corrected c05/source-library-v2 substitution. API net/pad matching
does not imply schematic editor reload or complete value/BOM matching.

Next authorized action is root-reviewed fresh combined native measurement,
strict actualr07 lost0/API guard and DRC0. Report r06 regressions separately.
Neither old r06+3/-0 nor the parent two-path+2/-0 proves this combination.
'''
 report.write_text(text,encoding='utf-8')
 members={str(p.relative_to(HERE)).replace('\\','/'):sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest}
 manifest.write_text(json.dumps({'schema':'fag-r07-repair-frozen-host-source-v1','files':members,
                               'qualified_native':False,'adopted':False,'manufacturing_ready':False},indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'files':len(members),'report_sha256':sha(report.read_bytes()),'manifest_sha256':sha(manifest.read_bytes()),
                   'source_flags_sha256':sha((HERE/'retained-via-source-flags.json').read_bytes()),'unique_inherited_pairs':len(unique_pairs)},indent=1))

if __name__=='__main__':main()
