"""Freeze the actual five accepted CORE feeds with exact latest B5 objects.

This is a partial, source-rooted construction checkpoint for joint assembly,
never a final no-loss/current/native acceptance. No board is written.
"""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely import set_precision
import core_inner_feed_r18 as I
L=I.L;P=I.P;FIELD=I.FIELD
OUT=L.OUT/'five-core-and-b5-checkpoint-r32'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    prior=L.OUT/'core-inner-feed-r24-checkpoint-frozen-r25/model.pkl'
    assert sha(prior)=='df6045e042610b3ccc7824db5db4f232e243202e84b5be53f34969e9c754bf8e'
    g,h,binding,_,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    cp=L.OUT/'core-inner-feed-r28';checkpoint=json.loads((cp/'checkpoint.json').read_text())
    accepted=pickle.loads((cp/'proposed-discrete.pkl').read_bytes());zones=pickle.loads((cp/'all-zones.pkl').read_bytes())
    assert len(checkpoint['rows'])==len(accepted['vias'])==3
    assert {q['uuid'] for q in accepted['vias']}=={r['via']['uuid'] for r in checkpoint['rows']}
    snapshot=[]
    for name in ('checkpoint.json','proposed-discrete.pkl','new-CORE-zones.pkl','all-zones.pkl','source-used.py'):
        src=cp/name;dst=OUT/name;dst.write_bytes(src.read_bytes());assert sha(src)==sha(dst)
        snapshot.append({'source_file':str(src.resolve()),'sha256':sha(src),'frozen_file':str(dst.resolve())})
    field_bindings=[]
    for directory,receipt_sha,counts,add_zones in (
        ('remaining-field-ground-feeds-r23','c7a120e6edf443c2aa6839b78d54673c6245de3a0312ce4757d9778f184fd3eb',(2,6,2),False),
        ('b5-source-rooted-feeds-r4','6de12c1e964abfcc1855e4449016301dcc0c3265ae7d7a7623c8107647e59c6f',(4,4,3),True)):
        folder=FIELD/directory;rf=folder/'receipt.json';assert sha(rf)==receipt_sha;r=json.loads(rf.read_text())
        df=folder/'proposed-discrete.pkl';zf=folder/'proposed-zones.pkl'
        assert sha(df)==r['proposed_discrete_sha256'] and sha(zf)==r['proposed_zones_sha256']
        ds=pickle.loads(df.read_bytes());zs=pickle.loads(zf.read_bytes())
        assert (len(ds['vias']),len(ds['tracks']),len(zs))==counts
        for kind in ('vias','tracks'):
            assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in ds[kind]};h[kind]+=ds[kind]
        if add_zones:
            assert not {q['uuid'] for q in zones} & {q['uuid'] for q in zs};zones+=zs
        else:
            byid={q['uuid']:q for q in zones}
            assert all(byid[q['uuid']]['shape'].equals(q['shape']) for q in zs)
        field_bindings.append({'directory':str(folder.resolve()),'receipt_sha256':sha(rf),'discrete_sha256':sha(df),'zones_sha256':sha(zf),'counts':counts})
    for kind in ('vias','tracks'):
        assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in accepted[kind]};h[kind]+=accepted[kind]
    r25=FIELD/'local-and-b5-return-audit-r25';rf=r25/'receipt.json'
    assert sha(rf)=='d5b593c9f678f7b3197057a8b06b4e86ec17fc061d7d69db607c112e4ee3bf42'
    rr=json.loads(rf.read_text());lf=r25/'local-owned-discrete.pkl';assert sha(lf)==rr['local_owned_discrete_sha256']
    local=pickle.loads(lf.read_bytes())
    for kind in ('vias','tracks'):
        byid={q['uuid']:q for q in h[kind]};assert all(byid[q['uuid']]==q for q in local[kind])
    for carve in checkpoint['carves']:
        for key in ('old','new','cutter'):
            f=Path(carve[key+'_wkb_file']);assert sha(f)==carve[key+'_wkb_sha256']
        z=next(q for q in zones if q['uuid']==carve['zone_uuid'])
        assert hashlib.sha256(z['shape'].wkb).hexdigest()==carve['new_wkb_sha256']
    known=set(binding.get('restored_generated_grid_UUIDs',[]))|{r['zone_uuid'] for r in checkpoint['carves']}
    for q in zones:
        if q['uuid'] in known or q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q.get('label')=='CORE-main-In2' or q.get('label','').startswith(('CORE-island-r19-','CORE-island-r26-')):
            q['shape']=set_precision(q['shape'],1e-6);known.add(q['uuid'])
    flash=FIELD/'additive-ground-b5-native-recipe-r27/native-flash-obligations.json'
    assert sha(flash)=='9c0970316e1a455efa2dbea86716df532a88fb73e2a6c7964f43f33009884e90'
    binding.update({'exact_native_discrete_board_sha256':'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a',
        'partial_five_CORE_checkpoint_parent_sha256':sha(prior),'accepted_CORE_r28_checkpoint_files':snapshot,
        'additional_exact_field_R23_and_B5_R4':field_bindings,'latest_field_R25_receipt_sha256':sha(rf),
        'latest_field_R25_exact_owned_25via_108segment_comparison':True,
        'field_R27_native_flash_ledger_file':str(flash.resolve()),'field_R27_native_flash_ledger_sha256':sha(flash),
        'restored_generated_grid_UUIDs':sorted(known),'CORE_field_main_return_antipads':checkpoint['carves'],
        'accepted_CORE_feed_count':5,'root_protected_overlay_included':False})
    candidate,cuts=P.projected(g,h,zones)
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    receipt={'verdict':'PARTIAL_FIVE_CORE_AND_LATEST_B5_FROZEN_MUTUAL_CONTACT_CURRENT_NATIVE_PENDING',
        'model_sha256':sha(model),'binding':binding,'accepted_CORE_feed_count':5,'r28_rows':checkpoint['rows'],
        'field_main_return_antipads':checkpoint['carves'],'all_latest_field_25via_108segment_objects_exact':True,
        'old_fill_retreats':cuts,'remaining_CORE_search':'OPEN; five actual feeds preserved, 33/54 prior pads joined before this new composition',
        'root_protected_overlay':'EXCLUDED; joint additive rebase/audit required','native_jobs':0,'board_written':False,
        'full_old_physical_contact_source_clearance_current_native_gates':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('FIVE_CORE_B5_FROZEN',sha(model),flush=True)
if __name__=='__main__':main()
