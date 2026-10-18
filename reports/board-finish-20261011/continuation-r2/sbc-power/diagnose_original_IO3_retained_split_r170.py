"""Compact original-198b IO3 split geometry diagnosis on exact SAFE R160."""
import hashlib, json, pickle
from pathlib import Path
from shapely.ops import unary_union, nearest_points
H=Path(__file__).resolve().parent.parent
O=H/'sbc-power/original-IO3-retained-split-diagnosis-r170'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    mp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl'
    assert sha(mp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
    gf=H/'sbc-power/SAFE-original198b-DC936-power-contact-audit-r150/groups.pkl'
    rf=H/'sbc-power/SAFE-original198b-DC936-power-contact-audit-r150/receipt.json'
    g,h,b,z,c=pickle.loads(mp.read_bytes());a=pickle.loads(gf.read_bytes())['/IO_3V3'];receipt=json.loads(rf.read_bytes())
    row=next(r for r in receipt['rows'] if r['net_normalized_for_lookup_only']=='/IO_3V3');root=row['source_group'];assert len(row['old_group_splits'])==1
    targets={r['group'] for r in row['old_group_splits'][0]['new_groups']};targets.add(root)
    unions={};rows=[]
    for i in sorted(targets):
        group=a['new_groups'][i];named=[r for r in group if not r['ref'].startswith('@')]
        ur={l:unary_union([s for s,j in zip(parts,a['new_assign'][l]) if j==i]) for l,parts in a['new_parts'].items()}
        unions[i]=ur
        rows.append({'group':i,'source':i==root,'physical_keys':len(group),'named_pads':len(named),'named_examples':named[:5],'layers':{l:{'area_mm2':s.area,'bounds_mm':s.bounds,'components':len(getattr(s,'geoms',[s]))} for l,s in ur.items() if not s.is_empty}})
    edges=[]
    for i in sorted(targets):
        for j in sorted(targets):
            if j<=i:continue
            for l in h['copper_layers']:
                x,y=unions[i][l],unions[j][l]
                if x.is_empty or y.is_empty:continue
                aa,bb=nearest_points(x,y)
                edges.append({'groups':[i,j],'layer':l,'gap_mm':aa.distance(bb),'closest_mm':[list(aa.coords[0]),list(bb.coords[0])]})
    edges.sort(key=lambda r:r['gap_mm'])
    branch=[]
    for br in row['old_Cu_union_branch_splits']:
        by={}
        for q in br['remaining_parts']:
            key=str(q['candidate_group']);d=by.setdefault(key,{'components':0,'retained_area_mm2':0.});d['components']+=1;d['retained_area_mm2']+=q['retained_area_mm2']
        branch.append({'layer':br['layer'],'old_union_part':br['old_union_part'],'old_group':br['old_group'],'old_area_mm2':br['old_area_mm2'],'remaining_groups':by})
    out={'verdict':'ORIGINAL_IO3_SPLIT_GEOMETRY_DIAGNOSIS_NO_CONSTRUCTION','model_sha256':sha(mp),'audit_sha256':sha(rf),'cache_sha256':sha(gf),'source_group':root,'split_groups':rows,'shortest_group_layer_edges':edges[:50],'nearest_source_edges':sorted([e for e in edges if root in e['groups']],key=lambda r:r['gap_mm'])[:30],'original_branch_split_summary':branch,'native_jobs':0,'board_written':False}
    (O/'geometry-cache.pkl').write_bytes(pickle.dumps({'unions':unions,'edges':edges,'root':root,'targets':targets,'audit_cache':a},protocol=5))
    (O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n')
    print('IO3_SPLIT_GROUPS',[(r['group'],r['physical_keys'],r['named_pads']) for r in rows],flush=True)
    print('IO3_NEAREST_EDGES',edges[:12],flush=True)
    print('IO3_BRANCH_SUMMARY',branch,flush=True)
if __name__=='__main__':main()
