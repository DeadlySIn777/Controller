"""Meaningful host rejection controls, no board/native operations."""
import hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
import screen_dic_stitch as T
from shapely.geometry import Point,LineString,box

def main():
    rows=[]
    def require(name,condition):
        if not condition:raise AssertionError(name)
        rows.append(name)
    origin=(0.,0.)
    legal=Point(origin).buffer(1.,resolution=64).difference(Point(origin).buffer(.9,resolution=64))
    legal=legal.intersection(box(.9131,.0131,.9139,.0139))
    sites=T.sample_parts(legal,origin)
    require('new return exact continuous subgrid site inside .9-1.0mm ring',sites and all(.9<=__import__('math').dist(p,origin)<=1.0 for p in sites))
    outside=box(1.01,-.01,1.02,.01)
    require('outside return window produces no site',not T.sample_parts(outside.intersection(legal),origin))
    source={'shape':Point(.95,0).buffer(.1),'net':'/LOGIC_GND','kind':'pad','layer':'F.Cu','pad_id':'SRC.1#0','uuid':'src'}
    isolated={**source,'pad_id':'ISLAND.1#0','uuid':'island'}
    unknown={'shape':Point(1.1,0).buffer(.25),'net':'/LOGIC_GND','kind':'via','layer':'F.Cu','uuid':'unobserved'}
    model=types.SimpleNamespace(own={'/LOGIC_GND':[source,isolated,unknown]},g={'vias':[{'uuid':'unobserved','x':1.1,'y':0.,'d':.5,'drill':.2}]})
    refs={'In1.Cu':box(-3,-3,3,3),'In4.Cu':box(-3,-3,3,3)}
    targets=T.grounded_targets(model,box(-2,-2,2,2),{'unobserved':{'F.Cu','In1.Cu','In4.Cu'}},{'unobserved':'changed ordinary KEEP_ALL source default; native flash open'},{'SRC.1#0'},refs,refs)
    require('stub endpoint requires actual native source pad membership, rejects isolated owner',len(targets['F.Cu']['records'])==1 and targets['F.Cu']['records'][0]['uuid']=='src')
    require('source-default via cannot qualify grounded return stub target',not any(r['uuid']=='unobserved' for r in targets['F.Cu']['records']))
    ground_via={'net':'/LOGIC_GND','point_mm':[0.,0.],'size_mm':.5,'drill_mm':.2}
    ground_stub={'net':'/LOGIC_GND','points_mm':[[-2.,0.],[2.,0.]],'layer':'F.Cu','width_mm':.2}
    blocked=T.new_copper_cut([ground_via],[ground_stub],'F.Cu','/DIC_CS')
    require('new return copper blocks signal route on all layers',blocked.covers(Point(.52,0)) and not T.new_copper_cut([ground_via],[],'B.Cu','/DIC_CS').covers(Point(.526,0)))
    require('grounded stub blocks same-domain signal trace by full .375mm envelope',blocked.covers(Point(1.,.374)) and not blocked.covers(Point(1.,.376)))
    require('unshared layer stub does not create invented obstruction',not T.new_copper_cut([], [ground_stub],'B.Cu','/DIC_CS').covers(Point(1.,0)))
    out=Path(__file__).with_name('host-controls.json')
    if out.exists():raise ValueError('Distinct immutable receipt')
    result={'verdict':'PASS','controls':rows,'script_sha256':hashlib.sha256(Path(T.__file__).read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_jobs':0,'board_emitted':False,'scope':'Host helper boundary controls, not native/electrical proof'}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':'PASS','controls':len(rows)}))

if __name__=='__main__':main()
