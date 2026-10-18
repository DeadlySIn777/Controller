from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'search_CDone_continuous_ordinary_source_ports_r29.py'
s=p.read_text().replace('source-search-r29','source-search-r30')
s=s.replace("K.Z.bounded_disk([v['x'],v['y']],", "K.Z.bounded_disk(v,")
s=s.replace("K.Z.bounded_disk(z['at'],", "K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},")
s=s.replace("K.Z.bounded_disk(circle[p['uuid']]['at'],", "K.Z.bounded_disk({'x':circle[p['uuid']]['at'][0],'y':circle[p['uuid']]['at'][1]},")
(H/'search_CDone_continuous_ordinary_source_ports_r30.generated.py').write_text(s)
