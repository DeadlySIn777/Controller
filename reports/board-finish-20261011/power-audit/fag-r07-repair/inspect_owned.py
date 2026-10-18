"""Read-only exact FAG donor/r07 source geometry inventory; no native or board output."""
from pathlib import Path
import hashlib
import json
import math
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPORT=HERE.parent.parent
sys.path.insert(0,str(REPORT/'recovery-composite/c06/alternate-r07'))
import screen_r07 as R
S=R.S
DONOR=REPORT/'power-audit/fag-r06/candidate/board.kicad_pcb'
SCREEN=REPORT/'power-audit/fag-r07-screen/screen.json'
NET='/motherboard_motors/FIELD_GND'

def own_additions():
    screen=json.loads(S.read(SCREEN))
    raw=S.read(DONOR)
    if hashlib.sha256(raw).hexdigest()!=screen['donor_sha256']:raise ValueError('donor differs')
    base=R.composition.inventory(S.read(S.overlay_tool.base.BASE))
    donor=R.composition.inventory(raw)
    if any(donor[4].get(u)!=ch for u,ch in base[4].items()):raise ValueError('original copper not preserved')
    items={u:ch for u,ch in donor[4].items() if u not in base[4]}
    if len(items)!=261:raise ValueError('unexpected donor count')
    rows={}
    for uid,ch in items.items():
        net=S.norm(S.overlay_tool.netname(ch))
        if net!=NET:raise ValueError('unexpected donor net')
        kind=R.composition.pcbtext.chunk_kind(ch)
        row={'uuid':uid,'kind':kind,'net':net,'chunk_sha256':hashlib.sha256(ch).hexdigest()}
        if kind=='via':
            row.update(at=S.overlay_tool.numbers(ch,'at'),d=S.overlay_tool.scalar(ch,'size'),drill=S.overlay_tool.scalar(ch,'drill'),span=['F.Cu','B.Cu'])
        else:
            row.update(a=S.overlay_tool.numbers(ch,'start'),b=S.overlay_tool.numbers(ch,'end'),width=S.overlay_tool.scalar(ch,'width'),layer=R.composition.pcbtext.chunk_layer(ch))
        rows[uid]=row
    return rows,screen

def main():
    rows,screen=own_additions();g,_,overlay=R.overlay_and_targets()
    vias={v['uuid']:v for v in g['vias']};tracks={t['uuid']:t for t in g['tracks']}
    results=[]
    for failure in screen['rows']:
        if not failure['failures']:continue
        row=dict(rows[failure['uuid']]);row['screen_failures']=failure['failures']
        if row['kind']=='via':
            nearby=sorted((math.dist(row['at'],(v['x'],v['y'])),v) for v in g['vias'] if math.dist(row['at'],(v['x'],v['y']))<1.5)
            row['nearby_retained_vias']=[dict(v,distance_mm=dist,exact_same_net=S.norm(v['net'])==NET) for dist,v in nearby]
            row['own_touching_segments']=[r for r in rows.values() if r['kind']=='segment' and (math.dist(r['a'],row['at'])<1e-6 or math.dist(r['b'],row['at'])<1e-6)]
        else:
            row['retained_blockers']=[tracks[f['uuid']] if f.get('uuid') in tracks else vias.get(f.get('uuid')) for f in failure['failures']]
        results.append(row)
    for path,expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('input changed')
    out={'scope':'partial96mA FIELD_A return; exact current r07 retained copper/source only','board_sha256':R.R07_SHA,
         'donor_sha256':screen['donor_sha256'],'owned_items':rows,'blocked_items':results,'overlay':overlay,'read_set':S.READS,
         'native_jobs':0,'GPU_jobs':0,'board_emitted':False}
    (HERE/'owned-inventory.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'owned_items':len(rows),'blocked_items':len(results),'via_observations':[{'uuid':r['uuid'],'at':r['at'],'nearby':[{'uuid':v['uuid'],'net':v['net'],'same_net':v['exact_same_net'],'d':v['d'],'drill':v['drill'],'at':[v['x'],v['y']],'distance_mm':v['distance_mm']} for v in r['nearby_retained_vias']]} for r in results if r['kind']=='via'],'segments':[r for r in results if r['kind']=='segment']},indent=1))

if __name__=='__main__':main()
