"""The real OUT9 native piece must fail when its five new Ground objects are cut."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_validate_motherboard_return_planes_r06 import validate
folder=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-review-r02')
nativefolder=folder.parent/'source26-r74-OUT9-external-ground-transfer-r01'
source=nativefolder/'motherboard-OUT9-external-ground-transfer-candidate.kicad_pcb'
generation=json.loads((nativefolder/'generation.json').read_text());cut=folder/'actual-OUT9-Ground-cut.kicad_pcb';frozen=sha(source)
if len(sys.argv)>1:
    if sys.argv[1]=='make':
        if cut.exists():raise ValueError('Fresh actual cut file required')
        b=pcbnew.LoadBoard(str(source));removed=[]
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString()in generation['new_ground_Cu_UUIDs']:
                removed.append(t.m_Uuid.AsString());b.Remove(t)
        if len(removed)!=5:raise ValueError('Actual five-object Ground cut incomplete')
        pcbnew.SaveBoard(str(cut),b)
    elif sys.argv[1]=='check':
        b=pcbnew.LoadBoard(str(cut));b.BuildConnectivity()
        mapping=json.loads(Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json').read_text())
        report=validate(b,mapping)
        failed=[r for r in report['unanchored_components']if r['literal_native_positive_metal_provenance']['zone_uuid']=='70779225-3f58-41c9-9ef5-f15169383fc2']
        if not failed:raise ValueError('Actual Ground transfer removal did not reject literal SOURCE-bearing OUT9 piece')
        write(folder/'actual-native-Ground-cut-proof.json',dict(passed=True,board_sha256=frozen,cut_board_sha256=sha(cut),actual_removed_UUIDs=generation['new_ground_Cu_UUIDs'],literal_OUT9_native_physical_piece_source_failure=failed,source_or_successful_candidate_mutated=False))
    else:raise ValueError('Exact mode required')
else:
    for mode in('make','check'):
        r=subprocess.run([sys.executable,str(Path(__file__)),mode],capture_output=True,text=True)
        (folder/('actual-native-Ground-cut-'+mode+'-command.txt')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('Actual native cut control failed: '+mode)
    if sha(source)!=frozen:raise ValueError('Successful candidate changed')
    print('Actual literal OUT9 SOURCE loss after physical Ground cut proved',flush=True)
