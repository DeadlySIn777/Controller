"""Create distinct 0.5/0.2 screens; frozen 0.6/0.3 files stay untouched."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

STRICT_FUNCTION='''\n\ndef strict_via_free(model,target,window):
    net=S.norm(target['net']); domain=target['domain']; blockers=[]; classes={}
    radius=.25
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole': gap=.25+radius
            elif r['kind']=='pad' and r['net']==net: gap=.1+radius
            elif r['net']==net: continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain: continue
            else: gap=(.15 if r.get('domain')==domain else .6)+radius
            blockers.append(r['shape'].buffer(gap+S.MARGIN)); classes[r['kind']]=classes.get(r['kind'],0)+1
        if layer in model.hard_trees:
            for i in model.hard_trees[layer].query(window.buffer(2),predicate='intersects'):
                r=model.hard[layer][i]
                if net not in r['exempt']:
                    blockers.append(r['shape'].buffer(radius+S.MARGIN));classes[r['kind']]=classes.get(r['kind'],0)+1
    for via in model.g['vias']:
        if window.buffer(2).covers(Point(via['x'],via['y'])):
            blockers.append(Point(via['x'],via['y']).buffer(.8+S.MARGIN))
    ref1=model.reference(target['domain'],'F.Cu',window);ref4=model.reference(target['domain'],'In3.Cu',window)
    free=window.intersection(model.outline.buffer(-.5-radius-S.MARGIN)).intersection(ref1.intersection(ref4)).difference(unary_union(blockers))
    return free,classes
'''


def replace_once(source,before,after):
    if source.count(before)!=1:raise ValueError('Ambiguous derivative source substitution:'+before)
    return source.replace(before,after)


def main():
    receipts=[]
    for original,destination,mode in [(HERE/'alternate-r07/screen_r07.py',HERE/'alternate-r07-small/screen_r07_small.py','r07'),
                                      (HERE/'screen_dive_c06.py',HERE/'small-c05/screen_dive_small.py','c05')]:
        raw=original.read_bytes();source=raw.decode('utf-8');destination.parent.mkdir(exist_ok=True)
        if destination.exists():raise ValueError('Fresh derivative only')
        if mode=='r07':
            source=replace_once(source,'def main():',STRICT_FUNCTION+'\n\ndef main():')
            source=replace_once(source,'D.via_free(model,target,window)','strict_via_free(model,target,window)')
            source=source.replace('size_mm=.6,drill_mm=.3','size_mm=.5,drill_mm=.2')
            source=source.replace("'No new VIPPO/D4 exceptions; .6/.3via", "'No new VIPPO/D4 exceptions; .5/.2via")
            source=source.replace("'alternate-r07-bounded-additive-screen-v1'","'alternate-r07-bounded-additive-small-via-screen-v1'")
        else:
            source=replace_once(source,'HERE=S.HERE','HERE=Path(__file__).resolve().parent')
            source=replace_once(source,'NEW_VIA_RADIUS=.3','NEW_VIA_RADIUS=.25')
            source=replace_once(source,"if r['kind']=='hole': gap=.25+.15","if r['kind']=='hole': gap=.25+NEW_VIA_RADIUS")
            source=source.replace('size_mm=.6,drill_mm=.3','size_mm=.5,drill_mm=.2')
            source=source.replace('0.6/0.3mm ordinary vias','0.5/0.2mm ordinary vias')
            source=source.replace("'c06-bounded-single-dive-screen-v1'","'c06-bounded-single-dive-small-via-screen-v1'")
            source=source.replace('from shapely.geometry import','from shapely.geometry import',1)
            (destination.parent/'target-inventory.json').write_bytes((HERE/'target-inventory.json').read_bytes())
        destination.write_text(source,encoding='utf-8',newline='\n')
        receipts.append({'original':str(original),'original_sha256':hashlib.sha256(raw).hexdigest(),
                         'derived':str(destination),'derived_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                         'via_size_drill_mm':[.5,.2],'clearances_unchanged':True,
                         'hole_policy':'foreign existing hole polygon buffered by .25mm+NEW COPPER radius+.025mm margin',
                         'source_derivation_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (HERE/'small-via-derivation.json').write_text(json.dumps({'derivatives':receipts,'native_jobs':0,'gpu_jobs':0},indent=1)+'\n',encoding='utf-8')
    print(json.dumps(receipts,indent=1))


if __name__=='__main__':main()
