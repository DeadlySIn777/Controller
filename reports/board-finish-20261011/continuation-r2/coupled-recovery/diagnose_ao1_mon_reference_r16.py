"""Exact prospective AO1 reference/contact diagnosis; no candidate or board credit."""
import json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_positive_operation_r2 as Q
import ao1_reference_coupled_r14 as R
import ao1_reference_gap_diagnostic_r2 as GD
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
OUT=HERE/'ao1-mon-reference-diagnostic-r16.json'

def main():
    if OUT.exists():raise ValueError('Fresh diagnosis required')
    started=time.monotonic();recipe=json.loads(A.read(HERE/'ao1-reference-coupled-r14.json'));case=recipe['attempts'][0]
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA or C.sha(raw)!=recipe['source_sha256']:raise ValueError('Frozen exact source differs')
    removed=set(recipe['removed_owned_items']);new={}
    for net,at in ((Q.VREF,case['VREF_via_mm']),(Q.SDI,case['SDI_via_mm'])):
        u,ch=Q.serial_via(identity,net,at);new[u]=ch
    for row in case['nomination_returns']:
        if row['existing_uuid']:continue
        u,ch=Q.serial_via(identity,Q.COM,row['at_mm']);new[u]=ch
    for row in case['paths']:
        for a,b in zip(row['points_mm'],row['points_mm'][1:]):u,ch=identity.serial_segment(row['net'],row['layer'],a,b,.2);new[u]=ch
    chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update(new);identity.assert_chunks(chunks)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,padproof=A.fresh_template(old,now,template,native)
    smasks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(smasks)
    parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};masks.update({u:set(template['copper_layers']) for u,z in parsed.items() if z['kind']=='via'})
    reserve,exempt=A.reservations();print('AO1_MON_DIAGNOSTIC_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],smasks)
    print('AO1_MON_DIAGNOSTIC_SERIALIZED_MODEL',flush=True)
    final=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],smasks)
    final,ledger,fillerrors=Q.prospective_fill(base,final,masks,now,parsed,set(parsed))
    oldrefs,oldwitness,_,_=Q.rooted_reference(base,smasks,identity.raw(Q.COM));refs,witness,_,_=Q.rooted_reference(final,masks,identity.raw(Q.COM))
    print(json.dumps({'early_fill_errors':len(fillerrors)}),flush=True)
    region=box(367,124,377,132);files={}
    for name,shape in [('original-In1-rooted-reference',oldrefs['F.Cu']),('prospective-In1-rooted-reference',refs['F.Cu']),('prospective-MON-physical-free',R.free(final,R.MON,'F.Cu')),('prospective-MON-full-reference-free',R.free(final,R.MON,'F.Cu').intersection(refs['F.Cu'].buffer(-.11)))]:
        z=shape.intersection(region);p=HERE/('ao1-mon-r16-'+name+'.wkb');p.write_bytes(z.wkb);files[name]={'path':str(p.resolve()),'SHA256':C.sha(z.wkb),'area_mm2':z.area,'bounds_mm':list(z.bounds)}
    mon=[];foreign=[];unchanged=[];bad=[]
    for row in base.records['F.Cu']:
        if row['uuid'] not in R.MON_REMOVED:continue
        original=row['shape'].difference(oldrefs['F.Cu']);candidate=row['shape'].difference(refs['F.Cu']);lost=row['shape'].intersection(oldrefs['F.Cu']).difference(refs['F.Cu'])
        p=HERE/('ao1-mon-r16-'+row['uuid']+'-reference-lost.wkb');p.write_bytes(lost.wkb)
        mon.append({'uuid':row['uuid'],'exact_shape_SHA256':C.sha(row['shape'].wkb),'original_uncovered_mm2':original.area,'prospective_uncovered_mm2':candidate.area,'previously_covered_lost_mm2':lost.area,'original_gap_bounds_mm':list(original.bounds),'prospective_gap_bounds_mm':list(candidate.bounds),'lost_WKB_path':str(p.resolve()),'lost_WKB_SHA256':C.sha(lost.wkb)})
    for layer,rows in base.records.items():
        if layer not in refs:continue
        for row in rows:
            if row['kind']!='track' or row['uuid'] in removed or row.get('domain')!=base.domains[Q.COM] or row.get('net')==Q.COM or not row['shape'].intersects(region):continue
            lost=row['shape'].intersection(oldrefs[layer]).difference(refs[layer])
            if lost.area>1e-9:
                rec={'uuid':row['uuid'],'net':row['net'],'layer':layer,'lost_reference_mm2':lost.area,'bounds_mm':list(lost.bounds)};unchanged.append(rec)
                p=HERE/('ao1-mon-r16-'+row['uuid']+'-'+layer+'-unchanged-reference-lost.wkb');p.write_bytes(lost.wkb);rec['WKB_path']=str(p.resolve());rec['WKB_SHA256']=C.sha(lost.wkb)
    bridge=box(369,127.4,376.5,128.9)
    for row in final.records['In1.Cu']:
        if row['kind']=='fill' or not row['shape'].intersects(bridge.buffer(.6)):continue
        foreign.append({'uuid':row['uuid'],'key':list(row.get('key',('physical-hole',row['uuid']))),'kind':row['kind'],'net':row.get('net'),'bounds_mm':list(row['shape'].bounds),'owned_new':row['uuid'] in new})
    errors,clear,anti=A.clearance(final,parsed,set(parsed),set())
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    losses,contacts,obligations,checks=R.proof_contacts(base,final,smasks,masks,removed,parts,prior)
    gapdir=HERE/'ao1-mon-r16-signal-reference-gaps';gapdir.mkdir();gaps=GD.diagnose(base,final,parsed,removed,smasks,refs,now,gapdir)
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    report={'verdict':'EXACT_PARTIAL_AO1_MON_REFERENCE_DIAGNOSIS_NO_CANDIDATE_CREDIT','source_SHA256':C.sha(raw),'native_template_proof':padproof,'removed_exact_UUIDs':sorted(removed),'partial_new_chunks':{u:ch.decode() for u,ch in new.items()},'paths':case['paths'],'nomination_returns':case['nomination_returns'],'source_root_witness':witness,'original_source_root_witness':oldwitness,'MON_original_and_prospective_reference':mon,'unchanged_neighbour_reference_losses':unchanged,'reference_bridge_actual_native_entities':foreign,'full_shape_files':files,'partial_fill_errors':fillerrors,'partial_fill_contact_ledger':ledger,'partial_clearance_errors':errors,'partial_pad_losses':losses,'partial_surviving_contact_losses':contacts,'partial_surviving_contact_ledger':obligations,'native_source_partition_checks':checks,'partial_signal_reference_gaps':gaps,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen source/helper changed '+p)
    OUT.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(OUT),'fill_errors':len(fillerrors),'unchanged_reference_losses':len(unchanged),'signal_reference_gaps':len(gaps),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
