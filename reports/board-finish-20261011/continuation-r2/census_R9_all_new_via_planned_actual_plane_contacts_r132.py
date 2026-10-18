"""Distinguish new-via layer flashes from actual same-net plane contacts."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'census_R9_owned_same_net_drill_intent_contacts_r131.py';code=source.read_text()
needle="OUT=H/'R9-owned-same-net-drill-intent-vs-actual-contact-census-r131'";assert code.count(needle)==1
code=code.replace(needle,"OUT=H/'R9-all-new-via-planned-vs-actual-plane-contact-census-r132'")
needle="    write(OUT/'all-owned-hole-annular-contact-rows.json',rows);";assert code.count(needle)==1
extra="""    allcontacts=[]
    for v in h['vias']:
        if v['uuid'] not in new_ids:continue
        pt=Point(v['x'],v['y']);ann=pt.buffer(v['d']/2,quad_segs=256).difference(pt.buffer(v['drill']/2,quad_segs=256))
        for layer in v['flashed']:
            planned_zones=[q for q in z if C.norm(q['net'])==C.norm(v['net']) and q['layer']==layer and q['shape'].intersects(ann)]
            planned=unary_union([q['shape'] for q in planned_zones]).intersection(ann).area
            if planned<=.01:continue
            key=(C.norm(v['net']),layer);xs=actual.get(key,[]);tree=actualtrees.get(key);indices=tree.query(ann,predicate='intersects') if tree is not None else []
            actualnear=unary_union([xs[int(k)] for k in indices]);overlap=actualnear.intersection(ann).area
            allcontacts.append({'new_via_UUID':v['uuid'],'raw_net':v['net'],'layer':layer,'centre_mm':[v['x'],v['y']],'planned_owned_zone_UUIDs':[q['uuid'] for q in planned_zones],'planned_physical_annular_overlap_mm2':planned,'actual_any_same_net_same_layer_zone_overlap_mm2':overlap,'actual_layer_flashed':layer in flashes[v['uuid']],'no_actual_plane_contact':overlap==0.})
    write(OUT/'all-new-via-planned-vs-actual-contact-rows.json',allcontacts)
    contact_deficits=[r for r in allcontacts if r['no_actual_plane_contact']];write(OUT/'all-new-via-actual-zero-plane-contact-rows.json',contact_deficits)
    print('R132_NEW_VIA_CONTACTS',len(allcontacts),'ZERO',len(contact_deficits),'by_net',{n:sum(r['raw_net']==n for r in contact_deficits) for n in sorted({r['raw_net'] for r in contact_deficits})},flush=True)
"""
code=code.replace(needle,extra+needle)
needle="'rows_sha256':sha(OUT/'all-owned-hole-annular-contact-rows.json')";assert code.count(needle)==1
code=code.replace(needle,"'all_new_via_positive_planned_contact_rows':len(allcontacts),'all_new_via_zero_actual_plane_contact_count':len(contact_deficits),'all_new_via_contact_ledger_sha256':sha(OUT/'all-new-via-planned-vs-actual-contact-rows.json'),"+needle)
exec(compile(code,str(source),'exec'))
