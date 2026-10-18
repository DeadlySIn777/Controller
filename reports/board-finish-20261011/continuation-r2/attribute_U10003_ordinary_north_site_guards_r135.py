"""Attribute exact ordinary-site guards without changing copper or masks."""
import hashlib,json,pickle,re,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
OUT=H/'U10003-ordinary-north-site-exact-guard-attribution-r135'
NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());records,trees=F.build({**h,'zones':[]});rows=[];root=next(xs for xs in pickle.loads(mp.with_name('groups.pkl').read_bytes())[NET] if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11003','2') for q in xs))
    refshapes={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in h['copper_layers']};foot=next(f for f in h['footprints'] if f['ref']=='U10003');court=unary_union([s for rs in foot['courtyard'].values() for s in C.poly(rs)])
    reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];dru=(reserved/'reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    for x,y in [(215.4,142.05),(215.45,141.95),(215.75,142.15),(216.05,142.05),(215.4,141.75)]:
        pt=Point(x,y);disk=pt.buffer(.25,quad_segs=256);ann=disk.difference(pt.buffer(.1,quad_segs=256));bad=[]
        for l in h['copper_layers']:
            for j in trees[l].query(disk.buffer(.627),predicate='intersects'):
                q=records[l][int(j)]
                if C.norm(q['net'])==NET:continue
                required=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET] else .6)+.025+.000020;actual=disk.distance(q['shape'])
                if actual<required:bad.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'layer':l,'actual':actual,'required':required})
        for q in z:
            if C.norm(q['net'])==NET:continue
            required=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET] else .6,float(q.get('clearance_mm',.15)))+.025+.000020;actual=disk.distance(q['shape'])
            if actual<required:bad.append({'kind':'OWNED_PROPOSED_PLANE','UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'actual':actual,'required':required})
        for p in h['pads']:
            for sh in C.poly(p.get('hole') or []):
                actual=pt.distance(sh)-.1
                if actual<.275+.000020:bad.append({'kind':'PAD_HOLE','UUID':p['uuid'],'actual':actual})
            if p['smd']:
                for l,rs in p['layers'].items():
                    actual=pt.distance(unary_union(C.poly(rs)))-.1
                    if actual<.275+.000020:bad.append({'kind':'SMD_HOLE_SPACING','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':l,'actual':actual})
        for v in h['vias']:
            actual=pt.distance(Point(v['x'],v['y']))-(.2+v['drill'])/2
            if actual<.275+.000020:bad.append({'kind':'VIA_HOLE_PITCH','UUID':v['uuid'],'actual':actual})
        for a in h['rule_areas']:
            if a.get('no_vias') and any(disk.intersects(s.buffer(.025)) for s in C.poly(a['outline'])):bad.append({'kind':'NATIVE_NO_VIA','UUID':a['uuid'],'name':a.get('name')})
        for a in areas:
            if NET not in exceptions.get(a['name'],set()) and any(disk.intersects(s.buffer(.025)) for s in C.poly(a['outline'])):bad.append({'kind':'ROUTER_SOURCE_RESERVATION','name':a['name']})
        core=[q['uuid'] for q in h['zones'] if C.norm(q['net'])=='/CORE_1V2' and 'In3.Cu' in q['layers'] and any(disk.intersects(s) for s in C.poly(q['outline']))]
        rows.append({'site_mm':[x,y],'diameter_drill_mm':[.5,.2],'outside_literal_own_courtyard_plus25um':disk.distance(court)>=.025,'actual_source_annular_overlap_mm2':{l:ann.intersection(sh).area for l,sh in refshapes.items()},'explicit_guard_deficits':bad,'conservative_native_CORE_In3_outline_mask_overlap_UUIDs':core})
    record={'verdict':'EXACT_ORDINARY_GROUND_SITE_GUARD_ATTRIBUTION_NO_EXEMPTIONS','model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
