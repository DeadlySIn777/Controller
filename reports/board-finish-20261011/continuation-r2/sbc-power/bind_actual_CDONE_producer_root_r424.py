"""Repair the transcribed source hash; preserve R423's failed guard."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
(P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r423/failure.json').write_text(json.dumps({'status':'PRE_BINDING_SOURCE_HASH_TRANSCRIPTION_GUARD_FAILURE','incorrect_asserted_hash':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b7b','actual_previous_source_hash_verified':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','repair':'R424','source_or_native_edits':0},indent=1)+'\n',encoding='utf-8')
s=(P/'bind_actual_CDONE_producer_root_r423.py').read_text(encoding='utf-8').replace('070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b7b','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2').replace('CM79-CDONE-fresh-producer-and-actual-native-group-binding-r423','CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424').replace('R423_COMPLETE','R424_COMPLETE')
E=P/'exact-expanded-CDONE-producer-binding-r424.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
