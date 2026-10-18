"""Bind all exact native current intents; never substitute four-role packet."""
import sys,json,pickle,time
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
A=N.K.A;sha=N.sha
OUT=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431'

def fields(raw):
    s=raw.decode();ans=[];depth=0;start=None;quoted=False;escape=False
    for i,c in enumerate(s):
        if quoted:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True;continue
        if c=='(':
            depth+=1
            if depth==2:start=i
        elif c==')':
            if depth==2:
                v=s[start:i+1]
                if not v.startswith('(filled_polygon')and not v.startswith('(fill_segments'):ans.append(v)
            depth-=1
    assert depth==0
    return ans

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir()
    prev=P/'CM79-R300-exact-current-local-context-BEFORE-fill-only-r430';rr=json.loads((prev/'receipt.json').read_bytes());pp=prev/'only-exact-current-Cu-local-pad-pose-profiles-and-BEFORE-fill-context.pkl';assert sha(pp)==rr['context_packet_SHA256'];packet=pickle.loads(pp.read_bytes())
    intents=H/'current-R753-all-native-zone-intents-read-only-r312/all-current-native-intended-zone-outlines-and-profiles.json';assert sha(intents)=='80452bcf08504313ac21195aba3d11ba11751bcd8943245c2404fb7c55e565c2';rows=json.loads(intents.read_bytes());assert len(rows)==852
    iv0=A.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes());iv1=A.C.inventory(Path(packet['active_board']).read_bytes());roi=box(108,191,126,211);qs=[];rules=[];local=[]
    for r in rows:
        polys=[Polygon(x[0],x[1:])for x in r['outline_mm_exact_native_IU_div_1e6']];assert all(p.is_valid for p in polys);shape=unary_union(polys)
        if r['rule_area']:
            rules.append({'uuid':r['UUID'],'name':r['raw_name'],'layers':r['layers'],'outline':r['outline_mm_exact_native_IU_div_1e6'],'no_tracks':r['no_tracks'],'no_vias':r['no_vias'],'no_fill':r['no_fill'],'native_record':r});continue
        unchanged=False
        if shape.intersects(roi)and r['UUID']in iv0[3]:unchanged=fields(iv0[3][r['UUID']])==fields(iv1[3][r['UUID']])
        for ly in r['layers']:
            q={'uuid':r['UUID'],'net':r['raw_net'],'layer':ly,'shape':shape,'clearance_mm':(r['local_clearance_IU']or 0)/1e6,'native_record':r,'unchanged_native_definition':unchanged}
            qs.append(q)
            if shape.intersects(roi):local.append({k:v for k,v in q.items()if k not in ('shape','native_record')}|{'bounds':list(shape.bounds),'area_mm2':shape.area})
    packet['all_current_native_intents']=qs;packet['all_current_native_rule_areas']=rules;packet.pop('current_owned_roles_raw_intended',None)
    fn=OUT/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';fn.write_bytes(pickle.dumps(packet,protocol=5))
    (OUT/'all-local-native-intent-classification.json').write_text(json.dumps(local,indent=1)+'\n',encoding='utf-8')
    receipt={'status':'ALL_CURRENT_NATIVE_INTENTS_BOUND_NOT_CURRENT_FILL_SOURCE_EQUIVALENCE','active_board_SHA256':rr['active_board_SHA256'],'R430_context_SHA256':sha(pp),'R312_all_native_intents_SHA256':sha(intents),'native_record_count':len(rows),'zone_layer_count':len(qs),'native_rule_count':len(rules),'local_zone_layer_count':len(local),'local_unchanged_definition_count':sum(r['unchanged_native_definition']for r in local),'packet_SHA256':sha(fn),'all49_unqualified_CM_excluded':True,'current_AFTER_fill_SOURCE_flash_reference':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print('R431_COMPLETE',sha(OUT/'receipt.json'),local,flush=True)
if __name__=='__main__':main()
