"""Wire exact source-grounded CMOS inputs to their own device ground pin.

Only static, SOURCE-declared input-to-ground ties on the same fitted package
are eligible. No output, supply distribution, capacitor, field circuit, new
via, source assignment, placement, or existing copper is changed. These local
ties do not qualify the still incomplete system ground distribution.
"""
from pathlib import Path
import argparse,json,math,shutil,subprocess,sys
import pcbnew
from hardware_build_ordinary_route_manifest import native,ROOT
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_owned_bypass_loops_wip_r03 import Geometry,reviewed_wip_warnings,new_route_defects
from hardware_route_logic_return import identity,xy,mm,segment_hits_box,segment_distance
from hardware_route_local_signals import paths
from hardware_anchor_owned_cmos_returns import source_clusters
from hardware_route_critical_digital_wip_r03 import clusters_preserved
from hardware_route_selected_additive_r02 import native_source_check
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
PREFIXES=('SN74','74LVC','74AHCT','TCA9517','TCA9534','TPS3808','TPS3839','TPS3851','TPS3700','TPS3702','LTC2962','LTC6994','W25Q32')


def source_rows(model,netlist):
    nodes,nets,functions=native(model,netlist);rows=[]
    for ref,part in model['components'].items():
        if not part.get('mpn','').startswith(PREFIXES):continue
        grounds=[pin for (r,pin),net in nodes.items() if r==ref and net=='/LOGIC_GND'
                 and functions[r][pin]['type']=='power_in' and functions[r][pin]['name'] in ('GND','VSS','EP')]
        if not grounds:continue
        for (r,pin),net in nodes.items():
            if r==ref and net=='/LOGIC_GND' and functions[r][pin]['type']=='input':
                rows.append(dict(reference=ref,input_pin=pin,ground_pins=grounds,MPN=part['mpn'],source_pin_function=functions[r][pin]))
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('board','source','adoption','map','baseline-disposition','out'):
        ap.add_argument('--'+key,dest=key.replace('-','_'),type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    accepted=json.loads(a.adoption.read_text());assert accepted['passed'] and accepted['adopted'] and accepted['independent_validation_pass']
    for name,h in accepted['source_hashes'].items():
        p=Path(name);p=p if p.is_absolute() else a.source/p
        if sha(p)!=h:raise ValueError('Frozen adopted source changed: '+str(p))
    model=json.loads((a.source/'design.json').read_text());rows=source_rows(model,a.source/'netlist.xml')
    mapping=json.loads(a.map.read_text());assert not mapping['errors'] and mapping['source_physical_population_complete']
    base_report=json.loads((a.board.parent/'drc.json').read_text())
    known=reviewed_wip_warnings(base_report,json.loads(a.baseline_disposition.read_text()),sha(a.board))
    frozen={str(p.resolve()):sha(p)for p in (a.board,a.source/'design.json',a.source/'netlist.xml',a.map,a.baseline_disposition,Path(__file__))}
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();native_source_check(b,model,a.source/'netlist.xml')
    prior=source_clusters(b);old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
    pads={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()}
    physical={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
    domain={p['net']:p['domain']for p in mapping['pads']}
    # Preserve .6mm functional spacing to actual foreign same-side source
    # copper; ordinary LOGIC and its unused NC package lands use native rules.
    foreign_pads=[p for p in mapping['pads']if p['domain'] not in ('LOGIC','NC')]
    foreign_tracks=[t for t in b.GetTracks()if domain.get(t.GetNetname(),'LOGIC')not in ('LOGIC','NC')]
    geometry=Geometry(b);groups=[];blocked=[];already=[];alive=[]
    def foreign_clear(points,layer):
        name=b.GetLayerName(layer)
        for s,e in zip(points,points[1:]):
            if any(name in p['copper_layers'] and segment_hits_box(s,e,p['copper_aabb_mm'],.7)for p in foreign_pads):return False
            for t in foreign_tracks:
                if not t.IsOnLayer(layer):continue
                w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
                if segment_distance(s,e,mm(t.GetStart()),mm(t.GetEnd()))<.7+w/2-1e-6:return False
        return True
    for row in rows:
        p=physical[row['reference'],row['input_pin']];targets=[physical[row['reference'],pin]for pin in row['ground_pins']]
        assert p.GetNetname()=='/LOGIC_GND' and all(q.GetNetname()==p.GetNetname()for q in targets)
        b.BuildConnectivity();peers={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}
        if any(q.m_Uuid.AsString()in peers for q in targets):already.append(row);continue
        layer=p.GetParentFootprint().GetLayer();assert layer in (pcbnew.F_Cu,pcbnew.B_Cu)
        chosen=None
        for q in sorted(targets,key=lambda q:math.dist(mm(p.GetPosition()),mm(q.GetPosition()))):
            for route in paths(mm(p.GetPosition()),mm(q.GetPosition())):
                length=sum(math.dist(s,e)for s,e in zip(route,route[1:]))
                if length<=20 and geometry.clear(route,'/LOGIC_GND',layer,width=.20)and foreign_clear(route,layer):chosen=(q,route,length);break
            if chosen:break
        if not chosen:blocked.append(row);continue
        q,route,length=chosen;items=[]
        for s,e in zip(route,route[1:]):
            if math.dist(s,e)<1e-8:continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(p.GetNet());t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(.20));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);geometry.add(t);items.append(t)
        alive.extend(items);groups.append(dict(**row,target_ground_pin=q.GetNumber(),length_mm=length,new_UUIDs=[t.m_Uuid.AsString()for t in items],retained=True))
    a.out.mkdir(parents=True);dest=a.out/'local-CMOS-ground-ties-candidate.kicad_pcb'
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
    for item in a.board.parent.iterdir():
        if item.is_dir()and(item.suffix=='.pretty'or item.name=='3dmodels'):shutil.copytree(item,a.out/item.name)
        elif item.name=='fp-lib-table':shutil.copyfile(item,a.out/item.name)
    owners={u:i for i,g in enumerate(groups)for u in g['new_UUIDs']}
    for attempt in range(8):
        pcbnew.SaveBoard(str(dest),b);out=a.out/('native-'+str(attempt)+'.json')
        run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out),str(dest)],capture_output=True,text=True)
        (a.out/('native-'+str(attempt)+'.txt')).write_text(run.stdout+run.stderr);assert run.returncode==0
        report=json.loads(out.read_text());bad=set()
        for issue in new_route_defects(report,known):
            found={owners[v['uuid']]for v in issue['items']if v['uuid']in owners}
            if not found:raise ValueError('New defect outside literal added ground ties')
            bad|=found
        if not bad:break
        for i in bad:
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString()in groups[i]['new_UUIDs']:b.Remove(t)
            groups[i]['retained']=False
    else:raise ValueError('Native local-tie correction bound exceeded')
    actual=pcbnew.LoadBoard(str(dest));actual.BuildConnectivity();new={t.m_Uuid.AsString():identity(t)for t in actual.GetTracks()}
    added={u for g in groups if g['retained']for u in g['new_UUIDs']}
    assert set(new)==set(old)|added and all(new[u]==v for u,v in old.items())
    assert pads=={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in actual.GetPads()}
    actual_pads={(f.GetReference(),p.GetNumber()):p for f in actual.GetFootprints()for p in f.Pads()if p.GetNumber()}
    for group in groups:
        if not group['retained']:continue
        p=actual_pads[group['reference'],group['input_pin']];q=actual_pads[group['reference'],group['target_ground_pin']]
        assert q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in actual.GetConnectivity().GetConnectedItems(p)}
    cluster_proof=clusters_preserved(prior,actual);native_source_check(actual,model,a.source/'netlist.xml')
    assert all(sha(Path(p))==h for p,h in frozen.items())
    scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Static source-grounded CMOS inputs to the actual same-device GND pin; .20mm same-side copper≤20mm, no vias, no supply/output/field routing.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(added),reviewed_added_zone_UUIDs=[])
    write(a.out/'bounded-scope.json',scope)
    result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_source_review=rows,groups=groups,already_connected=already,blocked_required_ties=blocked,
        retained_groups=sum(g['retained']for g in groups),new_copper_count=len(added),new_vias=0,prior_source_cluster_proof=cluster_proof,
        native_errors=0,remaining_native_warnings=report['violations'],ignored_checks=[],native_uncapped_joins=actual.GetConnectivity().GetUnconnectedCount(False),
        same_device_actual_GND_pin_connectivity_checked=True,global_ground_distribution_or_physical_immunity_qualified=False,manufacturing_ready=False)
    write(a.out/'receipt.json',result);print(dict(new_groups=result['retained_groups'],new_Cu=len(added),missing=result['native_uncapped_joins']))
if __name__=='__main__':main()
