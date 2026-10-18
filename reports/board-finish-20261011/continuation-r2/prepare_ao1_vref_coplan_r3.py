"""Derive wider legal analog via sites and bounded two-face track construction."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    original=HERE/'probe_ao1_vref_local_r2.py'
    derived=HERE/'probe_ao1_vref_coplan_r3.py'
    if derived.exists(): raise ValueError('Fresh analog constructor required')
    raw=original.read_text()
    raw=raw.replace("OUT = HERE / 'ao1-vref-local-r2'","OUT = HERE / 'ao1-vref-coplan-r3'")
    raw=raw.replace('region=box(372,126,379,132)','region=box(370,125,381,133)')
    old="[(376.725+i*.05,129+j*.05) for i in range(9) for j in range(-2,3)] + [(374.25-i*.05,129+j*.05) for i in range(6) for j in range(-2,3)]"
    new="[(377.3+i*.1,129+j*.1) for i in range(23) for j in range(-2,3)] + [(374.25-i*.1,129+j*.1) for i in range(35) for j in range(-2,3)]"
    if raw.count(old)!=1: raise ValueError('Exact finite site list marker differs')
    raw=raw.replace(old,new)
    marker='    for p,h in A.READS.items():\n'
    addition='''    # A same-domain AO1_COM fill may retreat under a new legal trace.
    # This is only a prospective construction; full fill contact/reference
    # audits and actual native refill remain mandatory.
    free_by_layer={}
    for layer in ['B.Cu','F.Cu']:
        obstacles=[]
        for rec in model.records[layer]:
            if rec.get('net')==net: continue
            if rec['kind']=='fill' and rec.get('domain')==domain and rec.get('net')=='/motherboard_analog_output/AO1_COM': continue
            clearance=.275 if rec['kind']=='hole' else .175 if rec.get('domain')==domain else .625
            if rec['shape'].distance(region)<clearance+.125: obstacles.append(rec['shape'].buffer(clearance+.1))
        for hard in model.hard[layer]:
            if net not in hard['exempt']: obstacles.append(hard['shape'].buffer(.125))
        free_by_layer[layer]=region.buffer(-.125).difference(unary_union(obstacles))
    attempts=[]
    legal_sites=sorted([r for r in rows if not r['via_errors']],key=lambda r:math.dist(r['at'],[375.498,129]))
    for row in legal_sites[:24]:
        paths=[];failed=[]
        for pad_id,layer in zip(padids,['B.Cu','F.Cu']):
            free=free_by_layer[layer];start=(pads[pad_id]['x'],pads[pad_id]['y']);goal=row['at']
            if not free.covers(Point(start)) or not free.covers(Point(goal)):
                failed.append({'layer':layer,'reason':'source_or_via_center_not_in_exact_free_polygon'});break
            path,details=S.astar(free,[start],[goal],time.monotonic()+12,node_cap=120000)
            if not path:
                failed.append({'layer':layer,**details});break
            points=[[round(float(x),6),round(float(y),6)] for x,y in path['points_mm']]
            if not free.buffer(1e-9).covers(LineString(points)):
                failed.append({'layer':layer,'reason':'native_quantized_path_exits_guarded_free_polygon'});break
            paths.append({'pad':pad_id,'layer':layer,'points_mm':points,'width_mm':.2,'search':details})
        attempts.append({'at':row['at'],'diameter_mm':row['diameter_mm'],'drill_mm':row['drill_mm'],'paths':paths,'failures':failed})
        if not failed and len(paths)==2:
            row['routes']=paths;row['track_errors']=[];row['geometry_candidate']=True
            row['construction']='bounded_quantized_two_face_detour_with_prospective_AO1_COM_fill_retreat'
            break
    (OUT/'route-construction.json').write_text(json.dumps({'legal_via_sites':len(legal_sites),'attempts':attempts,'all_source_fill_polygons_unchanged':True,'full_fill_contact_reference_audit':'OPEN','adopted':False},indent=1)+'\\n',encoding='utf-8')
'''
    if raw.count(marker)!=1: raise ValueError('Exact probe pre-receipt marker differs')
    raw=raw.replace(marker,addition+marker)
    derived.write_text(raw,encoding='utf-8')
    (HERE/'ao1-vref-coplan-r3-derivation.json').write_text(json.dumps({'original':str(original),'original_sha256':sha(original),'derived':str(derived),'derived_sha256':sha(derived),'changes':['Wider explicit finite candidate list and regional independence bound','Bounded F and B detour construction','Allow prospective retreat only for the same-domain AO1_COM fill','Quantize new paths to integer nanometres before exact free-polygon recheck'],'all_original_via_track_drill_pitch_domain_reservation_thresholds_preserved':True,'source_fill_definitions_unchanged':True,'board_emitted':False,'adopted':False},indent=1)+'\n',encoding='utf-8')
    print(str(derived),flush=True)
if __name__=='__main__': main()
