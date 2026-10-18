"""Ground the second bare COM component using its actual .610334 mm SOURCE gap."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_U14624_actual_minimum_F_ground_bridge_r640.py';dest=H/'construct_AO1_COM_U14636_actual_minimum_F_ground_bridge_r652.py';assert not dest.exists();text=src.read_text().replace('r640','r652').replace('R640_','R652_').replace('U14624-3','U14636-3').replace("islands['islands'][1]","islands['islands'][4]").replace("p['ref']=='U14624'and p['pin']=='3'","p['ref']=='U14636'and p['pin']=='3'").replace("r['uuid']=='19434a4b-d4ed-4193-90b1-b90a71062411'","r['uuid']=='53ea5aa5-a009-4367-accd-c5b6de94f6fd'").replace('actual_BEFORE_U14624_3_island_metal_overlap_mm2','actual_BEFORE_U14636_3_island_metal_overlap_mm2').replace('ACTUAL_COM_SOURCE_TO_U14624_3','ACTUAL_COM_SOURCE_TO_U14636_3')
assert 'win=box(351,140,363,149)' in text;text=text.replace('win=box(351,140,363,149)','win=box(363,112,377,127)').replace('[[355.898,143.9],[356.898,143.85]]','[[367.521196787937,118.12826652802909],[368.076806,118.380866]]')
dest.write_text(text);print('R652_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
