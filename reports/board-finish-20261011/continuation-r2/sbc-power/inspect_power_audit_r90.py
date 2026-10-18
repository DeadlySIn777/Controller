"""Compact diagnosis of the frozen R89 source/contact obligations."""
import json,pickle,hashlib
from pathlib import Path
from shapely.ops import unary_union
import complete_geometry_r2 as G
L=G.L;p=G.p
O=L.OUT/'power-audit-diagnosis-r90'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    prior=L.OUT/'r17031-translated-source-composition-r78/model.pkl'
    g,h,b,z,c=pickle.loads(prior.read_bytes())
    receipt=L.OUT/'full-power-source-contact-audit-r89/receipt.json'
    rr=json.loads(receipt.read_text());cache=pickle.loads((receipt.parent/'groups.pkl').read_bytes())
    out=[]
    for row in rr['rows']:
        n=row['net_normalized_for_lookup_only'];details=cache[n];parts=details['new_parts'];assign=details['new_assign'];root=row['source_group']
        bare=[q for q in row['all_named_pads'] if not q['source_connected']]
        fragments=[]
        for q in row['new_zones']:
            zz=next(x for x in z if x['uuid']==q['uuid']);outline=zz.get('zone_outline_shape',zz['shape'])
            for d in q['detached_components']:
                if d['source_connected']:continue
                piece=p.hubs.components(zz['shape'])[d['component_index']]
                hits=[{'outline_index':i,'intersection_mm2':s.intersection(piece).area,'outline_area_mm2':s.area,'outline_bounds':list(s.bounds)} for i,s in enumerate(p.hubs.components(outline)) if s.intersection(piece).area>0]
                fragments.append({**d,'zone_uuid':q['uuid'],'zone_label':q['label'],'layer':q['layer'],'bounds':list(piece.bounds),'outline_hits':hits})
        branches=[]
        for br in row['old_Cu_union_branch_splits']:
            for q in br['remaining_parts']:
                if q['candidate_group']==root:continue
                s=parts[br['layer']][q['candidate_part']]
                branches.append({**q,'layer':br['layer'],'old_union_part':br['old_union_part'],'actual_whole_piece_area_mm2':s.area,'bounds':list(s.bounds),'physical_WKB_sha256':hashlib.sha256(s.wkb).hexdigest()})
        lost=[]
        for lostrow in row['entirely_lost_old_Cu_union_parts']:
            pads=[]
            for pad in g['pads']:
                if p.norm(pad['net'])!=n:continue
                shape=unary_union(p.base.polygons(pad['layers'].get(lostrow['layer'],[])))
                if abs(shape.area-lostrow['old_area_mm2'])<1e-10:
                    new=next(x for x in h['pads'] if x['uuid']==pad['uuid'])
                    pads.append({'ref':pad['ref'],'num':pad['num'],'uuid':pad['uuid'],'old_at':[pad['x'],pad['y']],'new_at':[new['x'],new['y']],'old_area_mm2':shape.area,'old_shape_WKB_sha256':hashlib.sha256(shape.wkb).hexdigest(),'replacement_source_group':next((i for i,rs in enumerate(details['new_groups']) if any(a['uuid']==pad['uuid'] for a in rs)),None)})
            lost.append({**lostrow,'exact_area_pad_nominees':pads})
        record={'net':n,'bare_named':bare,'detached_new_fragments':fragments,'old_detached_branch_pieces':branches,'lost_old_components':lost}
        out.append(record)
        print('DIAG',n,'bare',[(q['ref'],q['pad'],q['group']) for q in bare],'newfragmentareas',[round(q['area_mm2'],6) for q in fragments],'oldbranches',len(branches),'largebranches',[(round(q['actual_whole_piece_area_mm2'],6),q['bounds']) for q in branches if q['actual_whole_piece_area_mm2']>.2],'lost',lost,flush=True)
    (O/'receipt.json').write_text(json.dumps({'prior_model_sha256':sha(prior),'audit_sha256':sha(receipt),'rows':out,'diagnosis_only':True,'native_jobs':0,'board_written':False},indent=2)+'\n')
if __name__=='__main__':main()
