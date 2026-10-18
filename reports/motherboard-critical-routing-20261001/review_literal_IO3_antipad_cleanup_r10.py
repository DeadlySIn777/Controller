"""Actual physical cleanup review, independent of the later clock-route proof."""
from pathlib import Path
import sys,json,types
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as c
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
P=Path(__file__).parent;B=P/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';A=P/'CCK-literal-IO3-collar-baseline-r09/motherboard-IO3-antipad-collar-candidate.kicad_pcb';O=P/'CCK-IO3-literal-cleanup-native-review-r10';O.mkdir(exist_ok=False)
before,after=pcbnew.LoadBoard(str(B)),pcbnew.LoadBoard(str(A));before.BuildConnectivity();after.BuildConnectivity();pre=json.loads((P/'CCK-IO3-antipad-cleanup-preflight-r09/review.json').read_text());prop=json.loads((A.parent/'proposal.json').read_text());drc=json.loads((A.parent/'native.json').read_text());f=c.f
assert not drc['violations']and not drc['ignored_checks'];assert prop['input_board_sha256']==c.sha(B)and c.sha(c.SOURCE)==pre['source_sha256'];region=f.box(*pre['literal_bounds_mm']);rule_uid=prop['literal_rule_uuid']
bc={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};ac={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};assert bc==ac
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
bz,az=definitions(B),definitions(A);assert set(az)==set(bz)|{rule_uid}and all(az[u]==z for u,z in bz.items());rule=next(z for z in after.Zones()if z.m_Uuid.AsString()==rule_uid)
assert rule.GetIsRuleArea()and list(rule.GetLayerSet().Seq())==[pcbnew.In2_Cu]and rule.GetDoNotAllowZoneFills()and not any((rule.GetDoNotAllowTracks(),rule.GetDoNotAllowVias(),rule.GetDoNotAllowPads(),rule.GetDoNotAllowFootprints()))and f.symmetric_equal(rule.Outline(),region)
def actual_cleanup_geometry(b,a):
    def ownership(old,new):
        pieces=list(split_polygons(new));rows=[]
        for i,p in enumerate(split_polygons(old)):
            owners=[j for j,q in enumerate(pieces)if f.intersection(p,q).OutlineCount()]
            assert len(owners)==1,'Actual power core or full component split/disappeared';rows.append(dict(before=i,after=owners[0]))
        return rows
    assert b.OutlineCount()and a.OutlineCount();full=ownership(b,a);be,ae=f.duplicate(b),f.duplicate(a)
    for x in(be,ae):x.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
    assert be.OutlineCount()and ae.OutlineCount();cores=ownership(be,ae)
    opened=f.duplicate(be);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(b);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
    thin=f.subtract(b,opened);precision=f.duplicate(a);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
    definite_removed=f.subtract(b,precision);definite_thin_lost=f.subtract(thin,precision);outside=f.subtract(definite_removed,region);thin_outside=f.subtract(definite_thin_lost,region)
    assert not outside.OutlineCount(),'Real removed IO3 copper beyond literal physical cleanup';assert not thin_outside.OutlineCount(),'Definite old thin feature removed outside exact physical correction'
    assert not f.intersection(a,region).OutlineCount(),'Literal native rule area still contains IO3 copper'
    removed=f.subtract(b,a);nominal_outside=f.subtract(removed,region)
    return dict(passed=True,actual_full_component_ownership=full,actual_502um_core_ownership=cores,minimum_backbone_screen_mm=1.,native_comparison_precision_um=1.,actual_physical_correction_bounds_mm=pre['literal_bounds_mm'],all_definite_old_thin_features_outside_exact_physical_correction_retained=True,exact_actual_removed_native_polygon=removed.Format(False),actual_removed_mm2=removed.Area()/1e12,actual_nominal_outside_delta_polygon=nominal_outside.Format(False),actual_nominal_outside_delta_mm2=nominal_outside.Area()/1e12,no_area_based_exemptions=True,physical_rule_area_fill_absent=True,ampacity_IRdrop_thermal_unqualified=True)
text=c.FROZEN.read_text();old=' geometry=backbone(b,a)';assert text.count(old)==1;text=text.replace(old,' geometry=exact_actual_cleanup_geometry(b,a)');mod=types.ModuleType('literal_IO3_cleanup_r10');mod.__file__=str(c.FROZEN.resolve());mod.exact_actual_cleanup_geometry=actual_cleanup_geometry;exec(compile(text,str(c.FROZEN),'exec'),mod.__dict__)
try:
    proof=mod.review(before,after);error=None
except Exception as ex:proof=dict(passed=False);error=str(ex)
padrows=[];bp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in before.GetPads()};ap={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in after.GetPads()};s0,s1=bp['R18001','2'],ap['R18001','2']
def connected(b,p,q):return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
for k,p in bp.items():
    if p.GetNetname()!='/IO_3V3':continue
    old,new=connected(before,s0,p),connected(after,s1,ap[k]);assert not old or new
    padrows.append(dict(reference=k[0],pin=k[1],old_actual_source_connected=old,new_actual_source_connected=new))
nets={p.GetNetname()for p in before.GetPads()if p.GetNumber()};assert clusters_survive(native_pad_clusters(before,nets),native_pad_clusters(after,nets))
r=dict(passed=proof['passed'],error=error,before_board_sha256=c.sha(B),after_board_sha256=c.sha(A),literal_rule_uuid=rule_uid,literal_In2_bounds_mm=pre['literal_bounds_mm'],source_sha256=c.sha(c.SOURCE),preflight_sha256=c.sha(P/'CCK-IO3-antipad-cleanup-preflight-r09/review.json'),frozen_power_guard_sha256=c.sha(c.FROZEN),actual_same_IO3_guard_body_except_separate_physical_cleanup_geometry=True,actual_power_proof=proof,actual_all601_IO3_source_pad_status=padrows,all_old_native_Cu_lands_poses_zone_defs_preserved=True,all_actual_old_Source_clusters_retained=True,native_errors=0,native_warnings=0,no_ignored_checks=True,original_CCK_guard_failure_preserved=True,later_CCK_vs_cleaned_baseline_still_requires_unchanged_r07_IO3_body=True,adopted=False,manufacturing_ready=False)
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],error=error,actual_IO3_pads=len(padrows))));assert r['passed']
