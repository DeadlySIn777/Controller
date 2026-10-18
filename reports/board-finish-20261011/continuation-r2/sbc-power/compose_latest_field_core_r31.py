"""Compose exact latest B5 additions before full CORE/source/contact audit.

R23 is already in the completed CORE search. Only B5 R4 additions are added
here, with exact R25 ownership comparison and explicit native flash ledger.
No mutual collision is waived and no native board is written.
"""
import copy,json,pickle,hashlib,sys
from pathlib import Path
from shapely import set_precision,STRtree
import core_inner_feed_r18 as I
G=I.G;P=I.P;Q=I.Q;L=I.L;p=I.p;FIELD=I.FIELD
OUT=L.OUT/'latest-field-core-composition-r31'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else L.OUT/'core-inner-feed-r28/model.pkl'
    assert path.exists() and not OUT.exists();OUT.mkdir();g,h,binding,zones,_=pickle.loads(path.read_bytes());h=copy.deepcopy(h)
    b5=FIELD/'b5-source-rooted-feeds-r4';rpath=b5/'receipt.json';assert sha(rpath)=='6de12c1e964abfcc1855e4449016301dcc0c3265ae7d7a7623c8107647e59c6f';r=json.loads(rpath.read_text())
    df=b5/'proposed-discrete.pkl';zf=b5/'proposed-zones.pkl';assert sha(df)==r['proposed_discrete_sha256'] and sha(zf)==r['proposed_zones_sha256'];ds=pickle.loads(df.read_bytes());adds=pickle.loads(zf.read_bytes())
    assert len(ds['vias'])==4 and len(ds['tracks'])==4 and len(adds)==3
    for kind in ('vias','tracks'):
        assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in ds[kind]};h[kind]+=ds[kind]
    assert not {q['uuid'] for q in zones} & {q['uuid'] for q in adds};zones+=adds
    r25=FIELD/'local-and-b5-return-audit-r25';r25r=json.loads((r25/'receipt.json').read_text());assert sha(r25/'receipt.json')=='d5b593c9f678f7b3197057a8b06b4e86ec17fc061d7d69db607c112e4ee3bf42';assert r25r['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING'
    localfile=r25/'local-owned-discrete.pkl';assert sha(localfile)==r25r['local_owned_discrete_sha256'];local=pickle.loads(localfile.read_bytes())
    for kind in ('vias','tracks'):
        composed={q['uuid']:q for q in h[kind]}
        assert all(composed[q['uuid']]==q for q in local[kind]),('latest_field_owned_exact_comparison',kind)
    flashfile=FIELD/'additive-ground-b5-native-recipe-r27/native-flash-obligations.json';assert sha(flashfile)=='9c0970316e1a455efa2dbea86716df532a88fb73e2a6c7964f43f33009884e90'
    binding.update({'latest_CORE_model_file':str(path.resolve()),'latest_CORE_model_sha256':sha(path),'latest_B5_receipt_sha256':sha(rpath),'latest_B5_discrete_sha256':sha(df),'latest_B5_zones_sha256':sha(zf),'latest_field_R25_receipt_sha256':sha(r25/'receipt.json'),'latest_field_R25_exact_owned_25via_108segment_comparison':True,'field_R27_native_flash_ledger_file':str(flashfile.resolve()),'field_R27_native_flash_ledger_sha256':sha(flashfile)})
    # Restore only explicitly recorded generated-grid objects. Original
    # geometry is never blanket snapped, and positive boolean deltas remain
    # the earlier bound carve obligations.
    known=set(binding.get('restored_generated_grid_UUIDs',[]))
    for q in zones:
        if q['uuid'] in known or q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q.get('label')=='CORE-main-In2' or q.get('label','').startswith(('CORE-island-r19-','CORE-island-r26-')):q['shape']=set_precision(q['shape'],1e-6)
    collisions=[]
    for layer in h['copper_layers']:
        zz=[q for q in zones if q['layer']==layer];tree=STRtree([q['shape'] for q in zz])
        for i,q in enumerate(zz):
            for jj in tree.query(q['shape'].buffer(.625),predicate='intersects'):
                j=int(jj)
                if j<=i or p.norm(q['net'])==p.norm(zz[j]['net']):continue
                other=zz[j];required=max(G.gap(h,q['net'],other['net']),float(q.get('clearance_mm',.15)),float(other.get('clearance_mm',.15)))+.025
                if q['shape'].buffer(required).intersects(other['shape']):collisions.append({'layer':layer,'first_uuid':q['uuid'],'first_raw_net':q['net'],'second_uuid':other['uuid'],'second_raw_net':other['net'],'required_mm_with_guard':required,'actual_distance_mm':q['shape'].distance(other['shape']),'overlap_area_mm2':q['shape'].intersection(other['shape']).area})
    candidate,cuts=P.projected(g,h,zones);model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    receipt={'verdict':'LATEST_FIELD_CORE_COMPOSITION_MUTUAL_NEW_ZONE_SPACING_PASS_CONTACT_CURRENT_NATIVE_PENDING' if not collisions else 'LATEST_FIELD_CORE_MUTUAL_NEW_ZONE_SPACING_FAILED','model_sha256':sha(model),'binding':binding,'foreign_new_zone_spacing_failures':collisions,'original_fill_retreats':cuts,'source_contact_original_and_native_loss_audits':'NEXT_REQUIRED','all_ordinary_holes_SMD_drill_and_physical_Cu_gate':'NEXT_REQUIRED','native_jobs':0,'board_written':False,'full_signed_current_return_and_native_gates':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('LATEST_FIELD_CORE_COMPOSITION',len(collisions),sha(model),flush=True)
if __name__=='__main__':main()
