"""Read completed actual R299 CPP partitions: all CM grounds still isolated."""
import sys,json,time,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
OUT=P/'CM51-actual-current-R299-full-native-CPP-J1-source-necessity-r462'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();native=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full';rf=native/'receipt.json';receipt=json.loads(rf.read_bytes());part=native/'partitions.json';data=json.loads(part.read_bytes());assert receipt['candidate_SHA256']==data['sha256']=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2';assert sha(part)==receipt['partitions_SHA256']=='05df2c56837de04e3c57ad1af6081d0e87faec27cd42d0b001871538c762c136';assert data['refilled']and receipt['full_native_CPP_Fill_calls']==1 and not receipt['discrete_Cu_errors']and not receipt['old_actual_or_NEW_ordinary_mask_errors'];groups=data['nets']['/LOGIC_GND'];source=next(g for g in groups if'J11001.2#0'in g);rows=[]
    for i,g in enumerate(groups):
        for key in g:
            if key.startswith(('J15001.','J15002.')):rows.append({'native_pad_key':key,'native_group':i,'native_group_pad_key_count':len(g),'actual_current_full_native_J1_SOURCE_connected':key in source,'isolated_single_pad_group':len(g)==1})
    assert len(rows)==51;result={'status':'ACTUAL_CURRENT_FULL_NATIVE_CPP_ALL51_CM_GROUNDS_STILL_REQUIRE_SOURCE_CONNECTION','actual_R299_native_receipt':str(rf.resolve()),'actual_R299_native_receipt_SHA256':sha(rf),'actual_partition_file':str(part.resolve()),'actual_partition_SHA256':sha(part),'native_candidate_SHA256':data['sha256'],'actual_current_full_native_connected_CM_ground_count':sum(r['actual_current_full_native_J1_SOURCE_connected']for r in rows),'actual_current_single_pad_islands':sum(r['isolated_single_pad_group']for r in rows),'CM_ground_pad_keys':rows,'comparison_with_prospective_R461':'R461 is not replayed in this actual native board;44/51 is conditional SOURCE-before nomination only','physical_allnet_AFTER_model_groups_oldrefs_current_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print('R462_COMPLETE',sha(OUT/'receipt.json'),result['actual_current_full_native_connected_CM_ground_count'],result['actual_current_single_pad_islands'],flush=True)
if __name__=='__main__':main()
