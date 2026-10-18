"""Bounded six-group native route/pose merge onto a newer COPY only."""
from pathlib import Path
import argparse,json,hashlib,shutil,copy,subprocess,collections
import pcbnew
from hardware_build_assembly import parse,dump,child,children,value
from hardware_route_logic_return import identity,pad_identity
ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--donor',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--via-rule',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists()or not a.out.resolve().is_relative_to(ROOT/'reports'):raise ValueError('New report copy only')
    a.out.mkdir(parents=True);digest=sha(a.base);r=json.loads(a.receipt.read_text());assert r['board_sha256']==sha(a.donor)
    b=pcbnew.LoadBoard(str(a.base.resolve()));d=pcbnew.LoadBoard(str(a.donor.resolve()));bf={f.GetReference():f for f in b.GetFootprints()};df={f.GetReference():f for f in d.GetFootprints()}
    scope={x for g in json.loads(a.recipes.read_text())['groups'].values()for x in g};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};allpads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),pad_identity(p))for p in b.GetPads()}
    poses=[];retained_current_NC=[]
    dispositions=json.loads((ROOT/'hardware/motherboard/assembly-map.json').read_text())['native_unused_functional_dispositions_allowed']
    allowed_NC={(v['reference'],v['pin']):v for v in dispositions}
    for ref in sorted(scope):
        f,don=bf[ref],df[ref]
        pp=lambda fp:sorted((p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname(),tuple(p.GetSize()),p.GetShape(),p.GetAttribute())for p in fp.Pads())
        fpins={p.GetNumber():p for p in f.Pads()};dpins={p.GetNumber():p for p in don.Pads()}
        if pp(f)!=pp(don):
            for pin in fpins:
                actual,previous=fpins[pin],dpins[pin]
                if actual.GetNetname()==previous.GetNetname():continue
                reviewed=allowed_NC.get((ref,pin))
                assert reviewed and actual.GetNetname()==reviewed['new_native_net']and previous.GetNetname()==reviewed['old_native_net'],'Unreviewed source pin/net change '+ref+'.'+pin
                assert not any(t.GetNetname()==previous.GetNetname()for t in d.GetTracks()),'Donor routes an obsolete NC endpoint'
                retained_current_NC.append(reviewed)
            assert [v[:2]+v[3:]for v in pp(f)]==[v[:2]+v[3:]for v in pp(don)],'Source pad/land change '+ref
        poses.append(dict(ref=ref,before_mm=[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y),f.GetOrientationDegrees()],after_mm=[pcbnew.ToMM(don.GetPosition().x),pcbnew.ToMM(don.GetPosition().y),don.GetOrientationDegrees()]))
        f.SetPosition(don.GetPosition());f.SetOrientationDegrees(don.GetOrientationDegrees())
    poseboard=a.out/'pose-only.kicad_pcb';pcbnew.SaveBoard(str(poseboard),b)
    t=parse(poseboard.read_text());dt=parse(a.donor.read_text());removed={x['uuid']:x for x in r['exact_removed_private_copper']};added={x['uuid']for x in r['added_copper']};zones={x['uuid']for x in r['added_zones']}
    for uid,row in removed.items():assert uid in old and json.loads(json.dumps(old[uid]))==row['identity'],'Exact retained removal no longer agrees '+uid
    t[:]=[x for x in t if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in removed)]
    donor_nets={item.m_Uuid.AsString():item.GetNetname()for item in list(d.GetTracks())+list(d.Zones())}
    for x in dt:
        if isinstance(x,list)and x and ((x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in added)or(x[0]=='zone'and value(child(x,'uuid')[1])in zones)):
            item=copy.deepcopy(x);uid=value(child(x,'uuid')[1]);net=donor_nets[uid];target_net=b.FindNet(net)
            assert target_net is not None,'Newer board lacks exact reviewed net '+net
            net_row=child(item,'net')
            # KiCad10's current native schema serializes name-only nets; a
            # numeric code here would create a different net named "123".
            if len(net_row)==2 and net_row[1].startswith('"'):net_row[1]=json.dumps(net)
            else:net_row[1]=str(target_net.GetNetCode())
            t.append(item)
    target=a.out/'power-groups-merged-candidate.kicad_pcb';target.write_text(dump(t)+'\n')
    for suffix in ['.kicad_pro','.kicad_dru']:
        if a.base.with_suffix(suffix).exists():shutil.copyfile(a.base.with_suffix(suffix),target.with_suffix(suffix))
    for resource in a.base.parent.iterdir():
        if resource.is_dir()and(resource.suffix=='.pretty'or resource.name=='3dmodels'):shutil.copytree(resource,a.out/resource.name)
        elif resource.name=='fp-lib-table':shutil.copyfile(resource,a.out/resource.name)
    adopted_via_rule=None
    if a.via_rule:
        vr=json.loads(a.via_rule.read_text());actual={v.m_Uuid.AsString():v for v in d.GetTracks()}
        if len(vr['exact_vias'])!=4 or vr['advanced_factory_dfm_confirmed']:raise ValueError('Exact four unqualified factory escape records required')
        conditions=[]
        for row in vr['exact_vias']:
            uid=row['uuid'];via=actual[uid]
            if uid not in added or json.loads(json.dumps(identity(via)))!=row['identity']or row['diameter_mm']!=.4 or row['drill_mm']!=.2:
                raise ValueError('Exact reviewed advanced escape geometry differs '+uid)
            x,y=row['position_mm'];net=row['net']
            conditions.append(f"(A.NetName == '{net}' && A.Position_X == {x:.6f}mm && A.Position_Y == {y:.6f}mm)")
        text='\n# Four exact low-current control escapes only; PCBWay advanced DFM/price pending.\n(rule "Four exact converter control escapes"\n  (condition "A.Type == \'Via\' && ('+' || '.join(conditions)+')")\n  (constraint via_diameter (min 0.40mm) (max 0.40mm))\n  (constraint hole_size (min 0.20mm) (max 0.20mm))\n  (constraint annular_width (min 0.10mm)))\n'
        rules=target.with_suffix('.kicad_dru');rules.write_text(rules.read_text()+text)
        adopted_via_rule=dict(source_sha256=sha(a.via_rule),exact_vias=vr['exact_vias'],exact_position_net_rule=text,advanced_factory_dfm_confirmed=False,original_target_rules_retained=True)
    run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(a.out/'drc.json'),str(target)],capture_output=True,text=True,encoding='utf-8',errors='replace');(a.out/'drc.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
    drc=json.loads((a.out/'drc.json').read_text());assert not drc.get('ignored_checks')
    final=pcbnew.LoadBoard(str(target));final.BuildConnectivity();after={x.m_Uuid.AsString():identity(x)for x in final.GetTracks()}
    assert all(after.get(uid)==v for uid,v in old.items()if uid not in removed),'Unrelated copper changed'
    assert all(after[uid][1]==donor_nets[uid]for uid in added),'Added copper net name changed during native merge'
    for p in final.GetPads():
        ref,ident=allpads[p.m_Uuid.AsString()]
        if ref not in scope:assert pad_identity(p)==ident,'Unrelated fitted pad changed'
    assert sha(a.base)==digest
    receipt=dict(source_board=str(a.base),source_hash=digest,source_unchanged=True,donor_hash=sha(a.donor),poses=poses,current_reviewed_NC_preserved=retained_current_NC,removed_old_copper=len(removed),exact_removed_old_copper=sorted(removed),new_copper=len(added),exact_added_copper=sorted(added),new_zones=len(zones),exact_added_zones=sorted(zones),adopted_via_rule=adopted_via_rule,all_unrelated_copper_and_pads_preserved=True,native_drc_types=dict(collections.Counter(x['type']for x in drc['violations'])),native_uncapped_unconnected=final.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,board_hash=sha(target))
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='poses'}))
if __name__=='__main__':main()
