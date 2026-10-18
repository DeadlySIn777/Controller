from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motherboard-docs-20261001/source26-root62-sync-r01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def main():
 OUT.mkdir()
 adopted=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/adoption.json'
 board=adopted.parent/'motherboard-source26-WIP.kicad_pcb'
 proof=ROOT/'reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/independent-connectivity/review.json'
 a,c=read(adopted),read(proof)
 assert a['adopted'] and a['passed'] and a['board_sha256']==sha(board)==c['board_sha256']
 assert (a['track_via_count'],a['zone_count'],a['missing_joins'],a['native_errors'],a['native_warnings'],a['orphan_copper_count'])==(10506,1507,3811,0,12,0)
 assert c['source_net_checks_pass'] and c['complete_source_population_pass'] and not c['errors'] and not c['orphan_copper_items']
 old='The current **working native PCB candidate r50**, separate from the published viewer, has **2,688 footprints, 9,498 fitted pads, 8,927 track/via items and 197 zones**. Its exact source and independent physical connectivity checks pass, with **609 fully joined and 1,125 incomplete multi-pad nets out of 1,734**, **4,435 uncapped missing joins** and zero orphan copper. Native DRC reports **zero errors, 22 IO3 feed-via warnings and two FIELD_B return-track warnings, all unsuppressed with no ignored checks**.'
 new='The current **adopted working PCB r62**, separate from the published viewer, has **2,688 footprints, 9,498 fitted pads, 10,506 track/via items and 1,507 zones**. Its exact source and independent physical connectivity checks pass, with **609 fully joined and 1,125 incomplete multi-pad nets out of 1,734**, **3,811 uncapped missing joins**, agreement between native and independent SOURCE-connected cluster counts, and zero orphan copper. Native DRC reports **zero errors, ten isolated-fill warnings and two FIELD_B return-track warnings, all unsuppressed with no ignored checks**. Combined proof preserves **93 actual owned-bypass loops, 191 receiving-return endpoint checks and 43 physically SOURCE-anchored reference-bridge groups**. These are scoped local proofs; global power and reference qualification remain incomplete.'
 files=['PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md']
 before,after={},{}
 for f in files:
  p=ROOT/f;before[f]=sha(p);text=p.read_text(encoding='utf8');assert text.count(old)==1
  copy=OUT/'before'/f;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes())
  original_lines=text.splitlines(keepends=True)
  text=text.replace(old,new).replace('source26/r50 candidate','source26/r62 working PCB')
  text=text.replace('motherboard-pcb-integration-20261001/source26-ao-display-r50/receipt.json','motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/adoption.json')
  text=text.replace('motherboard-pcb-integration-20261001/source26-ao-display-r50/independent-connectivity/review.json','motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/independent-connectivity/review.json')
  # Restrict this synchronisation to the existing current top paragraphs.
  latest_lines=text.splitlines(keepends=True)
  assert len(latest_lines)==len(original_lines)
  assert all(x==y for x,y in zip(original_lines[18:],latest_lines[18:]))
  p.write_text(text,encoding='utf8',newline='');after[f]=sha(p)
 receipt=dict(passed=True,scope='Four existing current paragraphs; historical content after line18 unchanged',before_hashes=before,after_hashes=after,
  evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in [adopted,board,proof,ROOT/'hardware/motherboard/design.json',ROOT/'hardware/motherboard/netlist.xml']},
  working_board='r62',published_viewer='20260930-24',source26_unchanged=True,source_or_PCB_mutated=False,manufacturing_ready=False)
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt))
if __name__=='__main__':main()
