"""Quantized ordinary CORE island feeds against exact native and field local work.

This is a constructive host proposal. Source-contact retention, return sharing,
native refill and current/thermal qualification remain gates.
"""
import copy,hashlib,json,pickle,uuid,math
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import zone_projection_r1 as P
import io3_contact_restore_r2 as Q
import continuous_path_fast_r1 as CP
import local_copper_r2 as C
L=G.L;p=G.p;R=G.B.J.R;NET=p.norm(L.stage.caps.CORE)
OUT=L.OUT/'core-inner-feed-r18';FIELD=L.OUT.parent/'field-power'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def load():
    file=L.OUT/'core-retained-f-feeds-r17/model.pkl';g,h,binding,zones,_=pickle.loads(file.read_bytes());h=copy.deepcopy(h)
    binding['CORE_r17_model_sha256']=sha(file);binding['exact_native_discrete_board_sha256']='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    binding['field_local_overlays']=[]
    for directory,name,key in [('source-rooted-local-field-returns-r6','proposed-zones.pkl','proposal_sha256'),('bridged-field-ground-dogbones-r8','proposed-zones.pkl','proposed_zones_sha256')]:
        base=FIELD/directory;receipt=json.loads((base/'receipt.json').read_text());f=base/name;assert sha(f)==receipt[key];adds=pickle.loads(f.read_bytes());zones+=adds
        binding['field_local_overlays'].append({'file':str(f.resolve()),'sha256':sha(f),'receipt_sha256':sha(base/'receipt.json'),'kind':'new_zone','count':len(adds),'qualification':'proposal; mutual/native/current open'})
    for directory,name,key in [('bridged-field-ground-dogbones-r8','proposed-discrete.pkl','proposed_discrete_sha256'),('fine-outer-field-ground-joins-r9','proposed-tracks.pkl','proposal_sha256')]:
        base=FIELD/directory;receipt=json.loads((base/'receipt.json').read_text());f=base/name;assert sha(f)==receipt[key];adds=pickle.loads(f.read_bytes());adds=adds if isinstance(adds,dict) else {'tracks':adds}
        for kind,rows in adds.items():h[kind]+=rows
        binding['field_local_overlays'].append({'file':str(f.resolve()),'sha256':sha(f),'receipt_sha256':sha(base/'receipt.json'),'kind':'new_discrete','counts':{k:len(v) for k,v in adds.items()},'qualification':'r8 one .15 stub rejected pending field derived correction; mutual/native/current open'})
    precision=json.loads((L.OUT/'io3-field-crossings-r15/precision-state-ledger.json').read_text())
    # Explicitly preserve the r15 nine generated-grid objects after pickle.
    changed={q['uuid'] for q in zones if q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q.get('label')=='CORE-main-In2'}
    for q in zones:
        if q['uuid'] in changed:q['shape']=set_precision(q['shape'],1e-6)
    return g,h,binding,zones
def main():
    assert not OUT.exists();OUT.mkdir();g,h,binding,zones=load();candidate,cuts=P.projected(g,h,zones);Q.NET=NET;groups,parts,assign=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rows in enumerate(groups) for q in rows};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']]
    targets=[i for i,rows in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rows)];targets.sort(key=lambda i:sum(not q['ref'].startswith('@') for q in groups[i]),reverse=True)
    write(OUT/'initial-islands.json',{'binding':binding,'source_group':root,'targets':[{'group':i,'pads':[q for q in groups[i] if not q['ref'].startswith('@')]} for i in targets],'zone_metadata':[{k:v for k,v in q.items() if k not in ('shape','contacts','route')} for q in zones]})
    (OUT/'overlay-model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5));print('CORE_INNER_INITIAL',len(targets),'root',root,flush=True)
if __name__=='__main__':main()
