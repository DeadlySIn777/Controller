"""Review exactly the 48 existing ISO1212 SENSE/IN local circuit nets.

This is a source-backed field-filter recipe, separate from ordinary digital
autorouting. External pre-RTHR wiring, sensor supplies, floating SUB islands,
logic outputs, power and all other analog/timing circuits stay excluded.
"""
import argparse,json,math
from pathlib import Path
from hardware_build_ordinary_route_manifest import native,sha,load,write,ROOT

PDF=ROOT/'research/digital-inputs/iso1212.pdf'
PDF_SHA='41e0bc7308dd4e0cc8c7f30efb6a2cd87bcc865d9195095ff849be6036cb2328'

def review(source,adoption):
    source=Path(source).resolve();adoption=Path(adoption).resolve();accepted=load(adoption)
    if not all(accepted.get(k) is True for k in ('passed','adopted','independent_validation_pass')) or accepted.get('native_ERC_errors')!=0:
        raise ValueError('Actual adopted source required')
    for name,digest in accepted['source_hashes'].items():
        path=Path(name);path=path if path.is_absolute() else source/path
        if sha(path)!=digest:raise ValueError('Frozen electrical source changed: '+str(path))
    if sha(PDF)!=PDF_SHA:raise ValueError('Exact manufacturer ISO1212 revision required')
    model=load(source/'design.json');nodes,nets,functions=native(model,source/'netlist.xml')
    di=load(ROOT/'hardware/motherboard_di/design.json')
    if di['interface']['operating_max_v']!=30 or di['source_spec']['current_above_falling_to_30v_a'][1]!=.00275 or len(di['channels'])!=24:
        raise ValueError('Actual selected 0–30V/2.75mA field input limits changed')
    rows={}
    for i,ch in enumerate(di['channels']):
        u='U'+str(8001+i//2);r='R'+str(8001+i);rs='R'+str(8101+i);c='C'+str(8001+i)
        sense_pin,in_pin=('16','15') if i%2==0 else ('11','10')
        if ch['schematic_ref']!=u or ch['threshold_ref']!=r or ch['sense_ref']!=rs or ch['filter_ref']!=c:
            raise ValueError('Exact selected channel identities changed')
        for ref,mpn in ((u,'ISO1212DBQR'),(r,'SMM02040C1001FB300'),(rs,'CRCW0603562RFKEA'),(c,'C2012C0G2A103J125AA')):
            if model['components'][ref]['mpn']!=mpn:raise ValueError('Actual field RC manufacturer identity changed: '+ref)
        ret=nodes[u,'9']
        if nodes[u,'14']!=ret or nodes[c,'2']!=ret or not ret.endswith('/FIELD_B_0V'):
            raise ValueError('Actual receiving/filter FIELD_B return changed')
        for kind,endpoints in (
          ('SENSE',[(u,sense_pin),(r,'2'),(rs,'1'),(c,'1')]),
          ('IN',[(u,in_pin),(rs,'2')])):
            name=nodes[u,sense_pin if kind=='SENSE' else in_pin]
            if not name.endswith('/DI'+str(i)+'_'+kind) or nets[name]!=sorted(endpoints):
                raise ValueError('Exact full physical field RC endpoint set changed: '+name)
            if functions[u][sense_pin if kind=='SENSE' else in_pin]['type']!='input':
                raise ValueError('Manufacturer receiving pin function changed')
            rows[name]=dict(signal_class='isolated_field_input_local_filter',maximum_voltage_v=30,
              normal_current_max_a=.00275,return_net=ret,source_pins=[list(p) for p in sorted(endpoints)],
              layers=['F.Cu'],reference_layers={'F.Cu':'In1.Cu'},width_mm=.20,clearance_mm=.15,
              reference_corridor_margin_mm=.10,allow_vias=False,
              maximum_source_pad_route_span_mm=12.,maximum_added_path_length_mm=18.,
              actual_receiver_field_ground_pins=[[u,'9'],[u,'14']],
              external_pre_RTHR_node_excluded=nodes[r,'1'],
              manufacturer_layout_basis='SLLSEY7G 8.4.1: RSENSE/CIN/RTHR same top layer, own FGND reference; RTHR external high-voltage pin at least4mm from receiver/CIN/RSENSE pins. No SUB-to-ground route.',
              ordinary_logic_promoted=False,physical_EMC_filter_delay_and_surge_qualified=False)
    if len(rows)!=48:raise ValueError('Exact48 local field-filter nets required')
    return dict(passed=True,source_review_sha256={str(source/'design.json'):sha(source/'design.json'),str(source/'netlist.xml'):sha(source/'netlist.xml'),str(adoption):sha(adoption),str(PDF):PDF_SHA,str(ROOT/'hardware/motherboard_di/design.json'):sha(ROOT/'hardware/motherboard_di/design.json'),str(Path(__file__).resolve()):sha(__file__)},
      nets=rows,exact_source_physical_footprints=len(model['components']),
      scope='48 same-side ISO1212 local SENSE/IN filter nets only; existing selected 0–30V limits retained.',
      exact_new_via_count_permitted=0,full_external_input_wiring_completed=False,
      full_source_owned_return_qualification_required_before_routing=True,
      routing_run=False,manufacturing_ready=False,physical_measurements_performed=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','adoption','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable report required')
    result=review(a.source,a.adoption);write(a.out,result)
    print(dict(passed=True,exact_local_nets=len(result['nets']),maximum_voltage_v=30,new_vias_permitted=0))
if __name__=='__main__':main()
