"""Freeze exact original CDONE barrel/source/contact scope before a real move."""
import sys,pickle,json,time
from pathlib import Path
from shapely.ops import unary_union
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;A=K.A;sha=N.sha
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';UID='b1e550d5-047a-447c-a64c-45c2a92c14b0';NET='/fpga_core/FPGA_CDONE';OUT=P/'CM79-actual-CDONE-original-barrel-source-and-incident-scope-r422'
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before();assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(BASE.read_bytes());native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flash=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias'];actual,ctx,pads=N.convert_selected_actual(h,c,native,flash,{NET},source_pcb=N.R157/'copy/board.kicad_pcb');groups=K.physical(actual,NET,ctx)[1];group=next(xs for xs in groups if any(r['kind']=='via'and r['uuid']==UID for r in xs));v=next(v for v in actual['vias']if v['uuid']==UID);ann={r['layer']:r['shape']for r in group if r['kind']=='via'and r['uuid']==UID};incident=[]
 for r in group:
  if r['uuid']==UID or r['layer']not in ann:continue
  contact=r['shape'].intersection(ann[r['layer']])
  if contact.area>0:
   exact=next((t for t in actual['tracks']if t['uuid']==r['uuid']),None);incident.append({'UUID':r['uuid'],'kind':r['kind'],'layer':r['layer'],'positive_actual_native_contact_mm2':contact.area,'exact_track':exact})
 pcb=N.R157/'copy/board.kicad_pcb';iv=A.C.inventory(pcb.read_bytes());chunk=iv[3][UID];(OUT/'exact-original-CDONE-barrel-native-chunk').write_bytes(chunk);oldkeys=sorted(K.keys(group));packet={'original_barrel':v,'actual_native_before':actual,'all_actual_before_groups':groups,'original_barrel_group':group,'actual_annuli':ann,'incident_contacts':incident,'BASE_h':h,'BASE_q':q,'BASE_c':c,'g':g,'b':b,'native_geometry':native,'actual_flashes':flash};(OUT/'only-exact-original-CDONE-barrel-native-source-scope.pkl').write_bytes(pickle.dumps(packet,protocol=5));receipt={'status':'ORIGINAL_CDONE_BARREL_SOURCE_AND_INCIDENT_SCOPE_FROZEN','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'BASE_SHA256':sha(BASE),'barrel':v,'native_chunk_SHA256':sha(OUT/'exact-original-CDONE-barrel-native-chunk'),'actual_group_count':len(groups),'barrel_group_layer_keys':len(oldkeys),'all_pad_identities':sorted({(r['ref'],str(r['pin']),r['uuid'])for r in group if r['kind']=='pad'}),'all_original_retained_layer_keys':oldkeys,'all_actual_original_native_incident_positive_contacts':incident,'source_selector_requires_exact_contract_lookup':True,'original_full_dc1a_retained_all_other_original_Cu_and_holes_hard':True,'only_this_barrel_and_new_owned_reconnects_may_change_if_qualified':True,'old_native_masks_source_refs_current_native':'OPEN after constructive real move','scope_packet_SHA256':sha(OUT/'only-exact-original-CDONE-barrel-native-source-scope.pkl'),'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1,allow_nan=False)+'\n',encoding='utf-8');print('R422_COMPLETE',sha(OUT/'receipt.json'),len(incident),len(oldkeys),flush=True)
if __name__=='__main__':main()
