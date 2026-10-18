"""Actual CM51 split groups/source faces, no current allocation/bridge credit."""
import hashlib,json,pickle,sys,collections
from pathlib import Path
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM51-actual-drilled-split-groups-source-bridge-diagnosis-r272'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/R270-true-literal-DOB-current-filled-alignment-requalification-r271/T4-plus-R7';mp=base/'model.pkl';r=json.loads((base/'construction-receipt.json').read_text());assert sha(mp)==r['model_sha256'];g,h,b,q,c=pickle.loads(mp.read_bytes());gp=base/'actual-drilled-groups.pkl';gs=pickle.loads(gp.read_bytes());groups=gs['/LOGIC_GND'];root=K.root(groups,'J11001','2');ri=next(i for i,xs in enumerate(groups)if xs is root);cm=[p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'];assert len(cm)==51;cmuids={p['uuid']for p in cm};pmap={p['uuid']:p for p in h['pads']};groupids=sorted({i for i,xs in enumerate(groups)if any(r['kind']=='pad'and r['uuid']in cmuids for r in xs)});recby={l:[r for r in root if r['layer']==l]for l in K.LAYERS};trees={l:STRtree([r['shape']for r in rows])for l,rows in recby.items()};rows=[];nearest=[]
 for i in groupids:
  xs=groups[i];keys=K.keys(xs);cp=[pmap[uid]for uid in cmuids if any(('pad',uid,l)in keys for l in pmap[uid]['layers'])];layers={};witness=[]
  for l in K.LAYERS:
   bodies=[r['shape']for r in xs if r['layer']==l]
   if not bodies:continue
   sh=unary_union(bodies);f=O/('CMgroup'+str(i)+'-'+l+'-whole-actual-drilled-body.wkb');f.write_bytes(sh.wkb);layers[l]={'area_mm2':sh.area,'bounds':list(sh.bounds),'body_WKB_sha256':sha(f),'actual_piece_record_count':len(bodies)}
   if not recby[l]:continue
   j=int(trees[l].nearest(sh));target=recby[l][j];a,bb=nearest_points(sh,target['shape']);gap=a.distance(bb);n={'CM_group':i,'layer':l,'CM_ground_pin_count':len(cp),'whole_floating_group_bounds':list(sh.bounds),'floating_true_Cu_point':[a.x,a.y],'actual_source_root_true_Cu_point':[bb.x,bb.y],'literal_edge_gap_mm':gap,'actual_source_item':{k:target.get(k)for k in('kind','uuid','ref','pin','contour')},'actual_source_piece_WKB_sha256':hashlib.sha256(target['shape'].wkb).hexdigest(),'not_a_fullwidth_centreline_or_barrel_or_clearance_nomination':True};nearest.append(n);witness.append(n)
  entries=[{'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'at':[p['x'],p['y']],'layers':list(p['layers']),'actual_source_rooted':i==ri}for p in cp];viauids={r['uuid']for r in xs if r['kind']=='via'};native={v['uuid']:v for v in g['vias']};vias=[{'object':v,'exact_original_native_record':native.get(v['uuid']),'native_mask_authority_preserved':v.get('flashed')==native.get(v['uuid'],{}).get('flashed')}for v in h['vias']if v['uuid']in viauids];otherpads=[{'ref':r['ref'],'pin':r['pin'],'UUID':r['uuid']}for r in xs if r['kind']=='pad'and r['uuid']not in cmuids];rows.append({'CM_group':i,'actual_source_rooted':i==ri,'CM_physical_pads':entries,'all_layer_keys_count':len(keys),'other_actual_pad_layer_entries':otherpads,'actual_or_prospective_barrels':vias,'actual_drilled_Cu_by_layer':layers});put(O/'split-ground-group-progress.json',rows);print('R272_CM_GROUP',i,len(cp),len(keys),len(vias),list(layers),flush=True)
 put(O/'nearest-actual-source-Cu-edge-witnesses.json',sorted(nearest,key=lambda r:r['literal_edge_gap_mm']));put(O/'all-CM51-native-actual-pad-poses.json',cm);result={'verdict':'CM51_EXACT_PHYSICAL_SPLIT_AND_SOURCE_EDGE_WITNESSES_NO_BRIDGE_PROOF','model_sha256':sha(mp),'actual_drilled_groups_sha256':sha(gp),'CM_ground_pad_count':len(cm),'CM_distinct_actual_group_count':len(groupids),'CM_source_rooted_group_count':sum(i==ri for i in groupids),'full_CM_plus_AUX_cancellation_return_A':3.5593046439628484,'groups':rows,'closest_same_layer_source_edge_witnesses':sorted(nearest,key=lambda r:r['literal_edge_gap_mm'])[:12],'ordinary_0p5_0p2_new_hole_actual_native_masks_all77_source_current_and_true_fullwidth_multilayer_bridge':'OPEN','no_equal_current_split_or_new_return_capacity_claim':True,'native_jobs':0,'board_written':False,'adopted':False};put(O/'receipt.json',result);print('R272_COMPLETE',sha(O/'receipt.json'),len(groupids),min((r['literal_edge_gap_mm']for r in nearest),default=None),flush=True)
if __name__=='__main__':main()
