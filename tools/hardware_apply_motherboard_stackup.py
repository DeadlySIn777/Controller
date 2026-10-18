"""Apply the explicit six-layer fabrication request to a native PCB copy.

This sets engineering fabrication requirements, not factory approval. Existing
physical objects and copper are invariant; controlled impedance still requires
PCBWay's final material/etch model and coupon verification before manufacture.
"""
import argparse,copy,json,shutil,subprocess
from pathlib import Path
from hardware_build_assembly import parse,dump,child,children,value,q

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
COPPER=(('F.Cu',.070),('In1.Cu',.035),('In2.Cu',.035),('In3.Cu',.035),('In4.Cu',.035),('B.Cu',.070))
DIELECTRIC=(.220,.330,.220,.330,.220)
CONTROL_VIA_EXCEPTIONS=(
 ('/motherboard_power_entry/C_PGOOD',234.65,156.18),
 ('/motherboard_power_entry/CORE_CORE_CONFIG',237.38,156.45),
 ('/motherboard_power_entry/C_PGOOD',230.65,182.18),
 ('/motherboard_power_entry/MOTION_CORE_CONFIG',233.38,182.45))

def validate(spec):
    if spec['copper_layers']!=[dict(name=n,thickness_mm=t) for n,t in COPPER]:raise ValueError('Exact six-layer copper request required')
    if spec['dielectric_thickness_mm']!=list(DIELECTRIC):raise ValueError('Exact symmetrical pressed dielectric request required')
    if abs(sum(t for n,t in COPPER)+sum(DIELECTRIC)-spec['nominal_board_thickness_mm'])>1e-9:raise ValueError('Stack thickness does not reconcile')
    if spec['factory_stackup_approval']is not False or spec['physical_impedance_verified']is not False:raise ValueError('Engineering request cannot claim factory or physical approval')
    if spec['reference_layers']!={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'}:raise ValueError('Outer signals need adjacent same-domain return references')
    exceptions=spec['exact_low_current_control_via_exceptions']
    actual={(r['net'],*r['position_mm'])for r in exceptions}
    if len(exceptions)!=4 or actual!=set(CONTROL_VIA_EXCEPTIONS):raise ValueError('Only four exact control-via locations are eligible')
    if any((r['diameter_mm'],r['finished_drill_mm'],r['annular_width_mm'],r['factory_DFM_and_quote_approved'])!=(.40,.20,.10,False)for r in exceptions):raise ValueError('Control-via geometry and unapproved factory status must stay explicit')
    for row in spec['controlled_impedance']:
        if row['target_ohm']not in (90,100) or row['tolerance_percent']!=10:raise ValueError('Reviewed pair impedance targets required')
    return True

def spec():
    result=dict(schema_version=1,nominal_board_thickness_mm=1.600,finished_thickness_tolerance_percent=10,
        copper_layers=[dict(name=n,thickness_mm=t) for n,t in COPPER],dielectric_thickness_mm=list(DIELECTRIC),
        dielectric_material='FR-4 Tg170 minimum; 2116-family prepreg, pressed thickness as specified; core dielectric0.330mm',
        dielectric_nominal_Dk=[4.45,4.60,4.45,4.60,4.45],dielectric_loss_tangent_for_layout_model=.02,
        surface_finish='ENIG',soldermask='Both sides; no exposed signal vias; BGA/capillary vias tented unless assembly review specifies filling',
        nominal_outer_finished_copper_oz=2,nominal_inner_copper_oz=1,
        reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
        controlled_impedance=[dict(interface='USB2',target_ohm=90,tolerance_percent=10),dict(interface='HDMI TMDS / Ethernet MDI',target_ohm=100,tolerance_percent=10)],
        ordinary_track_minimum_mm=.2,conventional_via_diameter_mm=.5,conventional_via_finished_drill_mm=.2,
        conventional_via_annular_width_mm=.15,ordinary_copper_clearance_mm=.15,copper_to_edge_minimum_mm=.5,
        inner_drill_to_copper_minimum_mm=.205,uncoated_SELV_interdomain_engineering_clearance_mm=.6,
        final_FPGA_conventional_pad_via_exception_mm=.125,
        GCT_USB4105_own_locating_hole_ground_pad_exception_mm=.18,
        exact_low_current_control_via_exceptions=[dict(net=n,position_mm=[x,y],diameter_mm=.40,finished_drill_mm=.20,annular_width_mm=.10,scope='Exact four receiving control escapes only; never power/thermal vias',factory_DFM_and_quote_approved=False)for n,x,y in CONTROL_VIA_EXCEPTIONS],
        factory_stackup_approval=False,physical_impedance_verified=False,
        primary_sources=['https://www.pcbway.com/pcb_prototype/What_is_layer_stack_up.html','https://www.pcbway.com/multi-layer-laminated-structure.html'],
        provenance='Engineering custom thickness request based on PCBWay published 6-layer2oz/1oz2116/core family; not an asserted stock stackup. Published laminated versus finished dimensions are distinct.',
        required_factory_review=['Confirm actual Tg170 laminate/prepreg product, pressed thicknesses and outer finished copper before controlled-impedance routing release',
            'Provide field-solver impedance width/gap adjustment and90/100ohm coupon results; do not alter isolation, lands, pad clearance or outline without review',
            'Confirm .20mm finished plated drills/.15mm annulus and the exact .125mm BGA pad-via and .18mm own GCT NPTH clearances for2ozouter6L processing',
            'Separately quote and approve only the four exact .40/.20mm control vias with .10mm annuli under the scoped coordinate rules; no whole-board annulus relaxation',
            '460x340mm assembly handling/warpage, no panel substitutions without reviewed datums'])
    validate(result);return result

def main():
    import pcbnew
    from hardware_populate_motherboard_pcb import sha,write,pad_template
    from hardware_route_logic_return import identity
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    base=a.board.resolve();out=a.out.resolve()
    if out.exists():raise ValueError('Fresh owned report required')
    request=spec();tree=parse(base.read_text());prior=copy.deepcopy(tree)
    setup=child(tree,'setup')
    if child(setup,'stackup')is not None:raise ValueError('Existing explicit stackup requires separate review')
    layers=['stackup']
    for n,kind in [('F.SilkS','Top Silk Screen'),('F.Paste','Top Solder Paste'),('F.Mask','Top Solder Mask')]:layers.append(['layer',q(n),['type',q(kind)]])
    for i,(n,t) in enumerate(COPPER):
        layers.append(['layer',q(n),['type',q('copper')],['thickness',str(t)]])
        if i<5:layers.append(['layer',q('dielectric '+str(i+1)),['type',q('core'if i in (1,3)else'prepreg')],['thickness',str(DIELECTRIC[i])],['material',q('FR4 Tg170')],['epsilon_r',str(request['dielectric_nominal_Dk'][i])],['loss_tangent','0.02']])
    for n,kind in [('B.Mask','Bottom Solder Mask'),('B.Paste','Bottom Solder Paste'),('B.SilkS','Bottom Silk Screen')]:layers.append(['layer',q(n),['type',q(kind)]])
    layers.extend([['copper_finish',q('ENIG')],['dielectric_constraints','yes']]);setup.insert(1,layers)
    if value(child(child(tree,'general'),'thickness')[1])!='1.6':raise ValueError('Previous nominal thickness changed')
    reverse=copy.deepcopy(tree);s=child(reverse,'setup');s.remove(child(s,'stackup'))
    if dump(reverse)!=dump(prior):raise ValueError('Change outside exact stackup metadata')
    out.mkdir(parents=True);dest=out/'motherboard-stackup-candidate.kicad_pcb'
    for f in base.parent.iterdir():
        if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
        elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    dest.write_text(dump(tree)+'\n');write(out/'fabrication-stackup-request.json',request)
    b=pcbnew.LoadBoard(str(base));r=pcbnew.LoadBoard(str(dest));r.BuildConnectivity()
    for exception in request['exact_low_current_control_via_exceptions']:
        matches=[t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()==exception['net']and [round(pcbnew.ToMM(v),6)for v in t.GetPosition()]==exception['position_mm']]
        if len(matches)!=1 or abs(pcbnew.ToMM(matches[0].GetWidth(pcbnew.F_Cu))-.40)>1e-6 or abs(pcbnew.ToMM(matches[0].GetDrillValue())-.20)>1e-6:
            raise ValueError('Actual exact scoped low-current control via differs from fabrication request')
    assert {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={t.m_Uuid.AsString():identity(t)for t in r.GetTracks()}
    assert {f.GetReference():sorted((pad_template(v)for v in f.Pads()),key=repr)for f in b.GetFootprints()}=={f.GetReference():sorted((pad_template(v)for v in f.Pads()),key=repr)for f in r.GetFootprints()}
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--format','json','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    d=json.loads((out/'drc.json').read_text());receipt=dict(source_board_sha256=sha(base),board_sha256=sha(dest),stackup_request_sha256=sha(out/'fabrication-stackup-request.json'),
        native_DRC_regular=len(d['violations']),native_ignored_checks=d.get('ignored_checks',[]),
        exact_physical_objects_copper_and_existing_zone_definitions_preserved=True,uncapped_missing_joins=r.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    write(out/'receipt.json',receipt);print(receipt)

if __name__=='__main__':main()
