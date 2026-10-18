"""Read-only exact198b native overlay and actual-annulus source references."""
import hashlib,json,re
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
import prepare_sbc_targeted_changed_set as C
p,v=C.p,C.v
REPORT=p.HERE.parent
COMBINED=p.HERE/'fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
SHA='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab'
R07=p.EXT/'integrate/revs/r07-ripup-signals-1.kicad_pcb'
R07_SHA='0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
RES=REPORT/'recovery-composite/c06/alternate-r07'
STRICT=REPORT/'recovery-composite/c06/four-fag/runtime-audit/strict-reference-r1.json'
NATIVE=REPORT/'measure/r07-four-fag-shared/source-proof.json'
ACTUAL={}


def overlay():
    original,current,live=[p.read(x) for x in (p.base.BASE,COMBINED,R07)]
    p.require(hashlib.sha256(original).hexdigest()==p.base.BASE_SHA and hashlib.sha256(current).hexdigest()==SHA and hashlib.sha256(live).hexdigest()==R07_SHA,'frozen native source differs')
    old,new,r07=[p.base.inventory(x) for x in (original,current,live)]
    p.require(old[0]==new[0] and old[2]==new[2] and old[5]==new[5],'native noncopper definitions differ from trusted geometry')
    p.require(all(new[3].get(u)==ch for u,ch in r07[3].items()) and len(set(new[4])-set(r07[4]))==287,'r07+287 additive contract differs')
    g=json.loads(p.read(p.base.GEOM))
    p.require(g['sha256']==p.base.BASE_SHA and g['refilled'] and not g['api_errors'],'native geometry invalid')
    native={r['uuid']:r for r in g['vias']};arcs={r['uuid']:r for r in g['tracks'] if r.get('kind')=='arc'}
    proof=json.loads(p.read(NATIVE))
    p.require(proof['verdict']=='PASS' and proof['candidate_sha256']==SHA,'same-candidate native API evidence differs')
    added={r['uuid']:r for r in proof['native_api']['added_via_annuli']['rows']}
    tracks=[];vias=[]
    for u,ch in new[4].items():
        kind=p.base.pcbtext.chunk_kind(ch)
        if kind=='segment':tracks.append({'uuid':u,'net':p.netname(ch),'a':p.numbers(ch,'start'),'b':p.numbers(ch,'end'),'w':p.scalar(ch,'width'),'layer':p.base.pcbtext.chunk_layer(ch),'locked':b'(locked yes)' in ch})
        elif kind=='via':
            p.require(b'(layers "F.Cu" "B.Cu")' in ch and not any(flag in ch for flag in (b'via blind',b'via micro',b'padstack')),'unsupported through-via source')
            x,y=p.numbers(ch,'at');r={'uuid':u,'net':p.netname(ch),'x':x,'y':y,'d':p.scalar(ch,'size'),'drill':p.scalar(ch,'drill'),'span':g['copper_layers']}
            if old[4].get(u)==ch and u in native:
                n=native[u];p.require(all(n[k]==r[k] for k in ('x','y','d','drill')),'old exact native via geometry differs')
                r.update(flashed=n['flashed'],span=n['span'],mask_provenance='exact r06 native observed')
            elif u in added:r.update(flashed=added[u]['actual_flashed_layers'],mask_provenance='same198b native API')
            else:r.update(flashed=[],mask_provenance='changed unverified via excluded from conductivity')
            ACTUAL[u]=dict(r);vias.append(r)
        else:p.require(u in arcs and old[4].get(u)==ch,'unsupported changed arc');tracks.append(arcs[u])
    g.update(tracks=tracks,vias=vias,board=str(COMBINED),sha256=SHA,refilled=False)
    g['domains_normalized']={p.norm(n):d for n,d in g['nets'].items()}
    strict=json.loads(p.read(STRICT))
    p.require(strict['verdict']=='HOST_PASS_NATIVE_ELECTRICAL_OPEN' and strict['contract']['candidate_sha256']==SHA and len(strict['checks'])==8 and not strict['failures'],'strict198b reference audit differs')
    for path,expected in strict['source_files_sha256'].items():p.require(hashlib.sha256(p.read(path)).hexdigest()==expected,'strict reference dependency differs')
    changed=[r for r in vias if old[4].get(r['uuid'])!=new[4][r['uuid']] and p.norm(r['net'])!=v.GND]
    cuts=unary_union([Point(r['x'],r['y']).buffer(r['d']/2+(.15 if g['domains_normalized'].get(p.norm(r['net']))=='DOM_LOGIC' else .6)+p.MARGIN) for r in changed])
    anchor=next(r for r in g['pads'] if r['ref']=='J11001' and r['num']=='2')
    rooted={};witness={}
    for layer in ('In1.Cu','In4.Cu'):
        fill=unary_union([poly for z in g['zones'] if p.norm(z['net'])==v.GND for poly in p.base.polygons(z['fills'].get(layer,[]))]).difference(cuts)
        own=[poly for pad in g['pads'] if p.norm(pad['net'])==v.GND for poly in p.base.polygons(pad['layers'].get(layer,[]))]
        own.extend(p.base.body(t) for t in tracks if t['layer']==layer and p.norm(t['net'])==v.GND)
        own.extend(Point(r['x'],r['y']).buffer(r['d']/2) for r in vias if p.norm(r['net'])==v.GND and layer in r['flashed'])
        conductor=unary_union([fill]+own);source=unary_union(p.base.polygons(anchor['layers'][layer]))
        connected=unary_union([part for part in p.hubs.components(conductor) if part.intersects(source)])
        rooted[layer]=fill.intersection(connected)
        witness[layer]={'source':'J11001.2','source_uuid':anchor['uuid'],'foreign_via_cutters':len(changed),'actual_flashed_LOGIC_vias':sum(p.norm(r['net'])==v.GND and layer in r['flashed'] for r in vias),'source_connected_safe_fill_mm2':rooted[layer].area}
    g['_rooted_refs']=rooted;p.read(Path(__file__))
    return g,{'exact198b_native_overlay':True,'all_r07_items_bytes_exact':True,'new_copper':287,'components_poses_setup_zone_definitions_exact_r06':True,'c05_DFM_poses_carried':False,'conservative_r06_fill_only':True,'actual198b_fill_claimed':False,'source_reference_witnesses':witness,'prospective_new_power_antipads_not_qualified':True}


def reservations():
    data=json.loads(p.read(RES/'reserved-r07.json'));ex={}
    for line in p.read(RES/'reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={p.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    return [{**a,'exempt':ex.get(a['name'],set())} for a in data['keepouts']]


def reference(g,layer):return g['_rooted_refs'][layer].intersection(p.base.WINDOW)
