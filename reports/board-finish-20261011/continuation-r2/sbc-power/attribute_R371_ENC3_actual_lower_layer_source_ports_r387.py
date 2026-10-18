"""Inspect actual ENC3 source ports for a bounded ordinary signal dive if F is blocked."""
import json,pickle,hashlib,sys,time
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import Point
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-R371-ENC3-actual-existing-lower-layer-source-port-attribution-r387'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());scope=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());own={p['uuid']for p in scope['pads']};base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};net=L.norm(scope['source_pin_nets']['2']);_,groups=K.physical(base,net,K.hole_context(base));contacts={r['UUID']for r in scope['old_direct_contacts'][1]['retained_old_direct_contacts']};components=[xs for xs in groups if any(r['uuid']in contacts for r in xs)];vmap={v['uuid']:v for v in h['vias']};pmap={p['uuid']:p for p in h['pads']};rows=[]
 for gi,xs in enumerate(components):
  for rr in xs:
   if rr['layer']in ('F.Cu','In1.Cu','In4.Cu')or rr['kind']not in ('via','pad'):continue
   item=vmap.get(rr['uuid'])if rr['kind']=='via'else pmap.get(rr['uuid']);xy=[item['x'],item['y']]
   if Point(*xy).distance(Point(84.547,24.7))>20:continue
   rows.append({'source_component':gi,'UUID':rr['uuid'],'kind':rr['kind'],'actual_layer':rr['layer'],'xy':xy,'actual_all_drill_subtracted_annulus_or_pad_area_mm2':rr['shape'].area,'raw_net':rr['net'],'native_source_mask_unmodified':True,'pad_ref':item.get('ref'),'pad_pin':item.get('num'),'diameter_mm':item.get('d'),'drill_mm':item.get('drill'),'flashed_actual_model':item.get('flashed')})
 put(O/'actual-existing-ENC3-lower-layer-source-ports.json',rows);(O/'actual-old-ENC3-contact-components-after-owned-pad-withdrawal.pkl').write_bytes(pickle.dumps(components,protocol=5));put(O/'receipt.json',{'verdict':'ACTUAL_ENC3_LOWER_LAYER_SOURCE_PORT_ATTRIBUTION_NO_NEW_VIA_OR_PATH','current_R371_model_sha256':sha(D/'model.pkl'),'raw_source_net':scope['source_pin_nets']['2'],'old_contact_components_after_only_owned_pad_withdrawal':len(components),'actual_lower_layer_source_port_rows':len(rows),'rows_by_layer':{ly:sum(r['actual_layer']==ly for r in rows)for ly in ('In2.Cu','In3.Cu','B.Cu')},'new_signal_via_ordinary_return_actual_mask_old_reference_preservation_and_three_layer_leg_path':'OPEN','model_native_source_profile_rules_or_masks_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R387',sha(O/'receipt.json'),len(rows),flush=True)
if __name__=='__main__':main()
