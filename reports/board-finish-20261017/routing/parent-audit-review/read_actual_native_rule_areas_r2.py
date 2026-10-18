"""Read actual R299 native rule areas only; Fill0/Save0."""
import pcbnew,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
SOURCE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb';EXPECTED='6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632';OUT=HERE/'read-only-native-R299-rule-areas-r2'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
def chain(c):
 return [[c.CPoint(i).x,c.CPoint(i).y]for i in range(c.PointCount())]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();assert sha(SOURCE)==EXPECTED;b=pcbnew.LoadBoard(str(SOURCE));rows=[]
 zones=[(z,{'kind':'board'})for z in b.Zones()]
 for fp in b.GetFootprints():
  at=fp.GetPosition();owner={'kind':'footprint','UUID':fp.m_Uuid.AsString(),'ref':fp.GetReference(),'at_IU':[at.x,at.y],'orientation_degrees':fp.GetOrientationDegrees(),'layer':b.GetLayerName(fp.GetLayer())}
  zones.extend((z,owner)for z in fp.Zones())
 for z,owner in zones:
  if not z.GetIsRuleArea():continue
  poly=z.Outline();outlines=[]
  for i in range(poly.OutlineCount()):outlines.append({'outer_IU':chain(poly.COutline(i)),'holes_IU':[chain(poly.CHole(i,j))for j in range(poly.HoleCount(i))]})
  rows.append({'UUID':z.m_Uuid.AsString(),'owner':owner,'name':z.GetZoneName(),'layers':[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()if z.GetLayerSet().Contains(l)],'is_rule_area':bool(z.GetIsRuleArea()),'GetDoNotAllowZoneFills':bool(z.GetDoNotAllowZoneFills()),'GetDoNotAllowTracks':bool(z.GetDoNotAllowTracks()),'GetDoNotAllowVias':bool(z.GetDoNotAllowVias()),'GetDoNotAllowPads':bool(z.GetDoNotAllowPads()),'GetDoNotAllowFootprints':bool(z.GetDoNotAllowFootprints()),'native_outline_arcs':poly.ArcCount(),'outlines':outlines})
 assert sha(SOURCE)==EXPECTED;put('exact-native-rule-areas.json',rows);put('receipt.json',{'status':'ACTUAL_R299_RULE_AREA_NATIVE_API_READ_ONLY_BOUND','native_board_SHA256':EXPECTED,'rule_area_count':len(rows),'board_owned_rule_count':sum(r['owner']['kind']=='board'for r in rows),'footprint_owned_rule_count':sum(r['owner']['kind']=='footprint'for r in rows),'zone_fill_prohibition_count':sum(r['GetDoNotAllowZoneFills']for r in rows),'method':'GetDoNotAllowZoneFills() exact API; Board.Zones plus every Footprint.Zones, CuStack layers; raw Outline/COutline/CHole CPoint integer nanometres','native_Fill_calls':0,'native_Save_calls':0,'source_unchanged':True,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE)},'output_SHA256':sha(OUT/'exact-native-rule-areas.json'),'elapsed_seconds':time.monotonic()-st});print('NATIVE_RULES_COMPLETE',len(rows),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
