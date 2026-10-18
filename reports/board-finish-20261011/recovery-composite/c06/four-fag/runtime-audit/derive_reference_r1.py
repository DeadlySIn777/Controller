"""Distinct audit derivation: own-ground connectivity honors native annuli."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;STAGE=HERE.parent
base=STAGE/'audit_combined.py'
raw=base.read_text()
raw=raw.replace("HERE = Path(__file__).resolve().parent", "HERE = Path(__file__).resolve().parent.parent\nOUTPUT = Path(__file__).resolve().parent / 'strict-reference-r1.json'")
raw=raw.replace("destination = HERE / 'combined-audit.json'", "destination = OUTPUT")
raw=raw.replace("    anchor=model.pads['J11001.2#0']", '''    anchor=model.pads['J11001.2#0']
    S.read(Path(__file__))
    native_old=json.loads(S.read(S.overlay_tool.base.GEOM))
    native_vias={row['uuid']:row for row in native_old['vias']}
    native_new=json.loads(S.read(V.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    if native_new['verdict']!='PASS' or native_new['candidate_sha256']!=contract['candidate_sha256']:
        raise ValueError('Current added-via native provenance differs')
    new_actual={row['uuid']:row['actual_flashed_layers'] for row in native_new['native_api']['added_via_annuli']['rows']}
    actual_masks={};mask_provenance=[];mask_withheld=[]
    for via in g['vias']:
        if S.norm(via['net'])!='/LOGIC_GND':continue
        uid=via['uuid'];chunk=original[4][uid]
        if old[4].get(uid)==chunk and uid in native_vias:
            observed=native_vias[uid]
            if any(via[key]!=observed[key] for key in ('x','y','d','drill')):raise ValueError('Inherited native via geometry differs')
            actual_masks[uid]=set(observed['flashed'])
            mask_provenance.append({'uuid':uid,'source':'exact unchanged r06 native geometry','flashed':observed['flashed']})
        elif uid in new_actual:
            actual_masks[uid]=set(new_actual[uid])
            mask_provenance.append({'uuid':uid,'source':'same-candidate native API','flashed':new_actual[uid]})
        elif b'(layers "F.Cu" "B.Cu")' in chunk and not any(flag in chunk for flag in (b'remove_unused_layers',b'start_end_only',b'via blind',b'via micro')):
            actual_masks[uid]=set(g['copper_layers'])
            mask_provenance.append({'uuid':uid,'source':'changed through-via exact ordinary KEEP_ALL source flags; no suppression override','flashed_source_default':g['copper_layers']})
        else:
            actual_masks[uid]=set();mask_withheld.append(uid)
    excluded={layer:[uid for uid,mask in actual_masks.items() if layer not in mask] for layer in ('In1.Cu','In4.Cu')}
''')
raw=raw.replace("own=[r['shape'] for r in model.records[layer] if r['net']=='/LOGIC_GND' and r['kind'] in ('pad','via','track')]", "own=[r['shape'] for r in model.records[layer] if r['net']=='/LOGIC_GND' and r['kind'] in ('pad','via','track') and (r['kind']!='via' or layer in actual_masks.get(r['uuid'],set()))]")
raw=raw.replace("'old_foreign_via_cutters':len(foreign)}", "'old_foreign_via_cutters':len(foreign),'own_LOGIC_vias_excluded_for_unflashed_annulus':len(excluded[layer]),'unknown_own_vias_withheld':len(mask_withheld)}")
raw=raw.replace("'native_jobs':0,'adopted':False", "'own_ground_via_mask_provenance':mask_provenance,'unknown_own_vias_withheld':mask_withheld,'own_unflashed_vias_by_plane':excluded,'native_jobs':0,'adopted':False")
raw=raw.replace("'four-fag-independent-prospective-reference-v1'", "'four-fag-strict-own-annuli-prospective-reference-r1'")
target=HERE/'audit_reference_r1.py'
if target.exists():raise ValueError('Distinct strict audit already exists')
target.write_text(raw,encoding='utf-8')
receipt={'base':str(base),'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'derived':str(target),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'delta':'Own LOGIC_GND source component uses actual unchanged native flashed annuli; unknown changed conditional vias withheld. Foreign clearance remains conservative all-layer. Exact same candidate and all7 antipads.'}
(HERE/'reference-r1-derivation.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
print(json.dumps(receipt))
