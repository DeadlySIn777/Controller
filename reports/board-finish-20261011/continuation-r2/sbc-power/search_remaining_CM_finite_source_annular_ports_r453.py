"""Keep R452 strict full-disk rejection; screen finite true SOURCE annuli."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'search_remaining_CM_actual_source_local_ground_ports_r452.py').read_text(encoding='utf-8')
s=s.replace('CM51-seven-missing-bounded-real-SOURCE-before-local-ordinary-ground-ports-r452','CM51-seven-missing-finite-partial-SOURCE-annulus-local-ground-ports-r453')
s=s.replace("for sh in planes.values():source=source.intersection(sh.buffer(-.251,quad_segs=128))","for sh in planes.values():source=source.intersection(sh.buffer(.249,quad_segs=128))")
s=s.replace("(OUT/'bounded-fully-source-contained-new-port-free.wkb').write_bytes(source.wkb)","(OUT/'bounded-finite-SOURCE-nearby-port-free.wkb').write_bytes(source.wkb);(OUT/'bounded-full20-F-centre-free.wkb').write_bytes(ffree.wkb)")
s=s.replace("'genuine_source_port_free_area_mm2':local.area","'all_layer_port_free_in_same_F_component_mm2':vfree.intersection(start.buffer(radius,quad_segs=128)).intersection(face).area if face is not None else 0,'genuine_partial_source_port_free_area_mm2':local.area")
s=s.replace("'source_containment_margin_mm':.251","'finite_annulus_SOURCE_search_expansion_mm':.249,'full_disk_containment_required':False")
s=s.replace('R452-ground-port:','R453-ground-port:').replace('R452-ground-track:','R453-ground-track:').replace("'R452_ROUTE'","'R453_ROUTE'").replace("'R452_COMPLETE'","'R453_COMPLETE'")
E=P/'exact-expanded-finite-annular-CM-port-search-r453.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
