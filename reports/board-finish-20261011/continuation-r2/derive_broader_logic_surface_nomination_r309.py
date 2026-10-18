"""Continue the short-surface constructor on further existing native joins."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_short_current_logic_surface_connections_r307.py';target=H/'nominate_broader_current_logic_surface_connections_r309.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not target.exists();code=source.read_text()
old="pairs=[r for r in pairs if '/USB_' not in r['normalized_net'] and '/HDMI_' not in r['normalized_net'] and '/MIPI_' not in r['normalized_net']]"
new="""pairs=[r for r in pairs if '/USB_' not in r['normalized_net'] and '/HDMI_' not in r['normalized_net'] and '/MIPI_' not in r['normalized_net']]
 widerfile=census.parent/'all-745-native-split-net-census.json'
 wider=[r['nearest_common_surface_pad_pair']for r in json.loads(widerfile.read_bytes()) if r['native_domain']=='DOM_LOGIC' and r['nearest_common_surface_pad_pair'] and 5<r['nearest_common_surface_pad_pair']['centre_span_mm']<=15]
 wider.sort(key=lambda r:r['centre_span_mm']);pairs.extend(wider)
 pairs=[r for r in pairs if not any(tag in r['normalized_net'] for tag in ('/USB_','/HDMI_','/MIPI_')) and not any(v.startswith(('J15001.','J15002.','U1001.','R10007.','R10016.','U146','R146','C146')) for v in (r['native_left_pad'],r['native_right_pad']))][:160]"""
assert code.count(old)==1;code=code.replace(old,new)
old="'pairs_screened':len(pairs),"
new="'wider_native_census_SHA256':sha(widerfile),'bounded_endpoint_centre_span_mm':[0,15],'FPGA_compute_connector_and_AO1_owned_endpoint_scopes_excluded':True,'pairs_screened':len(pairs),"
assert code.count(old)==1;code=code.replace(old,new)
code=code.replace('r307','r309').replace('R307','R309');compile(code,str(target),'exec');target.write_text(code)
receipt=H/'broader-current-logic-surface-derivation-r309.json';assert not receipt.exists()
receipt.write_text(json.dumps({'source_file':str(source),'source_SHA256':sha(source),'derived_file':str(target),'derived_SHA256':sha(target),'change':'extend to actual native nearest common-surface residuals up to15mm; exclude other active ownership and controlled differential interfaces','conservative_width_true_clearance_allholes_rules_existing_Cu_and_no_mutation_policy_unchanged':True,'all_matching_FULL_AFTER_source_reference_current_native_gates_OPEN':True,'adopted':False},indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
