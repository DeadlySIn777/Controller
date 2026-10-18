"""Freeze accepted r24 Cu after an explicitly verified host-search interruption.

No accepted feed is discarded, and a partial checkpoint is never represented
as a completed search. Frozen corrected field R19 objects are composed exactly.
"""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely import set_precision
import core_inner_feed_r18 as I
G=I.G;P=I.P;Q=I.Q;L=I.L;p=I.p
OUT=L.OUT/'core-inner-feed-r24-checkpoint-frozen-r25'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();base=L.OUT/'core-inner-feed-r24'
    checkpoint=json.loads((base/'checkpoint.json').read_text())
    accepted=pickle.loads((base/'proposed-discrete.pkl').read_bytes())
    zones=pickle.loads((base/'all-zones.pkl').read_bytes())
    assert len(accepted['vias'])==len(checkpoint['rows'])
    assert {v['uuid'] for v in accepted['vias']}=={r['via']['uuid'] for r in checkpoint['rows']}
    prior=L.OUT/'core-retained-f-feeds-r17/model.pkl'
    g,h,binding,_,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    field=I.FIELD/'repaired-local-return-audit-r19';fr=json.loads((field/'receipt.json').read_text())
    assert fr['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING'
    localfile=field/'local-owned-discrete.pkl';assert sha(localfile)==fr['local_owned_discrete_sha256']
    local=pickle.loads(localfile.read_bytes());assert len(local['vias'])==19 and len(local['tracks'])==98
    for kind in ('vias','tracks'):
        known={q['uuid'] for q in h[kind]};assert not known & {q['uuid'] for q in local[kind]+accepted[kind]}
        h[kind]+=local[kind]+accepted[kind]
    r18=I.FIELD/'logic-island-repair-r18';r18r=json.loads((r18/'receipt.json').read_text())
    vm=next(q for q in h['vias'] if q['uuid']==r18r['existing_via_UUID'])
    assert vm['flashed']==r18r['existing_native_flash_mask']
    vm['flashed']=[l for l in I.LAYERS if l in vm['flashed'] or l==r18r['prospective_additional_flash_layer']]
    vm['prospective_new_flash_requires_native_refill']=r18r['prospective_additional_flash_layer']
    checkpoint_binding=[]
    for name in ('checkpoint.json','proposed-discrete.pkl','new-CORE-zones.pkl','all-zones.pkl'):
        src=base/name;copyfile=OUT/name;copyfile.write_bytes(src.read_bytes());assert sha(copyfile)==sha(src)
        checkpoint_binding.append({'source_file':str(src.resolve()),'source_sha256':sha(src),'frozen_file':str(copyfile.resolve()),'frozen_sha256':sha(copyfile)})
    grid={q['uuid'] for q in zones if q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q.get('label')=='CORE-main-In2' or q.get('label','').startswith('CORE-island-r19-')}
    grid|={q['zone_uuid'] for q in checkpoint['carves']}
    for q in zones:
        if q['uuid'] in grid:q['shape']=set_precision(q['shape'],1e-6)
    binding.update({'exact_native_discrete_board_sha256':'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a','CORE_r17_model_sha256':sha(prior),'corrected_field_R19_receipt_sha256':sha(field/'receipt.json'),'corrected_field_R19_discrete_sha256':sha(localfile),'field_existing_via_new_flash_obligation':{'uuid':vm['uuid'],'original_native_flashes':r18r['existing_native_flash_mask'],'prospective_required':vm['flashed']},'accepted_r24_checkpoint_files':checkpoint_binding,'restored_generated_grid_UUIDs':sorted(grid),'search_interrupted_and_resumed':True})
    candidate,cuts=P.projected(g,h,zones);Q.NET=I.NET
    groups,_,_=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rs in enumerate(groups) for q in rs}
    sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']]
    remaining=[{'group':i,'pads':[q for q in rs if not q['ref'].startswith('@')]} for i,rs in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rs)]
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    receipt={'verdict':'PARTIAL_ACCEPTED_CORE_CHECKPOINT_FROZEN_FOR_CONSTRUCTIVE_RESUMPTION','model_sha256':sha(model),'binding':binding,'rows':checkpoint['rows'],'remaining':remaining,'field_main_return_antipads':checkpoint['carves'],'accepted_checkpoint_feed_count':len(accepted['vias']),'old_fill_retreats':cuts,'original_search_completed':False,'native_jobs':0,'board_written':False,'all_contact_current_and_native_gates':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('FROZEN_ACCEPTED_CORE_CHECKPOINT',len(accepted['vias']),len(remaining),sha(model),flush=True)
if __name__=='__main__':main()
