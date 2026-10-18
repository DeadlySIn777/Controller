"""Fresh parent-only successor after the exact health overlay executes once."""
from pathlib import Path
import copy,json,csv,hashlib
from hardware_build_assembly import parse,dump,child,children,value,q
from hardware_apply_motor_feed_reset import apply_feed_reset,footprint_text
LEDGER={'id': 'MB-MOTOR-FEED-POR-001', 'parent_only_override': True, 'inherited_child_and_Source26_immutable': True, 'frozen_candidate': 'reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04', 'frozen_receipt_sha256': 'c75808eba7431a3cbb2c2c39758dbc28c92f028768f9e3c46a0f66c3089e6a0a', 'frozen_primary_review_sha256': '1d69e09169fa11917b1b358e82f20c6956455ee50a38b8117ba61cbb78ff2395', 'exact_added_references': ['C11089', 'C11090', 'C11091', 'C11092', 'R11082', 'R11083', 'U11035', 'U11036', 'U11037', 'U11038'], 'exact_existing_native_pin_changes': [{'reference': 'U11032', 'pin': '6', 'old': '/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A', 'new': '/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A'}, {'reference': 'U11034', 'pin': '6', 'old': '/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B', 'new': '/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B'}], 'physical_qualified': False}
def apply_generated_parent_feed_reset(folder,root):
 folder=Path(folder);root=Path(root).resolve();model=json.loads((folder/'design.json').read_text());mapping=json.loads((folder/'assembly-map.json').read_text())
 trees={name:parse((folder/(name+'.kicad_sch')).read_text())for name in('mc_local_power','motherboard_power_entry')}
 trees,new,receipt=apply_feed_reset(trees,model)
 for name,tree in trees.items():(folder/(name+'.kicad_sch')).write_text(dump(tree)+'\n')
 libdefs=[]
 for d in children(child(trees['motherboard_power_entry'],'lib_symbols'),'symbol'):
  if value(d[1]).startswith('CNC_MB_FeedReset:'):
   d=copy.deepcopy(d);d[1]=q(value(d[1]).split(':')[1]);libdefs.append(d)
 (folder/'CNC_MB_FeedReset.kicad_sym').write_text(dump(['kicad_symbol_lib',['version','20241209'],['generator',q('motherboard_feed_reset')]]+libdefs)+'\n')
 pretty=folder/'CNC_MB_FeedReset.pretty';pretty.mkdir(exist_ok=False)
 for n in(5,6):(pretty/('TI_DBV'+str(n)+'.kicad_mod')).write_text(footprint_text(n))
 for filename,table,uri,kind in(('fp-lib-table','fp_lib_table','CNC_MB_FeedReset.pretty','KiCad'),('sym-lib-table','sym_lib_table','CNC_MB_FeedReset.kicad_sym','KiCad')):
  tree=parse((folder/filename).read_text());tree.append(parse('(lib(name "CNC_MB_FeedReset")(type "'+kind+'")(uri "${KIPRJMOD}/'+uri+'")(options "")(descr "Exact manufacturer receiving CLR source"))'));(folder/filename).write_text(dump(tree)+'\n')
 mapping['physical_parts']=2698;mapping['reviewed_motor_feed_reset_delta']=copy.deepcopy(LEDGER)
 deps=(root/'tools/hardware_apply_motor_feed_reset.py',Path(__file__).resolve())
 for dep in deps:
  key=dep.relative_to(root).as_posix()if dep.is_relative_to(root)else str(dep);h=hashlib.sha256(dep.read_bytes()).hexdigest()
  for m in(new['source_sha256'],mapping['input_sha256']):m[key]=h
 (folder/'design.json').write_text(json.dumps(new,indent=2)+'\n');(folder/'assembly-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
 with(folder/'bom.csv').open(newline='',encoding='utf8')as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
 byref={row['Reference']:row for row in rows}
 for ref in('R11074','R11078'):
  part=new['components'][ref];byref[ref].update(MPN=part['mpn'],Value=part['value'])
 for ref in receipt['exact_added_references']:
  part=new['components'][ref];row={key:''for key in fields};row.update(Reference=ref,MPN=part['mpn'],Value=part['value'],Footprint=part['footprint'],DNP='false',Scope='actual_on_motherboard_component_candidate',Status=part['status']);rows.append(row)
 with(folder/'bom.csv').open('w',newline='',encoding='utf8')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return receipt
