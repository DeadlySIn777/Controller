"""Read-only exact generated-role/native definition inventory."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,uuid,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in (ROOT,ROOT/'sbc-power',ROOT/'coupled-recovery'):sys.path.insert(0,str(d))
import ordinary_routes as O
from verify_source import parse,children,child,atom
OUT=H/'FIELD-current-R157-to-R687-exact-native-definition-dependency-inventory-r733'
BASE=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
FINAL=H/'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r687/model.pkl'
SOURCE=ROOT/'R155-known-reference-native-diagnostic-r157/measure/copy/board.kicad_pcb'
PROFILE=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(v):return hashlib.sha256(v.wkb).hexdigest()
def obj(v):return hashlib.sha256(pickle.dumps(v,protocol=5)).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def parts(q):return sorted(list(q['zone_outline_shape'].geoms) if q['zone_outline_shape'].geom_type=='MultiPolygon' else [q['zone_outline_shape']],key=lambda s:(-s.area,s.bounds))
def identifiers(q):return [q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'separate-native-outer-'+str(i))) for i,_ in enumerate(parts(q))]
def main():
    assert not OUT.exists();OUT.mkdir();start=time.monotonic()
    assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(FINAL)=='3449baef41f8da4cdd7458cb120e906017e2e0c488c061aee9343e4b09022ee0'
    assert sha(SOURCE)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
    g0,h0,b0,q0,c0=pickle.loads(BASE.read_bytes());g,h,b,q,c=pickle.loads(FINAL.read_bytes())
    head,chunks,tail=O.C.pcbtext.split(SOURCE.read_bytes())
    sourcezones={O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if O.C.pcbtext.chunk_kind(ch)=='zone'}
    by0={r['uuid']:r for r in q0};by={r['uuid']:r for r in q}
    missing=[];row0=[];row1=[]
    for index,target in enumerate((q0,q)):
        rows=row0 if index==0 else row1
        for z in target:
            ids=identifiers(z)
            if index==0:
                for uid in ids:
                    if uid not in sourcezones:missing.append({'proposal_UUID':z['uuid'],'native_part_UUID':uid})
            rows.append({'proposal_UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],
                'physical_WKB_SHA256':hs(z['shape']),'intended_WKB_SHA256':hs(z['zone_outline_shape']),
                'native_part_UUIDs':ids,'native_profiles':{k:z[k] for k in PROFILE if k in z},
                'missing_profile_fields':[k for k in PROFILE if k not in z],
                'constituent_proposal_UUIDs':z.get('constituent_proposal_UUIDs')})
    comparisons=[]
    for key in ('tracks','vias','pads','shapes','footprints','outline','rule_areas'):
        if key in h0 or key in h:
            comparisons.append({'header_key':key,'before_object_SHA256':obj(h0.get(key)),'after_object_SHA256':obj(h.get(key)),
                'literal_object_pickle_equal':pickle.dumps(h0.get(key),protocol=5)==pickle.dumps(h.get(key),protocol=5)})
    changed=[]
    for uid in sorted(set(by0)&set(by)):
        old=by0[uid];new=by[uid]
        if any(old[k].wkb!=new[k].wkb for k in ('shape','zone_outline_shape')) or any(old.get(k)!=new.get(k) for k in PROFILE):
            changed.append({'proposal_UUID':uid,'before':next(r for r in row0 if r['proposal_UUID']==uid),'after':next(r for r in row1 if r['proposal_UUID']==uid)})
    outlines=[]
    for uid,ch in sourcezones.items():
        a=parse(ch.decode());outlines.append({'native_UUID':uid,'raw_net':atom(a,'net'),'layer':atom(a,'layer'),
            'priority':atom(a,'priority'),'chunk_SHA256':hashlib.sha256(ch).hexdigest(),
            'cached_fill_child_count':len(children(a,'filled_polygon'))+len(children(a,'fill_segments'))})
    put(OUT/'baseline-generated-role-native-parts.json',row0);put(OUT/'current-generated-role-native-parts.json',row1)
    put(OUT/'shared-role-geometry-or-profile-changes.json',changed);put(OUT/'native-zone-definition-inventory.json',outlines)
    put(OUT/'native-discrete-header-identity.json',comparisons)
    put(OUT/'receipt.json',{'status':'READ_ONLY_NATIVE_DEFINITION_DEPENDENCY_INVENTORY_NO_REPLAY_NO_ADOPTION',
        'exact_native_R157_SHA256':sha(SOURCE),'baseline_model_SHA256':sha(BASE),'current_model_SHA256':sha(FINAL),
        'native_zone_chunk_count':len(sourcezones),'baseline_owned_role_count':len(q0),'current_owned_role_count':len(q),
        'baseline_native_part_mapping_missing':missing,'removed_owned_proposal_UUIDs':sorted(set(by0)-set(by)),
        'new_current_owned_proposal_UUIDs':sorted(set(by)-set(by0)),'changed_shared_roles':len(changed),
        'missing_current_native_profile_fields':[{k:r[k] for k in ('proposal_UUID','missing_profile_fields')} for r in row1 if r['missing_profile_fields']],
        'header_identity':comparisons,'no_board_or_native_saved_fill_edits':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start})
    print('R733_COMPLETE',sha(OUT/'receipt.json'),'q',len(q0),len(q),'missing_native',len(missing),'changed',len(changed),flush=True)
if __name__=='__main__':main()
