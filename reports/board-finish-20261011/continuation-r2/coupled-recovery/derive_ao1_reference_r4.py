"""Bind the actual r06 DAC/decoupler relation; minimal unchanged-SDI branch."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;p=HERE/'ao1_reference_coupled_r3.py';t=p.read_text()
t=t.replace("OUT=HERE/'ao1-reference-coupled-r3.json'","OUT=HERE/'ao1-reference-coupled-r4.json'")
t=t.replace('U14636.7#0','C14643.1#0')
t=t.replace("removed=set(recipe['deletes']);withdrawn=set(recipe['restores'])","removed=set();withdrawn=set(recipe['restores'])\n    lost=json.loads(A.read(HERE/'conflict-graph.json'))['lost_route_rows']\n    relation=next(r for r in lost if r['net']==VREF)['native_lost_relationships'][0]['r06_pad_relationship']\n    if set(relation)!={'C14643.1#0','U14626.9#0'}:raise ValueError('Exact original lost VREF relation differs')")
t=t.replace('for vat in vsite[:6]:','for vat in vsite[:20]:')
t=t.replace('for sat in ssites[:12]:','for sat in [None]:')
t=t.replace('            if math.dist(vat,sat)<.81:continue\n','')
t=t.replace('for net,at in ((VREF,vat),(SDI,sat)):','for net,at in ((VREF,vat),):')
t=t.replace('case_refs=body_refs(refs,[vat,sat],gaps,initial)','case_refs=body_refs(refs,[vat],gaps,initial)')
t=t.replace('returns=[];all_positions=[vat,sat]','returns=[];all_positions=[vat]')
t=t.replace("jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets),(SDI,'F.Cu',[sstart],[sat]),(SDI,'In3.Cu',[sat],target_seeds)]","jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets)]")
needle="            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=returns)"
replacement="""            old_sdi_reference=[];old_sdi_loss=[]
            for z in base.own[SDI]:
                if z['kind']!='track' or z['layer'] not in frefs:continue
                before=z['shape'].intersection(refs[z['layer']]);lost=before.difference(frefs[z['layer']]).area
                row={'uuid':z['uuid'],'layer':z['layer'],'unchanged_exact_source_copper':True,'original_source_reference_uncovered_mm2':z['shape'].difference(refs[z['layer']]).area,'previously_source_rooted_full_body_reference_lost_mm2':lost}
                old_sdi_reference.append(row)
                if lost>1e-9:old_sdi_loss.append(row)
            ref_errors+=old_sdi_loss
            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=returns,unchanged_SDI_source_reference_preservation=old_sdi_reference)
"""
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("'component_diagnostic':diagnostic","'component_diagnostic':diagnostic,'exact_original_recovered_relation':relation,'all4_current_SDI_items_byte_exact':True,'existing_SDI_full_electrical_qualification':'OPEN; source/rooted-reference contact preservation is recorded separately from original full-body SI coverage'")
q=HERE/'ao1_reference_coupled_r4.py'
if q.exists():raise ValueError('Fresh r4 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-reference-r4-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'changes':['Bind exact original native lost C14643.1/U14626.9 pad relation, not a different same-net source pad','Retain every current SDI chunk; move only the seven absent original VREF withdrawables into a new ordinary F/B transition','Recheck complete VREF/SDI original/current/surviving Cu and preserve every previously source-rooted unchanged SDI body projection after new VREF/return cuts; report existing baseline SI coverage separately'],'board_emitted':False},indent=1)+'\n')
print('Minimal exact-relation r4 syntax PASS')
