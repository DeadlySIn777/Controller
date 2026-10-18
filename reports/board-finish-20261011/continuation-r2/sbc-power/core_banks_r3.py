"""Repack full-current CORE banks after the explicit local CT/GND/SBC Cu."""
import json,hashlib,math
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,box
import core_lane_r2 as R
import core_variable_plane_r2 as V
L=R.L;p=R.p
def main():
    g,h,*_=R.model();local=json.loads((L.OUT/'local-copper-r2.json').read_text())
    h={**h,'vias':h['vias']+local['new_vias'],'tracks':h['tracks']+local['new_tracks']}
    source=json.loads((L.OUT/'CORE-In2-variable-plane-r2.json').read_text())
    plane=from_wkb((L.OUT/'CORE-In2-after-IO3-fingers-r4.wkb').read_bytes());banks=[source['ordinary_via_banks'][0]]
    window=box(108,155,124,166);p.WINDOW=window
    region=V.via_region(h,L.stage.caps.CORE,window).intersection(plane.buffer(-.3))
    required=(114.2,161.4);chosen=[]
    if region.covers(Point(required)):chosen.append(required);region=region.difference(Point(required).buffer(.8))
    sites=p.hubs.pack_region(region,(116,161.4),spacing=.8);sites=sorted(sites,key=lambda x:math.dist(x,(116,161.4)))
    chosen+=sites[:16-len(chosen)]
    banks.append({'name':'load','sites':[{'at':s,'diameter_mm':.6,'drill_mm':.3,'ordinary_SMD_hole_margin':True,'maximum_planning_A':.5} for s in chosen],'legal_region_mm2':region.area,'required_total_current_A':4.396304643962849,'equal_share_claimed':False})
    result={'exact_board':L.live.SHA,'candidate_CORE_plane_file':str((L.OUT/'CORE-In2-after-IO3-fingers-r4.wkb').resolve()),'candidate_plane_sha256':hashlib.sha256((L.OUT/'CORE-In2-after-IO3-fingers-r4.wkb').read_bytes()).hexdigest(),'ordinary_via_banks':banks,'planning_current_A':4.396304643962849,'B_C11062_CORE_stub_site_in_bank':required in chosen,'load_bank_count':len(chosen),'local_geometry_sha256':hashlib.sha256((L.OUT/'local-copper-r2.json').read_bytes()).hexdigest(),'padfree_IO3_restoration_and_final_IR_not_yet_incorporated':True,'board_written':False,'native_jobs':0}
    (L.OUT/'CORE-banks-r3.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
