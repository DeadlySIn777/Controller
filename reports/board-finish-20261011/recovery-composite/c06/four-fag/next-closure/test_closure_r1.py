"""Small host controls for strict annuli, continuous lands and exact attachments."""
import hashlib,json,sys,time,types
from pathlib import Path
sys.dont_write_bytecode=True
import screen_closure_r1 as C
from shapely.geometry import Point,box
from shapely.strtree import STRtree

def main():
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    ordinary=b'(via (layers "F.Cu" "B.Cu"))';suppressed=b'(via (layers "F.Cu" "B.Cu") (remove_unused_layers yes))'
    v={'uuid':'v','net':'/LOGIC_GND','x':0.,'y':0.,'d':.5,'drill':.2}
    g={'vias':[v],'copper_layers':['F.Cu','In1.Cu','In3.Cu','In4.Cu','B.Cu']}
    old=[None]*5;current=[None]*5;old[4]={'v':ordinary};current[4]={'v':ordinary}
    native={'vias':[dict(v,flashed=['F.Cu','B.Cu'])]};added={'native_api':{'added_via_annuli':{'rows':[]}}}
    masks,provenance,reuse=C.actual_masks(g,old,current,native,added)
    check('native suppressed annuli never inferred from nominal through span',masks['v']=={'F.Cu','B.Cu'} and reuse['v'])
    bad={'vias':[dict(v,x=.001,flashed=['F.Cu'])]}
    try:C.actual_masks(g,old,current,bad,added)
    except ValueError:checks.append('changed native geometry rejected')
    else:raise AssertionError('native geometry accepted')
    current[4]['v']=suppressed
    masks,_,reuse=C.actual_masks(g,old,current,native,added)
    check('changed suppressed via withheld',not masks['v'] and not reuse['v'])
    current[4]['v']=ordinary+b'\n'
    masks,provenance,reuse=C.actual_masks(g,old,current,native,added)
    check('unobserved KEEP_ALL cannot become qualified existing return/new-layer reuse',masks['v']==set(g['copper_layers']) and not reuse['v'] and 'native flash open' in provenance['v'])
    # This positive island contains no .1mm gridpoint, but is physically inside
    # an existing-return radius and must produce an exact continuous seed.
    island=box(.9031,.0131,.9039,.0139);rv={'uuid':'r','x':0.,'y':0.,'diameter':.5,'return_net':'/LOGIC_GND'}
    sites,stats=C.continuous_landings(island,[rv],(1.,0.),'F.Cu')
    check('continuous sub-grid positive landing found',stats['continuous_return_intersection_components']==1 and sites and all(island.covers(Point(s['point_mm'])) for s in sites))
    check('no-return landing rejected',C.continuous_landings(island,[],(1.,0.),'F.Cu')[0]==[])
    wire_free=box(.9,0,2.,.1);start=tuple(sites[0]['point_mm']);end=(1.9813,.0387)
    path,_=C.S.astar(wire_free,[(start,{'uuid':'a','kind':'pad'})],[(end,{'uuid':'b','kind':'pad'})],time.monotonic()+2)
    check('off-grid endpoints retain checked exact connectors',path and path['points_mm'][0]==list(start) and path['points_mm'][-1]==list(end))
    # Unflashed via on B must not silently join these two saved pad partitions.
    records=[]
    for pid,layer in (('A.1#0','F.Cu'),('B.1#0','B.Cu')):
        records.append({'shape':Point(0,0).buffer(.2),'net':'/N','kind':'pad','uuid':pid,'key':('p',pid),'pad_id':pid,'layer':layer})
    for layer in ('F.Cu','B.Cu','In3.Cu'):
        records.append({'shape':Point(0,0).buffer(.25),'net':'/N','kind':'via','uuid':'v','key':('v','v'),'layer':layer})
    model=types.SimpleNamespace(own={'/N':records},g={'copper_layers':['F.Cu','B.Cu','In3.Cu']})
    target={'net':'/N','c05_groups':[['A.1#0'],['B.1#0']],'lost_relationships':[{'r07_connected_pad_ids':['A.1#0','B.1#0']}]}
    groups=C.physical_groups(model,target,{'v':{'F.Cu'}},{'v':True})
    check('physical partition graph excludes unflashed own annulus',len(groups)==2 and all('In3.Cu' not in x['layers'] for x in groups))
    try:C.physical_groups(model,target,{'v':{'F.Cu','B.Cu','In3.Cu'}},{'v':True})
    except ValueError:checks.append('false nominal all-layer join rejected by native partitions')
    else:raise AssertionError('false native topology accepted')
    # Larger conservative full-copper via radius participates in hole spacing.
    hole=Point(0,0).buffer(.1)
    mock=types.SimpleNamespace(g={'copper_layers':['F.Cu'],'vias':[]},records={'F.Cu':[{'shape':hole,'kind':'hole','net':'/OTHER'}]},trees={'F.Cu':STRtree([hole])},hard_trees={},hard={},outline=box(-3,-3,3,3))
    refs={'In1.Cu':box(-2,-2,2,2),'In4.Cu':box(-2,-2,2,2)}
    free,_=C.via_free(mock,{'net':'/N','domain':'DOM_LOGIC'},box(-2,-2,2,2),refs)
    check('full .25mm copper radius plus .25 hole clearance and .025 margin enforced',not free.covers(Point(.624,0)) and free.covers(Point(.626,0)))
    mock.g['vias']=[{'x':0.,'y':0.}]
    free,_=C.via_free(mock,{'net':'/N','domain':'DOM_LOGIC'},box(-2,-2,2,2),refs)
    check('ordinary .8mm via spacing plus margin enforced',not free.covers(Point(.824,0)) and free.covers(Point(.826,0)))
    output=Path(__file__).with_name('closure-r1-controls.json')
    if output.exists():raise ValueError('Distinct receipt required')
    result={'verdict':'PASS','controls':checks,'screen_sha256':hashlib.sha256(Path(C.__file__).read_bytes()).hexdigest(),'tests_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'real_screen_sha256':hashlib.sha256(Path(__file__).with_name('bounded-closure-r1.json').read_bytes()).hexdigest(),'native_jobs':0,'board_emitted':False,'scope':'Host algorithm controls only, not native or electrical proof'}
    output.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':'PASS','controls':len(checks)}))

if __name__=='__main__':main()
