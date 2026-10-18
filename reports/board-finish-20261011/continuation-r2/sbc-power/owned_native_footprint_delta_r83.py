"""Exact R17031 translation authorizer for final host/native recipe emission."""
import json,hashlib
from pathlib import Path
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def collect(binding,base,head):
    native=[];pads={};fps={};pins=[]
    for spec in binding.get('existing_native_owned_footprint_replacement_recipes',[]):
        f=Path(spec['file']);assert sha(f)==spec['sha256'];recipe=json.loads(f.read_text());rows=recipe['native_existing_owned_footprint_replacement_rows'];assert len(rows)==1
        source=Path(spec['source_contact_audit_file']);geometry=Path(spec['independent_geometry_audit_file']);ledger=Path(spec['host_pose_ledger_file'])
        for path,key in [(source,'source_contact_audit_sha256'),(geometry,'independent_geometry_audit_sha256'),(ledger,'host_pose_ledger_sha256')]:assert sha(path)==spec[key]
        sr=json.loads(source.read_text());gr=json.loads(geometry.read_text());assert sr['CORE_bare_named_groups']==[] and sr['OBS15_all_prior_physical_pad_track_via_layer_relationships_retained'] is True and gr['errors']==[]
        for row in rows:
            assert row['ref']=='R17031' and row['uuid']=='22ecc877-cc67-4abe-8582-59c4abee8832'
            for pathkey,digestkey in [('original_chunk_file','original_chunk_sha256'),('replacement_chunk_file','replacement_chunk_sha256'),('authorizing_recipe_file','authorizing_recipe_sha256')]:assert sha(row[pathkey])==row[digestkey]
            assert row['original_root_pose_mm_deg']==[250.752,32.697,0.] and row['replacement_root_pose_mm_deg']==[247.252,34.197,0.]
            native.append(row)
        records=json.loads(ledger.read_text());bp={q['uuid']:q for q in base['pads']};hp={q['uuid']:q for q in head['pads']}
        for r in records:
            if r['kind']=='pad':
                uid=r['uuid'];assert uid not in pads and r['original_geometry']==bp[uid] and r['replacement_geometry']==hp[uid];assert r['original_geometry']['ref']==r['replacement_geometry']['ref']=='R17031';assert r['original_geometry']['net']==r['replacement_geometry']['net'];pads[uid]=r
            elif r['kind']=='footprint':
                ref=r['ref'];assert ref=='R17031' and r['translation_mm']==[-3.5,1.5];assert r['original_geometry']==next(q for q in base['footprints'] if q['ref']==ref);assert r['replacement_geometry']==next(q for q in head['footprints'] if q['ref']==ref);fps[ref]=r
            else:raise ValueError('Unknown pose delta')
        assert set(pads)=={'1aa9d7d6-1ea4-4c3d-91f0-de0b4ac416b4','fa1831f5-068d-433f-8653-c70d19ffbbaf'}
        pins.append(spec)
    prior={q['ref']:q for q in base['footprints']};now={q['ref']:q for q in head['footprints']};assert prior.keys()==now.keys()
    for ref in prior:
        if ref in fps:assert now[ref]==fps[ref]['replacement_geometry']
        else:assert now[ref]==prior[ref],('Unlisted footprint metadata/courtyard change',ref)
    return native,pads,pins
