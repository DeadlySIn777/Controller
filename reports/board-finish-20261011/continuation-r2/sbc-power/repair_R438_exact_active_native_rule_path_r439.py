"""Retain R438 missing stage-rule path; bind native-read R312 copy rules."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'freeze_exact_CDONE_incremental_reservation_decision_r438.py').read_text(encoding='utf-8')
s=s.replace('CM79-CDONE-exact-owned-subset-incremental-helper-grandfathering-r438','CM79-CDONE-exact-owned-subset-incremental-helper-grandfathering-r439')
s=s.replace("board=Path(context['active_board']);dr=board.with_suffix('.kicad_dru');decision=","board=Path(context['active_board']);nr=json.loads((H/'current-R753-all-native-zone-intents-read-only-r312/receipt.json').read_bytes());dr=next(Path(p)for p in nr['input_SHA256']if p.endswith('board.kicad_dru'));assert sha(dr)==nr['input_SHA256'][str(dr)]=='ac9e9580a65765b5d77ca2d4a1594e6bdc088fe26cfc01cd9027a4e9f29c676c';decision=")
s=s.replace("'original_native_active_DRU_SHA256':sha(dr)","'original_native_active_DRU_path':str(dr.resolve()),'original_native_active_DRU_SHA256':sha(dr),'retained_R438_failure':'Stage PCB has no companion DRU; actual native R312 loaded exact R299 copy board.kicad_dru; native rules binding repaired only'")
s=s.replace("print('R438_COMPLETE'","print('R439_COMPLETE'")
E=P/'exact-expanded-CDONE-reservation-grandfathering-r439.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
