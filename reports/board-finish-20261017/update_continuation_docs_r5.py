"""Small backed-up factual continuation update; exact byte replacements only."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 backup=H/'project-docs-before-r5';assert not backup.exists();backup.mkdir()
 docs=[ROOT/'PROJECT_MEMORY.md',ROOT/'reports/ENGINEERING_STATUS.md',H/'README.md']
 before={str(p):sha(p) for p in docs}
 for p in docs:(backup/p.name).write_bytes(p.read_bytes())
 def change(p,old,new):
  b=p.read_bytes();x=old.encode();y=new.encode();assert b.count(x)==1,(p,old[:100]);p.write_bytes(b.replace(x,y))
 change(docs[0],
  'Global area2 mapping, a separate transport correction and complete physical-wrapper fit/timing remain open.',
  'Full-core area2 plus a verified transport alignment correction now maps at 18,107 LUTs + 2,107 ADD (20,214 total; still 486 above the coarse T20 screen), with all completed protocol buffers retained. Transport differential and unchanged full-runtime checks pass. The corrected baseline cached native DRC also completes at zero ordinary errors / 332 warnings / zero parity issues with all 220 launch inputs unchanged; the exact duplicate-hole warning is removed and 1,172 required joins remain. Complete physical-wrapper fit/timing and the current composed full native refill remain open.')
 change(docs[1],
  'Global area2 mapping and an isolated transport correction are next; complete physical-wrapper fit/timing remains open.',
  'Full-core area2 plus the verified transport alignment correction now maps at 18,107 LUTs + 2,107 ADD (20,214 total; still 486 above the coarse T20 screen). Transport differential and unchanged full-runtime checks pass, with completed protocol buffers retained. Corrected-baseline cached native DRC completes at zero ordinary errors / 332 warnings / zero parity issues and all 220 launch inputs unchanged; the duplicate-hole warning is removed and 1,172 required joins remain. The composed full native refill and complete physical-wrapper fit/timing remain open.')
 change(docs[2],
  'Cached native DRC/parity is running.',
  'Cached native DRC/parity has completed: zero ordinary errors, 332 retained warnings, zero schematic parity issues and zero ignored checks. The independent review binds all 220 unchanged launch inputs. One co-located-hole warning is removed by the exact duplicate-via retirement; two unchanged tracks receive different retained native via witnesses. The CLI emits 499 unconnected diagnostic rows, distinct from the unchanged uncapped 1,172 pad-island joins / 1,183 API items. No new refill was called. `corrected-baseline-cached-drc-review-r1/receipt.json` preserves this scope and the earlier one 84% CPU sample.')
 change(docs[2],
  'Events-only area/area2 settings do not establish global fit; a single full-core area2 measurement and an isolated transport-alignment correction are the next checks. Canonical gateware and all fitted functions/limits remain unchanged.',
  'Full-core area2 with these exact sources measures 19,919 LUT4 + 2,107 ADD, 11,047 FF and 64 RAM5K. The additional isolated transport alignment correction preserves 1,408-bit RX/completed buffers and 1,392-bit TX snapshot storage while directly collecting CMD in its final slice. Its actual-SPI differential passes 1,098,329 cycles / 80 transactions, independent valid CRC/rate-word checks, malformed/truncated/overlap/reset cases, 180,000 binary and 3,000 X/Z fuzz cycles. The unchanged full SIM2 suite also passes. Native full-core area2 with all three overlays measures 18,107 LUT4 + 2,107 ADD (20,214 total), 11,037 FF, 64 RAM5K and one multiplier, still 486 above the coarse T20 screen. Peak sampled CPU is 44.2%. See `release-review/transport-cmd-alignment-r1/reviewable-transport-overlay-packet.json` and immutable native resource supplement. Canonical gateware and all fitted functions/limits remain unchanged; physical wrapper, place/route and timing remain open.')
 result={'status':'EXACT_BYTE_DOCUMENTATION_UPDATE_WITH_BACKUPS','before_SHA256':before,'after_SHA256':{str(p):sha(p) for p in docs},'script_SHA256':sha(Path(__file__)),'no_design_source_modified':True}
 (H/'project-docs-update-r5.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
