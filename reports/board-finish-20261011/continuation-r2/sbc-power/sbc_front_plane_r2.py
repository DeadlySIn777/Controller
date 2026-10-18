"""Complete local F supply component probe, including all six native CM contacts."""
import json,hashlib
from shapely.geometry import box,Point
from shapely.ops import unary_union
import core_lane_r2 as R
L=R.L;p=R.p
def main():
    g,h,*_=R.model();local=json.loads((L.OUT/'local-copper-r2.json').read_text());h={**h,'vias':h['vias']+local['new_vias'],'tracks':h['tracks']+local['new_tracks']}
    window=box(108,156,124,172);p.WINDOW=window
    free=R.free_layer(h,p.NET,'F.Cu',window,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True)
    pads=[r for r in h['pads'] if (r['ref']=='U11012' and r['num'] in ('8','9','10')) or (r['ref'] in ('C15001','C15002') and r['num']=='1') or (r['ref']=='J15001' and r['num'] in ('77','79','81','83','85','87'))]
    targets=[(r['ref']+'.'+r['num'],L.body_pad(r)) for r in pads];rows=[]
    for i,part in enumerate(p.hubs.components(free)):
        names=[name for name,body in targets if body.intersects(part)]
        if any(name.startswith('U11012') for name in names):
            file=L.OUT/('SBC-F-component'+str(i)+'-r2.wkb');file.write_bytes(part.wkb)
            rows.append({'component':i,'area_mm2':part.area,'joined_pad_names':names,'all_six_CM_contacts_joined':all('J15001.'+n in names for n in ('77','79','81','83','85','87')),'all_U12_output_pads_joined':all('U11012.'+n in names for n in ('8','9','10')),'both_F_bulk_caps_joined':all(name in names for name in ('C15001.1','C15002.1')),'candidate_Cu_file':str(file.resolve()),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    result={'exact_source_board':L.live.SHA,'rows':rows,'complete_F_geometric_supply_component_exists':any(r['all_six_CM_contacts_joined'] and r['all_U12_output_pads_joined'] and r['both_F_bulk_caps_joined'] for r in rows),'current_sharing_full_IR_return_and_native_contacts_open':True,'direct_F_plane_is_variable_width':True,'new_CORE_F_fanout_must_avoid_this_plane':True,'all_other_SBC_shared_contacts_still_required':True,'board_written':False,'native_jobs':0}
    (L.OUT/'SBC-F-component-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
