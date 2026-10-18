"""Actual native-candidate controls for the separate literal CORE proof."""
from pathlib import Path
import sys,json,copy
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as c
from hardware_route_logic_return import mm,xy
from hardware_check_return_corridors import circle
P=Path(__file__).parent;O=P/'CORE-cleaned-CCK-native-controls-r05';O.mkdir(exist_ok=False)
B=P/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'
A=P/'CORE-literal-antipad-join-cck-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'
before=pcbnew.LoadBoard(str(B));rows=[]
def case(name,mutate=None):
    after=pcbnew.LoadBoard(str(A));change=mutate(after)if mutate else {}
    try:
        r=c.review(before,after);passed=r['passed'];error=None
    except (ValueError,AssertionError)as ex:passed=False;error=str(ex)
    rows.append(dict(name=name,expected_pass=mutate is None,actual_pass=passed,expected_result_observed=passed==(mutate is None),actual_rejection=error,native_mutation=change))
    print(json.dumps(dict(name=name,expected_result_observed=rows[-1]['expected_result_observed'],error=error)),flush=True)
def extra(b):
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet('/fpga_core/FPGA_FLASH_CCK_SOURCE'));t.SetStart(xy((95.2,46.4)));t.SetEnd(xy((95.3,46.4)));t.SetLayer(pcbnew.In2_Cu);t.SetWidth(pcbnew.FromMM(.35));b.Add(t)
    return dict(actual_extra_uuid=t.m_Uuid.AsString(),new_unreviewed_conductor_rejected=True)
def source_pad(b):
    p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='U2001'and p.GetNumber()=='3');old=mm(p.GetPosition());p.SetPosition(xy((old[0]+.01,old[1])));return dict(source='U2001.3',old_xy=old,new_xy=mm(p.GetPosition()))
def retained_via(b):
    t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='3376a140-028c-4a29-84f0-21540ab5865a');old=mm(t.GetPosition());t.SetPosition(xy((old[0]+.01,old[1])));return dict(retained_via_uuid=t.m_Uuid.AsString(),old_xy=old,new_xy=mm(t.GetPosition()))
def physical_cut(b,kind):
    b.BuildConnectivity();pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
    if kind=='annulus':
        via=next(t for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='/CORE_1V2'and t.FlashLayer(pcbnew.In3_Cu));shape=circle(tuple(via.GetPosition()),pcbnew.FromMM(.5));target=dict(via_uuid=via.m_Uuid.AsString(),xy=mm(via.GetPosition()),radius_mm=.5)
    else:
        pos=mm(pads['L2001','2'].GetPosition());shape=c.f.box(pos[0]-.6,pos[1]-.6,pos[0]+.6,pos[1]+.6);target=dict(actual_regulator_output='L2001.2',xy=pos,cut_bounds_mm=[pos[0]-.6,pos[1]-.6,pos[0]+.6,pos[1]+.6])
    changes=[]
    for z in b.Zones():
        if z.GetNetname()!='/CORE_1V2'or not z.IsOnLayer(pcbnew.In3_Cu)or z.GetIsRuleArea():continue
        old=c.f.duplicate(z.GetFilledPolysList(pcbnew.In3_Cu));new=c.f.subtract(old,shape);removed=c.f.subtract(old,new)
        if removed.OutlineCount():z.SetFilledPolysList(pcbnew.In3_Cu,new);z.SetIsFilled(True);changes.append(dict(zone_uuid=z.m_Uuid.AsString(),exact_removed_native_polygon=removed.Format(False),actual_removed_area_mm2=removed.Area()/1e12))
    assert changes,'Fixture cut must remove actual native filled copper'
    b.BuildConnectivity();return dict(kind=kind,target=target,actual_native_polygons=changes,no_area_filter=True)
case('actual_cleaned_CCK_native_positive')
case('unreviewed_extra_conductor',extra)
case('actual_regulator_source_land_move',source_pad)
case('actual_retained_neighbour_via_move',retained_via)
case('actual_CORE_receiving_annulus_removed',lambda b:physical_cut(b,'annulus'))
case('actual_converter_output_fill_removed',lambda b:physical_cut(b,'output'))
r=dict(passed=all(x['expected_result_observed']for x in rows),native_cases=rows,before_board_sha256=c.sha(B),after_board_sha256=c.sha(A),literal_CORE_checker_sha256=c.sha(Path(c.__file__)),generic_power_checker_sha256=c.sha(c.FROZEN),manufacturing_ready=False,actual_loaded_rail_proof=False)
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'];print(json.dumps(dict(passed=True,cases=len(rows))))
