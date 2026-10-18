"""Process-isolated actual native ADC cuts; successful candidate stays frozen."""
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck

root=Path('reports/motherboard-return-zoning-20261001/source26-r74-C19042-coupled-source-cell-r05')
folder=root/'physical-controls-r02'
source=root/'motherboard-C19042-source-cell-candidate.kicad_pcb'
generation=json.loads((root/'generation.json').read_text())
power='/motherboard_do/DOB_FIELD_3V3';ground='/motherboard_do/FIELD_B_0V'
frozen=sha(source)

if len(sys.argv)>1:
    mode=sys.argv[1];name=sys.argv[2]
    filename=folder/(name+'.kicad_pcb')
    if mode=='make':
        b=pcbnew.LoadBoard(str(source));removed=[]
        if name=='reference':
            for z in list(b.Zones()):
                if z.m_Uuid.AsString() in generation['new_zone_UUIDs']:
                    removed.append(z.m_Uuid.AsString());b.Remove(z)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        else:
            net=power if name=='supply' else ground
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in generation['new_Cu'] and t.GetNetname()==net:
                    removed.append(t.m_Uuid.AsString());b.Remove(t)
        if not removed:raise ValueError('Actual cut empty')
        pcbnew.SaveBoard(str(filename),b)
        write(folder/(name+'-cut.json'),dict(actual_removed_UUIDs=removed,cut_board_sha256=sha(filename)))
    elif mode=='check':
        b=pcbnew.LoadBoard(str(filename));b.BuildConnectivity()
        cut=json.loads((folder/(name+'-cut.json')).read_text())
        if name=='reference':
            declaration=dict(return_net=ground,reference_layers={'F.Cu':'In1.Cu'},allow_vias=False,reference_corridor_margin_mm=.4)
            checker=NativeCollectedAnnulusCheck(b,{power:declaration});rejected=[]
            for t in b.GetTracks():
                if t.m_Uuid.AsString() in generation['new_Cu'] and t.GetNetname()==power:
                    try:checker.segment(t,declaration)
                    except ValueError as error:rejected.append(dict(uuid=t.m_Uuid.AsString(),reason=str(error)))
            if not rejected:raise ValueError('Absent own reference failed to reject')
            proof=dict(actual_reference_rejections=rejected,native_refill_performed=True)
        else:
            pins={ (p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()}
            a=('C19042','1' if name=='supply' else '2');q=('U19026','8' if name=='supply' else '3')
            if pins[q].m_Uuid.AsString() in {t.m_Uuid.AsString() for t in b.GetConnectivity().GetConnectedItems(pins[a])}:
                raise ValueError('Actual physical Source pair cut failed to reject')
            proof=dict(actual_native_Source_pair_rejected=True,endpoints=[list(a),list(q)])
        write(folder/(name+'-proof.json'),dict(passed=True,case=name,**cut,**proof))
    else:raise ValueError('Exact control mode required')
else:
    if folder.exists():raise ValueError('Fresh immutable control folder required')
    folder.mkdir()
    for name in ('supply','ground','reference'):
        for mode in ('make','check'):
            result=subprocess.run([sys.executable,str(Path(__file__)),mode,name],capture_output=True,text=True)
            (folder/(name+'-'+mode+'-command.txt')).write_text(result.stdout+result.stderr)
            if result.returncode:raise ValueError('Native control failed: '+name+' '+mode)
    if sha(source)!=frozen:raise ValueError('Successful candidate changed')
    write(folder/'review.json',dict(passed=True,board_sha256=frozen,
          actual_native_negative_controls=[json.loads((folder/(n+'-proof.json')).read_text())for n in('supply','ground','reference')],
          source_or_candidate_mutated=False,manufacturing_ready=False))
    print('Three process-isolated native ADC cuts passed',flush=True)
