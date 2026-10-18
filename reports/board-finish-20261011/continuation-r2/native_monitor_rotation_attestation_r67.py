"""Read exact pad poses/attributes and native inside polygons, no refill/save."""
import hashlib,json,sys
from pathlib import Path
import pcbnew
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polygons(sh):
 return [[[[sh.Outline(i).CPoint(k).x/1e6,sh.Outline(i).CPoint(k).y/1e6]for k in range(sh.Outline(i).PointCount())],[[[sh.Hole(i,j).CPoint(k).x/1e6,sh.Hole(i,j).CPoint(k).y/1e6]for k in range(sh.Hole(i,j).PointCount())]for j in range(sh.HoleCount(i))]]for i in range(sh.OutlineCount())]
def main():
 specfile,boardfile,out=map(Path,sys.argv[1:]);r=json.loads(specfile.read_bytes());assert sha(boardfile)==r['candidate_sha256'];b=pcbnew.LoadBoard(str(boardfile));fp=next(f for f in b.GetFootprints()if f.GetReference()==r['ref']);assert fp.m_Uuid.AsString()==r['native_footprint_uuid'];assert [fp.GetPosition().x/1e6,fp.GetPosition().y/1e6]==r['target_pose'][:2];assert (fp.GetOrientationDegrees()-r['target_pose'][2])%360==0
 pads=[]
 for p in fp.Pads():
  uid=p.m_Uuid.AsString();expected=r['expected_pads'][uid];pos=p.GetPosition();assert [pos.x,pos.y]==expected['at_IU']and p.GetNumber()==expected['pin']and p.GetNetname()==expected['raw_net'];assert p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD
  layers={}
  for layer in b.GetEnabledLayers().CuStack():
   if not p.IsOnLayer(layer):continue
   poly=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(poly,layer,0,pcbnew.FromMM(.005),pcbnew.ERROR_INSIDE);layers[b.GetLayerName(layer)]=polygons(poly)
  assert list(layers)==['F.Cu'];pads.append({'UUID':uid,'ref':fp.GetReference(),'num':p.GetNumber(),'net':p.GetNetname(),'x':pos.x/1e6,'y':pos.y/1e6,'layers':layers,'smd':True,'npth':False,'hole':None,'absolute_pad_angle_deg':p.GetOrientationDegrees(),'size_IU':[p.GetSize().x,p.GetSize().y],'drill_IU':[p.GetDrillSize().x,p.GetDrillSize().y]})
 assert set(r['expected_pads'])=={p['UUID']for p in pads}
 out.write_text(json.dumps({'verdict':'PASS_NATIVE_EXACT_ROTATED_R9026_PAD_POSE','candidate_sha256':sha(boardfile),'spec_sha256':sha(specfile),'FP_pose_mm_deg':r['target_pose'],'footprint_UUID':fp.m_Uuid.AsString(),'native_pads':pads,'actual_native_polygon_inside_error_mm':.005,'fresh_native_polygons_must_replace_host_nomination_before_independent_qualification':True,'no_refill_or_save':True,'full_monitor_source_reference_DRC_threshold_current':'OPEN'},indent=1)+'\n');print('R67_NATIVE_PAD_POSE_PASS',flush=True)
if __name__=='__main__':main()
