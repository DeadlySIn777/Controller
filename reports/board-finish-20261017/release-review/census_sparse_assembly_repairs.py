"""Choose local assembly repair topology from actual saved native groups."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import collections,csv,hashlib,json,math,pickle,sys,xml.etree.ElementTree as ET
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from shapely.geometry import Point
from shapely import STRtree
import find_paired_return_sites as F
H=Path(__file__).resolve().parent;OUT=H/'assembly-repair-topology-r1';OUT.mkdir()
csvfile=F.ROOT/'reports/board-finish-20261017/power-review/native-warning-assembly-review-r2/actual-native-via-drill-SMD-Cu-intersections.csv'
model=F.CACHE/'actual-combined-full-after-model.pkl';graph=F.CACHE/'actual-combined-full-after-all-net-groups.pkl';xmlfile=H/'R299-fresh-source.xml'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pins={str(f):sha(f) for f in (csvfile,model,graph,xmlfile,Path(__file__))}
h=pickle.loads(model.read_bytes());groups=pickle.loads(graph.read_bytes());vv={v['uuid']:v for v in h['vias']}
a=list(csv.DictReader(csvfile.open()));bad=collections.defaultdict(list)
for r in a:
    if (r['native_filling']!='yes' or r['native_capping']!='yes') and r['old_291_registry_uuid_hit']!='True' and r['ROOT106_present_uuid_hit']!='True':bad[r['via_uuid']].append(r)
priority={'/motherboard_compute/USB_RECOVERY_MODE','/FPGA_USER_RESET_N','/motherboard_analog_input/AI3_CURRENT_MODE','/motherboard_compute/CM_COMMS_OE_N'}
xml=ET.parse(xmlfile).getroot();cn={q.get('ref'):q for q in xml.find('components')};netxml={F.norm(q.get('name')):q for q in xml.find('nets')}
results=[];census=collections.Counter()
for net,gg in groups.items():
    ids={r['uuid'] for q in gg for r in q if r['kind']=='via' and r['uuid'] in bad}
    if not ids:continue
    rows=[r for q in gg for r in q if r['kind']!='via' or r['uuid'] not in ids]
    trees={ly:STRtree([r['shape'] for r in rows if r['layer']==ly]) for ly in F.K.LAYERS};rr={ly:[r for r in rows if r['layer']==ly] for ly in F.K.LAYERS}
    for uid in ids:
        v=vv[uid];center=Point(v['x'],v['y']);ann=center.buffer(v['d']/2-.000002,quad_segs=256).difference(F.outer(center,v['drill']/2));contacts=[]
        for ly in v['flashed']:
            for i in trees[ly].query(ann):
                r=rr[ly][int(i)];area=ann.intersection(r['shape']).area
                if area>.000001:contacts.append({'kind':r['kind'],'UUID':r['uuid'],'layer':ly,'ref':r.get('ref'),'pin':r.get('pin'),'finite_contact_lower_mm2':area})
        layers=sorted({r['layer'] for r in contacts});census[tuple(layers)]+=1
        if net not in priority and not (len(layers)==1 and layers[0] in ('F.Cu','B.Cu')):continue
        peers=sorted((math.dist((v['x'],v['y']),(u['x'],u['y'])),u['uuid'],u['x'],u['y'],u['uuid'] in bad) for u in h['vias'] if F.norm(u['net'])==net and u['uuid']!=uid)
        results.append({'via_UUID':uid,'net':net,'at_mm':[v['x'],v['y']],'native_flashed_layers':v['flashed'],'contact_layers':layers,'finite_external_contacts':contacts,'assembly_pad_rows':bad[uid],
                        'nearest_same_net_existing_vias':[{'distance_mm':d,'UUID':u,'at_mm':[x,y],'also_unregistered_SMD_hit':b} for d,u,x,y,b in peers[:8]],
                        'source_connected_nodes':[] if net not in netxml else [{**n.attrib,'component_value':cn[n.get('ref')].findtext('value'),'footprint':cn[n.get('ref')].findtext('footprint')} for n in netxml[net].findall('node')]})
report={'status':'ACTUAL_EXTERNAL_CONTACT_CENSUS_NO_REPAIR_ADOPTED','unregistered_ordinary_vias':len(bad),'all_via_actual_external_contact_layer_patterns':{'|'.join(k):v for k,v in census.items()},'prioritized_and_surface_only_sites':results,'input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==s for f,s in pins.items()),'native_jobs':0,'PCB_written':False}
(OUT/'receipt.json').write_text(json.dumps(report,indent=1)+'\n')
print(json.dumps({'sites':len(results),'surface_only':sum(len(r['contact_layers'])==1 for r in results),'priority':[(r['net'],r['via_UUID'],r['contact_layers'],len(r['finite_external_contacts'])) for r in results if r['net'] in priority]}))
