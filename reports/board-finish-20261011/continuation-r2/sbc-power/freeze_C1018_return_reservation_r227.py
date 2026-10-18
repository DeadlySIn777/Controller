"""Third exact power/reference reservation, with full halo attribution."""
import hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
original=P/'freeze_C1021_C1023_return_reservations_r224.py'
s=original.read_text()
s=s.replace('C1021-C1023-source-ground-return-reservations-r224','C1018-source-ground-return-reservation-r227')
s=s.replace("for ref in ('C1021','C1023'):","for ref in ('C1018',):")
s=s.replace("assert owned['foreign_owned_physical_plane_attribution'][0]['owned_foreign_UUID']=='f4863c44-a057-598a-aef7-adca7cfb15f1'","full=H/'sbc-power/three-IO3-full-return-obstacle-diagnosis-r226/receipt.json';assert sha(full)=='c4966b21b3f8bf41681333e7a26f878e19119973536ebafd5a75eb279f7d7bcd';attr=next(q for q in json.loads(full.read_text())['rows']if q['ref']=='C1018');assert any(q['UUID']=='f4863c44-a057-598a-aef7-adca7cfb15f1'and q['kind']=='owned_foreign_plane_full_guard'for q in attr['full_guard_attribution'])")
s=s.replace('EXACT_TWO_UNACCEPTED_IO3_REFERENCE','EXACT_THIRD_UNACCEPTED_IO3_REFERENCE').replace('R224_COMPLETE','R227_COMPLETE')
assert s!=original.read_text()
exec(compile(s,str(__file__),'exec'))
