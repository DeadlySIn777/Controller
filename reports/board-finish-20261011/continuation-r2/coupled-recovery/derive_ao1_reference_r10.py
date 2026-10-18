"""Preserve r9 evidence, replace only bounded circular-return nomination."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r9.py').read_text().replace('import ao1_via_region_r2 as VR','import ao1_via_region_r2 as VR\nimport ao1_continuous_return_r1 as CR')
source=source.replace("OUT=HERE/'ao1-reference-coupled-r9.json'", "OUT=HERE/'ao1-reference-coupled-r10.json'")
source=source.replace("('ao1-r9-initial-'", "('ao1-r10-initial-'").replace("('ao1-r9-legal-centres-'", "('ao1-r10-legal-centres-'")
start=source.index('    single={};single_diagnostics={}')
end=source.index('    pairs=sorted(',start)
source=source[:start]+"""    frozen=json.loads(A.read(HERE/'ao1-reference-coupled-r9.json'))
    if frozen['source_sha256']!=C.sha(raw) or frozen['native_template_proof']!=padproof:raise ValueError('Frozen single-site nomination source differs')
    single_diagnostics=frozen['component_diagnostic']['reference_aware_site_nomination']
    single={n:[tuple(p) for p in single_diagnostics[n]['individually_continuous_sites']] for n in (VREF,SDI)}
    # Frozen points nominate only; exact final serialized rebuild and all gates
    # remain independent of this preserved earlier bounded reachability receipt.
"""+source[end:]
source=source.replace("nominations=[((373.4,128.3),(374.2,128.5))", "nominations=[((373.4,128.3),(374.225,128.4)),((373.4,128.3),(374.2,128.5))")
start=source.index('                for radius in (() if chosen else (.85,.9,.95,1.)):')
end=source.index("                if chosen is None:attempt['failures'].append",start)
source=source[:start]+"""                if chosen is None:
                    sites,space,physical,areas=CR.candidates(return_region,case_refs,at,all_positions)
                    attempt.setdefault('continuous_return_nomination',[]).append({'net':net,'signal_at_mm':at,'areas_mm2':areas,'candidate_count':len(sites),'exact_space_WKB_sha256':C.sha(space.wkb),'exact_physical_space_WKB_sha256':C.sha(physical.wkb),'space_bounds_mm':list(space.bounds) if not space.is_empty else []})
                    for ret in sites:
                        body=Point(ret).buffer(.25,resolution=128);hole=Point(ret).buffer(.1,resolution=128);ann=body.difference(hole)
                        if not all(case_refs[layer].buffer(-.075).intersection(ann).area>=.004 for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
                        chosen=ret;break
                    if chosen is None:
                        probes=[(at[0],at[1]+.9),(at[0]-.7,at[1]+.65),(at[0]-.7,at[1]-.65),(at[0]+.7,at[1]+.65)]
                        attempt.setdefault('failed_return_exact_blocker_probes',[]).append({'net':net,'signal_at_mm':at,'probes':[{'at_mm':ret,'ordinary_geometry_blockers':CR.site_blockers(temp,COM,ret,smd,centres,all_positions),'source_rooted_plane_annular_interior_mm2':{layer:case_refs[layer].buffer(-.075).intersection(Point(ret).buffer(.25,resolution=128).difference(Point(ret).buffer(.1,resolution=128))).area for layer in ('F.Cu','B.Cu')}} for ret in probes]})
"""+source[end:]
target=here/'ao1_reference_coupled_r10.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r10-syntax-only.pyc'))
print('Fresh r10 syntax PASS; continuous exact ordinary return geometry')
