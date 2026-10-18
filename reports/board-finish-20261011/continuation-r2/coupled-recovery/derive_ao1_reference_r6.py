"""Search freed SDI sites and actual joint return geometry, preserving r5."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;p=HERE/'ao1_reference_coupled_r5.py';t=p.read_text()
t=t.replace('import ao1_astar_exact_r1 as E','import ao1_astar_exact_r1 as E\nimport ao1_via_region_r1 as VR')
t=t.replace("OUT=HERE/'ao1-reference-coupled-r5.json'","OUT=HERE/'ao1-reference-coupled-r6.json'")
start=t.index('    vsite=[]\n');end=t.index('    vsite.sort',start)
replacement="""    via_regions={net:VR.legal_centres(initial,net,WINDOW) for net in (VREF,SDI)}
    vsite=[];ssites=[]
    for i in range(75):
        for j in range(65):
            at=(round(370.5+i*.1,9),round(125.5+j*.1,9));point=Point(at)
            if vspace.covers(point) and via_regions[VREF].covers(point):vsite.append(at)
            if sspace.covers(point) and via_regions[SDI].covers(point):ssites.append(at)
    old_sites=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/site-screen.json'))['sites_mm']
"""
t=t[:start]+replacement+t[end:]
t=t.replace("vsite.sort(key=lambda p:(math.dist(p,vstart),p));ssites.sort(key=lambda p:(math.dist(p,sstart),p))","vsite.sort(key=lambda p:(math.dist(p,(374.,129.1)),p));ssites.sort(key=lambda p:(math.dist(p,(374.8,128.5)),p))")
t=t.replace("'sdi_legal_sites_from_saved162':ssites","'newly_freed_SDI_sites':ssites,'frozen_old162_site_evidence_count':len(old_sites)")
t=t.replace("'ao1-r5-initial-'","'ao1-r6-initial-'")
t=t.replace('for vat in vsite[:12]:','for vat in vsite[:20]:')
t=t.replace('for sat in ssites[:12]:','for sat in ssites[:20]:')
needle="                chosen=None\n                for radius in (.9,.95,1.):"
replacement="""                shared=[r['at_mm'] for r in returns if .81-1e-9<=math.dist(at,r['at_mm'])<=1.+1e-9]
                chosen=shared[0] if shared else None
                for radius in (() if chosen else (.85,.9,.95,1.)):
"""
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("'SCLK_all_source_geometry_exact':True","'SCLK_all_source_geometry_exact':True,'new_SDI_sites_freed_by_replacing_old_VREF':True,'shared_return_allowed_only_if_source_rooted_and_ordinary_pitch_for_both':True")
q=HERE/'ao1_reference_coupled_r6.py'
if q.exists():raise ValueError('Fresh r6 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-reference-r6-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'changes':['All newly freed physically legal SDI sites, not an artificial old162 limit','Compiled exact local six-layer via centre polygons for nomination; complete source/candidate clearance and independent final audits still required','Rank targeted VREF374/129.1 and SDI374.8/128.5 neighborhoods','A qualified actual grounded ordinary return can serve both dives if it meets both .81 pitch and <=1mm distance'],'board_emitted':False},indent=1)+'\n')
print('Freed-site coupled r6 syntax PASS')
