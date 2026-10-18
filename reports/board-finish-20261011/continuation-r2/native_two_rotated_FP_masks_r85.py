"""Read actual pad masks, angles and field poses from two previously attested exact clones."""
import hashlib,json,sys
from pathlib import Path
import pcbnew
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mm(p):return [p.x/1e6,p.y/1e6]
def main():
 spec,out=map(Path,sys.argv[1:]);r=json.loads(spec.read_bytes());assert len(r['footprints'])==2;rows=[]
 for item in r['footprints']:
  bp=Path(item['board_file']);sp=Path(item['pose_spec_file']);assert sha(bp)==item['candidate_sha256']and sha(sp)==item['pose_spec_sha256'];ps=json.loads(sp.read_bytes());assert ps['candidate_sha256']==sha(bp);b=pcbnew.LoadBoard(str(bp));fp=next(f for f in b.GetFootprints()if f.GetReference()==ps['ref']);assert fp.m_Uuid.AsString()==ps['native_footprint_uuid']and mm(fp.GetPosition())==ps['target_pose'][:2]and(fp.GetOrientationDegrees()-ps['target_pose'][2])%360==0
  pads=[];posepads=[];stack=list(b.GetEnabledLayers().CuStack());shapes={pcbnew.PAD_SHAPE_RECT:'rect',pcbnew.PAD_SHAPE_ROUNDRECT:'roundrect'}
  for p in fp.Pads():
   uid=p.m_Uuid.AsString();exp=ps['expected_pads'][uid];assert [p.GetPosition().x,p.GetPosition().y]==exp['at_IU']and p.GetNumber()==exp['pin']and p.GetNetname()==exp['raw_net']and p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and mm(p.GetDrillSize())==[0.,0.]
   layers=[b.GetLayerName(l)for l in p.GetLayerSet().Seq()];flashes=[b.GetLayerName(l)for l in stack if p.FlashLayer(l)];assert flashes==['F.Cu']and set(layers)=={'F.Cu','F.Mask','F.Paste'};shape=shapes[p.GetShape(pcbnew.F_Cu)]
   pads.append({'type':'smd','shape':shape,'size_mm':mm(p.GetSize(pcbnew.F_Cu)),'drill_native':None,'native_declared_layers':layers,'expected_copper_layer_names':flashes,'roundrect_rratio':str(p.GetRoundRectRadiusRatio(pcbnew.F_Cu))if shape=='roundrect'else'','custom_primitive_native':None,'expected_raw_net':p.GetNetname(),'physical_pad_UUID':uid,'pin':p.GetNumber(),'absolute_position_mm':mm(p.GetPosition()),'absolute_angle_deg':p.GetOrientationDegrees()})
   posepads.append({'pin':p.GetNumber(),'pad_uuid':uid,'raw_net':p.GetNetname(),'absolute_center_mm':mm(p.GetPosition()),'actual_original_clone_native_flashes':flashes,'source_named_pin':True})
  assert {p['physical_pad_UUID']for p in pads}==set(ps['expected_pads']);texts=[]
  for f in fp.GetFields():texts.append({'kind':'property','identity':f.GetName(),'absolute_position_mm':mm(f.GetPosition()),'native_angle_deg':f.GetTextAngleDegrees(),'native_layer':f.GetLayerName(),'actual_text':f.GetText()})
  for t in fp.GraphicalItems():
   if isinstance(t,pcbnew.PCB_TEXT):texts.append({'kind':'fp_text','identity':t.GetText(),'absolute_position_mm':mm(t.GetPosition()),'native_angle_deg':t.GetTextAngleDegrees(),'native_layer':t.GetLayerName()})
  mask={'ref':ps['ref'],'footprint_UUID':ps['native_footprint_uuid'],'target_native_layer':'F.Cu','target_pose_mm_deg':ps['target_pose'],'exact_chunk_sha256':item['replacement_FP_chunk_sha256'],'pads':pads,'texts':texts};pose={'ref':ps['ref'],'native_footprint_uuid':ps['native_footprint_uuid'],'root_pose_mm_deg':ps['target_pose'],'layer':'F.Cu','schematic_path':fp.GetPath().AsString(),'chunk_path':item['replacement_FP_chunk_file'],'chunk_sha256':item['replacement_FP_chunk_sha256'],'pads':posepads}
  rows.append({'ref':ps['ref'],'native_candidate_sha256':sha(bp),'native_pose_row':pose,'native_mask_and_text_row':mask,'every_actual_pad_identity_and_integer_centre_exact':True,'actual_native_fields_pads_masks_angles_recorded':True});assert sha(bp)==item['candidate_sha256']
 out.write_text(json.dumps({'verdict':'PASS_TWO_EXACT_NATIVE_ROTATED_FP_MASKS_ANGLES_AND_FIELDS','spec_sha256':sha(spec),'rows':rows,'no_native_fill_save_or_source_edit':True,'new_copper_whole_native_connectivity_DRC_current_threshold_fault':'OPEN','adopted':False},indent=1)+'\n');print('R85_NATIVE_FP_MASKS_PASS',len(rows),flush=True)
if __name__=='__main__':main()
