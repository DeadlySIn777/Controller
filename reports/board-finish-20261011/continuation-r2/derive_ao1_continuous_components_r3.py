"""Diagnose exact continuous escape components before a finer bounded search."""
import hashlib,json,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'plan_ao1_vref_sdi_coupled_r2.py';target=HERE/'plan_ao1_vref_sdi_components_r3.py'
    if target.exists():raise ValueError('Fresh analog component diagnostic required')
    text=source.read_text(encoding='utf-8').replace("OUT=HERE/'ao1-vref-sdi-coupled-r2'","OUT=HERE/'ao1-vref-sdi-components-r3'")
    anchor='    attempts=[];success=None'
    if text.count(anchor)!=1:raise ValueError('Exact analog component anchor differs')
    extra='''    def polygons(shape):
        if shape.geom_type=='Polygon':return [shape]
        return [p for g in getattr(shape,'geoms',[]) for p in polygons(g)]
    free_ledger={}
    for layer,shape in free.items():
        path=OUT/(layer+'.free.wkb');path.write_bytes(shape.wkb)
        pieces=polygons(shape);free_ledger[layer]={'path':str(path.resolve()),'sha256':sha(shape.wkb),'components':[{'index':i,'area_mm2':p.area,'bounds':list(p.bounds),'contains_start':p.covers(Point(start)),'contains_goal':p.covers(Point(goal)),'legal_via_sites':[list(at) for at in sites if p.covers(Point(at))]} for i,p in enumerate(pieces)]}
    source_pieces=[p for p in polygons(free['F.Cu']) if p.covers(Point(start))]
    if len(source_pieces)!=1:raise ValueError('Analog source lacks exactly one free component')
    component=source_pieces[0]; reachable_sites=[at for at in sites if component.covers(Point(at))]
    blockers=[]
    for rec in model.records['F.Cu']:
        if rec.get('net')==SDI or rec['kind']=='fill' and rec.get('net')==COM:continue
        margin=.275 if rec['kind']=='hole' else .175 if rec.get('domain')==DOMAIN else .625
        grown=rec['shape'].buffer(margin+.1)
        if grown.distance(component)<.00001:blockers.append({'kind':rec['kind'],'uuid':rec.get('uuid',rec.get('id')),'net':rec.get('net'),'bounds':list(rec['shape'].bounds),'guard_margin_mm':margin+.1,'distance_to_source_component_mm':grown.distance(component)})
    write(OUT/'continuous-component-diagnostic.json',{'verdict':'CONTINUOUS_SOURCE_COMPONENT_REACHES_LEGAL_VIA_SITES' if reachable_sites else 'NO_SAMPLED_LEGAL_VIA_SITE_IN_EXACT_GUARDED_SOURCE_COMPONENT','source_mm':list(start),'source_component_area_mm2':component.area,'source_component_bounds':list(component.bounds),'all_legal_sites':len(sites),'source_reachable_legal_sites':len(reachable_sites),'boundary_blockers':blockers,'layer_free_polygons':free_ledger,'only_prospective_COM_fill_retreat_assumed':True,'global_no_path_claim':False})
    # Fine grid is useful only if a continuous free component reaches a legal site.
    sites=reachable_sites;S.STEP=.025
    attempts=[];success=None'''
    text=text.replace(anchor,extra)
    target.write_text(text,encoding='utf-8')
    (HERE/'ao1-vref-sdi-components-derivation-r3.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(target),'changes':'Save exact free polygons, diagnose source-connected components and boundary blockers; use .025mm grid only on continuously reachable via sites; all original clearance and exact ownership checks retained'},indent=1)+'\n',encoding='utf-8')
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
