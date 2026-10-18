"""Read-only bound inventory before any controlled original barrel exception."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point
OUT=H/'AO1-CS-cage-old-COM-barrel-actual-source-mask-own-incident-binding-r686';UID='2e243304-8de5-44b1-bee4-d95e5ae3017b';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 mp=pin(H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/AO1-only-sparse-prospective-normal-native-antipad-host-model.pkl','3605d85bb9c672bb2d8dc58b3a6d2c01b01c2e3412978c9941846ee5ad415b72');h=pickle.loads(mp.read_bytes());gp=pin(mp.parent/'AO1-and-local-antipad-all-drilled-after-groups.pkl','4587bd3d6b32ba0cfac8f4c1dfcddd193184ef0bb8049ddac85419a9a9f191de');groups=pickle.loads(gp.read_bytes())[COM];source=K.root(groups,'U14619','7');v=next(v for v in h['vias']if v['uuid']==UID);xy=[v['x'],v['y']];incident=[t for t in h['tracks']if K.L.norm(t['net'])==COM and min(math.dist(xy,t['a']),math.dist(xy,t['b']))<=.000002];touching=[t for t in h['tracks']if K.L.norm(t['net'])==COM and K.L.body(t).distance(Point(xy).buffer(v['d']/2))<=.000002];sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');raw=K.C.inventory(sp.read_bytes())[3];old={u:raw[u]for u in[UID]+[t['uuid']for t in incident]};packet=OUT/'exact-old-COM-barrel-and-own-endpoint-incident-chunks-BINDING-ONLY.pkl';packet.write_bytes(pickle.dumps(old,protocol=5));mf=pin(ROOT/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');actual=json.loads(mf.read_bytes())['vias'];native=next(q for q in actual if q['uuid']==UID)if isinstance(actual,list)else actual[UID]
 def clean(t):return {k:t[k]for k in('uuid','net','layer','a','b','w')if k in t}
 keys=K.keys(source);r={'verdict':'READ_ONLY_ORIGINAL_COM_BARREL_SOURCE_AND_INCIDENT_SCOPE_BOUND_NO_EXCEPTION_OR_MOVE','input_SHA256':pins,'old_barrel':{k:v[k]for k in('uuid','net','x','y','d','drill','flashed')if k in v},'actual_native_barrel_profile':native,'R20_SOURCE_original_barrel_layer_keys':[list(k)for k in keys if k[1]==UID],'endpoint_exact_own_COM_incident_tracks':[clean(t)for t in incident],'all_body_touching_own_COM_tracks':[clean(t)for t in touching],'old_chunks_packet_file':str(packet.resolve()),'old_chunks_packet_SHA256':sha(packet),'foreign_material_retained':True,'old_material_deletes_or_moves':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n')
 for p,s in pins.items():assert sha(p)==s,p
 print('R686_COMPLETE',sha(OUT/'receipt.json'),'barrel',xy,'d/drill',v['d'],v['drill'],'incident',[clean(t)for t in incident],flush=True)
if __name__=='__main__':main()
