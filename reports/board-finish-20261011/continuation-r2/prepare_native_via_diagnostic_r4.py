"""Add exact observed native via data before the existing unchanged gates."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=HERE/'native_entry_width_r3.py';new=HERE/'native_entry_diagnostic_r4.py'
    if new.exists():raise ValueError('Fresh diagnostic helper required')
    raw=old.read_text(encoding='utf-8');mark='        annuli=[]\n'
    insertion='''        diagnostic=[]
        for row in expected['added_vias']:
            item=actual.get(row['uuid'])
            if item is None:
                diagnostic.append({'expected':row,'missing':True});continue
            position=item.GetPosition()
            diagnostic.append({'expected':row,'actual_net_raw':str(item.GetNetname()),'actual_nm':[int(position.x),int(position.y)],'actual_mm':[pcbnew.ToMM(position.x),pcbnew.ToMM(position.y)],'actual_diameter_mm':pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)),'actual_drill_mm':pcbnew.ToMM(item.GetDrillValue()),'actual_flashed_layers':[str(board.GetLayerName(layer)) for layer in layer_ids if item.FlashLayer(layer)]})
        diagnostic_output=Path(tool_argv[-1]+'.actual-vias.json')
        diagnostic_output.write_text(json.dumps({'board_sha256':expected['board_sha256'],'rows':diagnostic,'no_fill_or_save':True},indent=1)+'\\n',encoding='utf-8')
'''
    if raw.count(mark)!=1:raise ValueError('Exact pre-gate marker mismatch')
    raw=raw.replace(mark,insertion+mark);new.write_text(raw,encoding='utf-8')
    (HERE/'native-via-diagnostic-derivation-r4.json').write_text(json.dumps({'original':str(old),'original_sha256':sha(old),'derived':str(new),'derived_sha256':sha(new),'changes':['Record each exact native via net,integernm position,size,drill,actualannuli before validation'],'all_original_gate_predicates_unchanged':True,'no_tolerances_waived':True},indent=1)+'\n',encoding='utf-8')
    print(str(new),flush=True)
if __name__=='__main__':main()
