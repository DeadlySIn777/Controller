"""Route source-verified ordinary DI, reset and fault nets outside old catalog."""
import ast,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
HERE=F.HERE
def main():
    source=HERE/'current-logic-source-role-inventory-r2.json';raw=source.read_bytes();inventory=json.loads(raw)
    exact={'/motherboard_do/DOB_CONTROLLER_RESET_N','/motherboard_process/ACC_CONTROLLER_RESET_N','/motherboard_acc_control/AI_SENSOR_FAULT_HOST','/motherboard_do/DOA_FLT_N_HOST','/motherboard_io_control/DI_SAFETY_SECONDARY_FAULT','/motherboard_io_control/DI_SENSOR_G2_FAULT','/motherboard_operator/MPG_ENABLE_ACTIVE'}
    rows=[]
    for row in inventory['rows']:
        n=row['normalized_net']
        if n not in exact and not re.fullmatch(r'/motherboard_di/DI(?:[0-9]|1[0-9]|2[0-3])_LOGIC',n):continue
        if n in ('/motherboard_di/DI6_LOGIC','/motherboard_di/DI15_LOGIC'):continue
        ports=row['current_source_ports']
        if any(p['pintype'] in ('power_in','power_out') or 'CLK' in p['pinfunction'] for p in ports):raise ValueError('Nonordinary source port '+n)
        if not any(p['pintype'] in ('output','open_collector') for p in ports):raise ValueError('No current source drive role '+n)
        row=dict(row,category='ordinary_digital_catalog',classification='CURRENT_SOURCE_ORDINARY_ROLE_REVIEWED_FOR_GEOMETRY_PLANNING');rows.append(row)
    F.OUT=HERE/'current-di-fault-routes-r1';F.OUT.mkdir(exist_ok=False)
    policy=F.OUT/'current-source-policy.json'
    policy.write_text(json.dumps({'rows':rows,'source_inventory':str(source),'source_inventory_sha256':hashlib.sha256(raw).hexdigest(),'current_source_roles_reviewed':True,'routing_geometry_width_mm':.2,'no_controlled_clock_or_power_roles':True,'electrical_rise_load_timing_qualification':'OPEN','native_drc_connectivity':'OPEN','adopted':False},indent=1)+'\n',encoding='utf-8')
    original=Path(F.__file__);tree=ast.parse(original.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    changed=0
    for node in ast.walk(fn):
        if isinstance(node,ast.Constant) and node.value=='remaining-net-census-r2.json':node.value='current-di-fault-routes-r1/current-source-policy.json';changed+=1
        if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=='refs' and isinstance(node.slice,ast.Name) and node.slice.id=='ref_layer':
            # Full .2mm copper body plus .025mm geometry planning guard must
            # fit over the source-rooted reference, not only its centreline.
            parent=next((p for p in ast.walk(fn) if isinstance(p,ast.Call) and node in p.args),None)
            if parent and isinstance(parent.func,ast.Attribute) and parent.func.attr=='intersection':parent.args=[ast.Call(func=ast.Attribute(value=node,attr='buffer',ctx=ast.Load()),args=[ast.UnaryOp(op=ast.USub(),operand=ast.Constant(.125))],keywords=[])]
    if changed!=1:raise ValueError('Source-policy derivation mismatch')
    mk=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='mkdir');mk.keywords=[ast.keyword(arg='exist_ok',value=ast.Constant(True))]
    fn.body.insert(1,ast.parse('read(Path(__file__))').body[0])
    (F.OUT/'derivation.json').write_text(json.dumps({'original':str(original),'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'derived_main':ast.unparse(fn),'current_source_nets':len(rows),'native_jobs':0,'board_emitted':False,'all_physical_clearance_domain_reservation_thresholds_unchanged':True,'adopted':False},indent=1)+'\n',encoding='utf-8')
    namespace=dict(F.__dict__);namespace['__file__']=str(Path(__file__))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'current-source-di-fault-routing','exec'),namespace);namespace['main']()
if __name__=='__main__':main()
