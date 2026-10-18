"""Concrete saved-positive DIC B backbone before the coupled CMD detour."""
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'construct_DIC_saved_B_backbone_CMD_r192.py';assert not p.exists();s=(H/'construct_DIC_actual_paired_CMD_r186.py').read_text();s=s.replace('DIC-actual-paired-CMD-construction-r186','DIC-saved-B-backbone-CMD-construction-r192').replace('DIC_R186_EXACT_ROUTE','DIC_R192_EXACT_ROUTE')
s=s.replace("requested=[(CMD,'B.Cu',[123.05,95.05],[128.549999,100.55]),(NET,'F.Cu',attach[0],so['signal']),(NET,'B.Cu',so['signal'],to['signal']),(NET,'F.Cu',to['signal'],attach[1])]", "requested=[(NET,'F.Cu',attach[0],so['signal']),(NET,'B.Cu',so['signal'],to['signal']),(NET,'F.Cu',to['signal'],attach[1]),(CMD,'B.Cu',[123.05,95.05],[128.549999,100.55])]")
s=s.replace("path,search=T.route(parts[0],tuple(a),tuple(b));path=[[round(x,6),round(y,6)] for x,y in path];body=", """if route_net==NET and layer=='B.Cu':
    saved=next(q for q in r164['selected']['routes'] if L.norm(q['raw_net'])==NET and q['layer']=='B.Cu');path=copy.deepcopy(saved['points_mm']);assert path[0]==a;path[-1]=b;search={'method':'EXACT_SAVED_R164_POSITIVE_B_BACKBONE_WITH_ONLY_CORRECTED_TERMINAL','saved_R164_backbone_points':saved['points_mm'],'old_terminal':saved['points_mm'][-1],'new_terminal':b}
    if not free.covers(LineString(path)):row['failure']='saved_B_backbone_current_strict_physical_region';break
   else:path,search=T.route(parts[0],tuple(a),tuple(b))
   path=[[round(x,6),round(y,6)] for x,y in path];body=""")
s=s.replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN','DIC_SAVED_B_BACKBONE_REAL_PAIRED_CMD_POSITIVE_INDEPENDENT_OPEN').replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_INCOMPLETE','DIC_SAVED_B_BACKBONE_REAL_PAIRED_CMD_INCOMPLETE')
assert "if route_net==NET and layer=='B.Cu'" in s and "requested=[(NET,'F.Cu'" in s
compile(s,str(p),'exec');p.write_text(s);print(p)
