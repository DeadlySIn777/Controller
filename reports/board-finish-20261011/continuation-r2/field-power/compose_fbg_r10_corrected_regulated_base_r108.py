"""Bind the exact zone UUID rather than R10's existing landing-via UUID."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
f=p/'corrected-regulated-fbg-r10-search-base-r107'
if not (f/'receipt.json').exists():(f/'receipt.json').write_text(json.dumps({'verdict':'FAIL_ZONE_UUID_ASSERTION_CONFLATED_WITH_LANDING_VIA_ID','asserted_zone_uuid':'df0142e5-1eec-5c16-a3af-fd791397b3d9','actual_exact_zone_uuid':'d480dd23-09f4-5c53-bc5b-0bee7c7536ff','projected_model_emitted':False,'board_written':False,'native_jobs':0},indent=1)+'\n',encoding='utf-8')
s=(p/'compose_fbg_r10_corrected_regulated_base_r107.py').read_text().replace('corrected-regulated-fbg-r10-search-base-r107','corrected-regulated-fbg-r10-search-base-r108').replace("peer[0]['uuid']=='df0142e5-1eec-5c16-a3af-fd791397b3d9'","peer[0]['uuid']=='d480dd23-09f4-5c53-bc5b-0bee7c7536ff'").replace("print('R107","print('R108")
exec(compile(s,str(p/'compose_fbg_r10_corrected_regulated_base_r107.py'),'exec'))
