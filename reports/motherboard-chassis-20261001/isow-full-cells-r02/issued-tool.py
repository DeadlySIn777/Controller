"""Apply two reviewed complete ISOW cells to a native PCB COPY only.

Exact changed pads/lands remain identical. Bounded old private attached copper
is recorded; unrelated copper is retained. Native rules exclude global pours
from each converter output corridor and the actual isolation centreline.
"""
import argparse,collections,json,shutil,subprocess
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,segment_hit
from hardware_isow_layout_recipe import notch,lands,vec
from hardware_route_logic_return import identity,distance
from hardware_build_assembly import parse,dump,children,child,value

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def poly(points):
    a=p.SHAPE_POLY_SET();a.NewOutline()
    for x,y in points:a.Append(p.FromMM(x),p.FromMM(y))
    return a
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();out=a.out.resolve();assert not out.exists();out.mkdir(parents=True)
    search=ROOT/'reports/motherboard-chassis-20261001/isow-full-cell-search-r03/review.json';s=json.loads(search.read_text());base=Path(next(q for q in s['input_hashes']if q.endswith('motherboard-local-capacitors-candidate.kicad_pcb')))
    fixture=ROOT/'reports/motherboard-chassis-20261001/isow-layout-fixture-r05/isow-layout-fixture.kicad_pcb';fr=fixture.with_name('receipt.json');frec=json.loads(fr.read_text());assert frec['native_DRC_regular_violations']==0 and not frec['native_DRC_ignored_checks']
    inputs={str(q):sha(q)for q in[base,fixture,fr,search,base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru'),Path(__file__)]};assert all(sha(Path(q))==h for q,h in s['input_hashes'].items())
    b=p.LoadBoard(str(base));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};owned=set(frec['fixture_poses']);oldlands={r:lands(f)for r,f in fps.items()};oldposes={r:[*xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]for r,f in fps.items()};oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};tracks=list(b.GetTracks());removed={}
    raw={z.GetNetname()for ref in ['U14812','U14813']for z in fps[ref].Pads()if z.GetNumber()in['11','12','13']}
    # Every raw-domain copper piece belongs exclusively to this owned cell.
    for net in raw:
        actual={z.GetParentFootprint().GetReference()for z in b.GetPads()if z.GetNetname()==net};assert actual<=owned,(net,actual-owned)
    movingpads=[z for r in owned for z in fps[r].Pads()]
    doomed=set()
    for t in tracks:
        uid=t.m_Uuid.AsString()
        if t.GetNetname()in raw:doomed.add(uid);removed[uid]=dict(before=oldcu[uid],reason='Entire exact source-owned raw converter net invalidated by whole-cell relocation.');continue
        if isinstance(t,p.PCB_VIA):continue
        if any(z.GetNetname()==t.GetNetname()and(z.HitTest(t.GetStart())or z.HitTest(t.GetEnd()))for z in movingpads):
            doomed.add(uid);removed[uid]=dict(before=oldcu[uid],reason='Exact old track has a terminal endpoint on a relocated cell pad; not stretched across foreign copper.')
    # Prune only newly detached leaf tails from the exact initial changed Cu.
    active={t.m_Uuid.AsString():t for t in tracks if t.m_Uuid.AsString()not in doomed};frontier={tuple(t.GetEnd())for t in tracks if t.m_Uuid.AsString()in doomed}|{tuple(t.GetStart())for t in tracks if t.m_Uuid.AsString()in doomed}
    fixedpads=[z for r,f in fps.items()if r not in owned for z in f.Pads()]
    while frontier:
        point=frontier.pop();pv=p.VECTOR2I(*point)
        if any(z.HitTest(pv)for z in fixedpads):continue
        touching=[]
        for uid,t in active.items():
            if isinstance(t,p.PCB_VIA):
                if tuple(t.GetPosition())==point:touching.append((uid,t))
            elif distance(xy(pv),xy(t.GetStart()),xy(t.GetEnd()))<1e-6:touching.append((uid,t))
        wire=[(uid,t)for uid,t in touching if not isinstance(t,p.PCB_VIA)]
        if len(wire)>1:continue
        if len(wire)==1:
            uid,t=wire[0]
            if point not in[tuple(t.GetStart()),tuple(t.GetEnd())]:continue
        for uid,t in touching:
            doomed.add(uid);removed[uid]=dict(before=oldcu[uid],reason='Exact newly detached private leaf tail pruned only to a surviving native branch junction or fixed pad.');active.pop(uid)
            frontier.update([tuple(t.GetStart()),tuple(t.GetEnd())])
    # Filter exact native Cu UUIDs without SWIG ownership deletion surprises.
    tree=parse(base.read_text());assert len(doomed)==len(removed)
    for q in list(tree):
        if isinstance(q,list)and q[0]in['segment','arc','via']and value(child(q,'uuid')[1])in doomed:tree.remove(q)
    filtered=out/'filtered-old-native.kicad_pcb';filtered.write_text(dump(tree)+'\n');b=p.LoadBoard(str(filtered));fps={f.GetReference():f for f in b.GetFootprints()}
    origins={z['IC']:z['origin_mm']for z in s['whole_cell_candidates']};poses={}
    for recipe in frec['recipes']:
        ic=next(r for r in recipe if r in origins);ox,oy=origins[ic]
        for ref,(x,y,angle)in recipe.items():
            f=fps[ref];f.SetOrientationDegrees(angle);f.SetPosition(vec((ox+x,oy+y)));poses[ref]=[ox+x,oy+y,angle]
        notch(fps[ic])
    # All graphical source libraries remain read-only; carry project copies.
    for q in base.parent.iterdir():
        if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,out/q.name)
    shutil.copyfile(base.parent/'fp-lib-table',out/'fp-lib-table');shutil.copyfile(fixture.parent/'CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod',out/'CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod')
    fb=p.LoadBoard(str(fixture));added=[]
    for t in fb.GetTracks():
        ic='U14812'if t.GetStart().x<p.FromMM(60)else'U14813';fo=(40,40)if ic=='U14812'else(80,40);to=origins[ic];delta=vec((to[0]-fo[0],to[1]-fo[1]));z=p.PCB_VIA(b)if isinstance(t,p.PCB_VIA)else p.PCB_TRACK(b)
        if isinstance(z,p.PCB_VIA):
            z.SetPosition(t.GetPosition()+delta);z.SetWidth(t.GetWidth(p.F_Cu));z.SetDrill(t.GetDrillValue());z.SetViaType(t.GetViaType());z.SetLayerPair(t.TopLayer(),t.BottomLayer())
        else:
            z.SetStart(t.GetStart()+delta);z.SetEnd(t.GetEnd()+delta);z.SetWidth(t.GetWidth());z.SetLayer(t.GetLayer())
        z.SetNet(b.FindNet(t.GetNetname()));b.Add(z);added.append(identity(z))
    areas=[];layers=[n for n in range(64)if p.IsCopperLayer(n)and b.IsLayerEnabled(n)]
    for ic,(ox,oy)in origins.items():
        rawpoly=[(3.2,2.6),(7.0,2.6),(7.0,.55),(13.5,.55),(13.5,10.2),(3.2,10.2)]
        for name,pts,blocktracks in[(ic+'_RAW_CONVERTER_POUR_EXCLUSION',rawpoly,False),(ic+'_FUNCTIONAL_ISOLATION_BARRIER',[(-.6,-7),(.6,-7),(.6,7),(-.6,7)],True)]:
            pts=[(ox+x,oy+y)for x,y in pts];zone=p.ZONE(b);mask=p.LSET()
            for layer in layers:mask.AddLayer(layer)
            zone.SetLayerSet(mask);zone.SetIsRuleArea(True);zone.SetZoneName(name);zone.SetDoNotAllowZoneFills(True);zone.SetDoNotAllowTracks(blocktracks);zone.SetDoNotAllowVias(blocktracks);zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False);zone.Outline().Append(poly(pts));b.Add(zone);areas.append(dict(name=name,polygon_mm=pts,all_Cu_layers=layers,tracks_and_vias_blocked=blocktracks))
    p.ZONE_FILLER(b).Fill(b.Zones());dest=out/'motherboard-isow-cell-candidate.kicad_pcb';p.SaveBoard(str(dest),b)
    for suffix in['.kicad_pro','.kicad_dru']:shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    fresh=p.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()};newcu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    assert oldlands=={r:lands(f)for r,f in nf.items()}
    assert all(oldposes[r]==[*xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]for r,f in nf.items()if r not in owned)
    assert all(newcu.get(uid)==record for uid,record in oldcu.items()if uid not in doomed)
    route=[]
    for r in frec['route_ledger']:
        one,two=r['a'],r['z'];pp=next(z for z in nf[one[0]].Pads()if z.GetNumber()==one[1]);gg=next(z for z in nf[two[0]].Pads()if z.GetNumber()==two[1]);cluster={z.m_Uuid.AsString()for z in fresh.GetConnectivity().GetConnectedItems(pp)if z.Type()==p.PCB_PAD_T};route.append(dict(a=one,z=two,actual_connected=gg.m_Uuid.AsString()in cluster))
    assert all(z['actual_connected']for z in route)
    cmd=[str(CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(out/'drc.json'),str(dest)];run=subprocess.run(cmd,capture_output=True,text=True);(out/'drc-command.txt').write_text(run.stdout+run.stderr);drc=json.loads((out/'drc.json').read_text())
    assert inputs=={q:sha(Path(q))for q in inputs}
    result=dict(input_hashes=inputs,board_sha256=sha(dest),exact_changed_poses={r:dict(before=oldposes[r],after=poses[r])for r in owned},removed_old_private_copper=removed,added_native_local_copper=added,all_other_native_footprints_and_existing_copper_preserved=True,all_lands_pin_nets_paste_mask_unchanged=True,project_courtyard_only_override=True,rule_areas=areas,local_route_receipt=route,physical_parts=len(nf),native_Cu_count=len(newcu),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),native_DRC_regular=len(drc['violations']),native_DRC_ignored=drc.get('ignored_checks',[]),source_modified=False,PCB_parent_modified=False,manufacturing_ready=False)
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,out/'issued-tool.py');print(json.dumps({k:v for k,v in result.items()if k not in['input_hashes','exact_changed_poses','removed_old_private_copper','added_native_local_copper','rule_areas','local_route_receipt']}))
    assert not drc['violations']and not drc.get('ignored_checks')
if __name__=='__main__':main()
