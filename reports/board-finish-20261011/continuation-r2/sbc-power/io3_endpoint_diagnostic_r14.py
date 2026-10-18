"""Diagnose exact endpoint access; no layout mutation or native job."""
import pickle,json,hashlib
from pathlib import Path
from shapely import from_wkb,set_precision,STRtree
from shapely.ops import unary_union,nearest_points
from shapely.geometry import box
import complete_geometry_r2 as G
import zone_projection_r1 as P
import io3_contact_restore_r2 as Q
L=G.L;p=G.p;R=G.B.J.R;NET='/IO_3V3';OUT=L.OUT/'io3-endpoint-diagnostic-r14b'
def main():
    assert not OUT.exists();OUT.mkdir()
    base=L.OUT/'coupled-power-geometry-frozen-r13';g,h,binding,zones=pickle.loads((base/'exact-native-bound-model.pkl').read_bytes())
    receipt=json.loads((base/'receipt.json').read_text());checkpoint=json.loads((base/'routing-checkpoint.json').read_text())
    core=next(q for q in zones if q['label']=='CORE-main-In2')
    for q in checkpoint['fingers']:
        f=Path(q['geometry_file']);assert hashlib.sha256(f.read_bytes()).hexdigest()==q['sha256'];new={**q,'label':'IO3-r13-new-restoration-'+str(q['candidate_group']),'shape':from_wkb(f.read_bytes())};zones.append(new)
        if new['layer']=='In2.Cu':core['shape']=set_precision(core['shape'].difference(new['shape'].buffer(.175)),1e-6)
    candidate,cuts=P.projected(g,h,zones);Q.NET=NET;groups,parts,assign=Q.groups(candidate,return_details=True)
    allids={r['uuid']:i for i,rows in enumerate(groups) for r in rows};original=json.loads((base/'initial-contact-partitions.json').read_text());root=allids[original['full_candidate_groups'][original['new_main_root_group']][0]['uuid']]
    unresolved={q['candidate_group']:allids[q['old_contacts'][0]['uuid']] for q in receipt['IO3_unresolved_contact_groups']}
    board=unary_union(p.base.polygons(g['outline'])).buffer(-.525);window=box(.526,.526,449.474,234.474);p.WINDOW=window;oldzoneids={q['uuid'] for q in g['zones']};rows=[]
    (OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,candidate,groups,parts,assign,root,unresolved),protocol=5))
    for layer in h['copper_layers']:
        source=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i==root])
        for mode in ('frozen','old-fill-retreat'):
            remove=oldzoneids if mode=='old-fill-retreat' else {q['uuid'] for q in g['zones'] if layer in ('In1.Cu','In4.Cu') and p.norm(q['net'])=='/LOGIC_GND'}
            model={**candidate,'zones':[q for q in candidate['zones'] if q['uuid'] not in remove]}
            free=set_precision(R.free_layer(model,NET,layer,window,(L.stage.caps.CORE,) if layer=='In2.Cu' else (),reference_guard=None,allow_own_via_connection=True).intersection(board),1e-6)
            file=OUT/(layer+'-'+mode+'.wkb');file.write_bytes(free.wkb);comps=p.hubs.components(free);tree=STRtree(comps);sr=set(map(int,tree.query(source,predicate='intersects')))
            for oldid,newid in unresolved.items():
                target=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i==newid]);tg=set(map(int,tree.query(target,predicate='intersects')));shared=sr&tg
                closest=None
                if sr and tg:
                    a,b=nearest_points(unary_union([comps[i] for i in sr]),unary_union([comps[i] for i in tg]));closest={'distance_mm':a.distance(b),'source_edge':list(a.coords[0]),'target_edge':list(b.coords[0])}
                row={'old_group':oldid,'new_group':newid,'layer':layer,'mode':mode,'source_area':source.area,'target_area':target.area,'target_free_area':target.intersection(free).area,'source_free_components':len(sr),'target_free_components':len(tg),'shared_components':len(shared),'closest_free_edges':closest};rows.append(row);print('ENDPOINT',json.dumps(row),flush=True)
    (OUT/'receipt.json').write_text(json.dumps({'binding':binding,'rows':rows,'native_jobs':0,'board_written':False},indent=2)+'\n')
if __name__=='__main__':main()
