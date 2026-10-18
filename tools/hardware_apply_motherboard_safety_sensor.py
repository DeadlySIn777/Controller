"""Exact additive integration corrections for XS1 sensor acquisition and B-LDO feed.
No source, PCB or copper is changed by the callable transforms.
"""
import copy,uuid
from hardware_build_assembly import child,children,value,q,point
from hardware_apply_motherboard_io3_upgrade import symbol_for,coords,exact_label
NS=uuid.UUID('6e3c494b-9dcc-5019-8431-c01b8d42c34b')

def apply_safety_sensor_endpoints(tree,model,scope):
 t,m=copy.deepcopy(tree),copy.deepcopy(model);p=m['components'] if 'components' in m else m;receipt=[]
 if scope=='power_entry':
  u=p.get('U11018',{});expected={'1':'DOB_FIELD_3V3','2':None,'3':None,'4':'FIELD_B_0V','5':'FIELD_B_24V_PROTECTED','6':None,'7':None,'8':'FIELD_B_24V_PROTECTED','9':'FIELD_B_0V'}
  if u.get('mpn')!='TPS7A1633DGNR' or u.get('pins')!=expected:raise ValueError('Unreviewed exact field-B LDO')
  for n in ['5','8']:
   lab=exact_label(t,'U11018',n,expected[n]);lab[1]=q('FIELD_B_5V_PRE');u['pins'][n]='FIELD_B_5V_PRE';receipt.append({'ref':'U11018','pin':n,'old':expected[n],'new':'FIELD_B_5V_PRE'})
 elif scope=='io_control':
  u=p.get('U13001',{});expected={'42':('PB3','DIC_SENSOR_SCL'),'43':('PB4','DIC_SENSOR_SDA')}
  if u.get('mpn')!='STM32G031C8T6' and u.get('mpn')!='STM32G031C8T6TR':raise ValueError('Unreviewed DIC part')
  ends,definition=coords(t,symbol_for(t,'U13001'));names={value(child(x,'number')[1]):value(child(x,'name')[1]) for sub in children(definition,'symbol') for x in children(sub,'pin')}
  for n,(gpio,net) in expected.items():
   if u['pins'].get(n) is not None or names.get(n)!=gpio:raise ValueError('Spare DIC GPIO is not exactly NC '+n)
   xy=ends[n];nc=[x for x in children(t,'no_connect') if point(child(x,'at'))==xy]
   if len(nc)!=1:raise ValueError('Expected one physical DIC NC endpoint')
   t.remove(nc[0]);t.append(['label',q(net),['at',str(xy[0]),str(xy[1]),'0'],['effects',['font',['size','.65','.65']],['justify','left','bottom']],['uuid',q(str(uuid.uuid5(NS,n+net)))] ]);u['pins'][n]=net;receipt.append({'ref':'U13001','pin':n,'old':None,'new':net,'gpio':gpio,'mode':'GPIO software open-drain I2C; target firmware not implemented'})
 else:raise ValueError('Unreviewed source scope')
 return t,m,{'scope':scope,'exact_endpoint_changes':receipt,'all_other_parts_pins_properties_preserved':True,'physical_qualification':False}
