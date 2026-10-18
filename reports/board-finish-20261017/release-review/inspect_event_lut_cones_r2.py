"""Bounded structural mapped-LUT cone census, no source or native changes."""
from pathlib import Path
import re,json,hashlib,collections
H=Path(__file__).resolve().parent
P=H/'event-capture-select-r2/native-events-map/literal-case/outflow/cnc3_runtime_events.map.v'
def norm(x):return x.strip().lstrip('\\')
def main():
 text=P.read_text().split('endmodule',1)[0]
 graph={};kind={};ffs=[];allprims=collections.Counter()
 for match in re.finditer(r'\b(EFX_LUT4|EFX_ADD|EFX_FF|EFX_GBUFCE)\s+(\S+)\s+\((.*?)\)\s*/\*',text,re.S):
  typ,name,body=match.groups();name=norm(name)
  ports={key:norm(value) for key,value in re.findall(r'\.(\w+)\(([^()]*)\)',body)}
  allprims[typ]+=1
  if typ=='EFX_FF':ffs.append((name,ports));continue
  outputs={'EFX_LUT4':['O'],'EFX_ADD':['O','CO'],'EFX_GBUFCE':['O']}[typ]
  for port in outputs:
   if port not in ports:continue
   graph[ports[port]]=[v for k,v in ports.items() if k not in outputs]
   kind[ports[port]]=(typ,name)
 for lhs,rhs in re.findall(r'\bassign\s+(\\?[^\s=]+)\s*=\s*(\\?[^\s;]+)\s*;',text):
  if '{' not in rhs and not re.search(r"[&|^?:]",rhs):graph.setdefault(norm(lhs),[norm(rhs)])
 groups=collections.defaultdict(list)
 for name,ports in ffs:
  base=name.split('[')[0].split('~')[0];groups[base].append(ports['D'])
  m=re.match(r'write_data\[(\d+)\]',name)
  if m:
   bit=int(m[1])%160
   field='payload' if bit<96 else 'ticks' if bit<128 else 'flags' if bit<136 else 'origin' if bit<144 else 'kind' if bit<152 else 'sequence'
   groups['WRITE_DATA_FIELD/'+field].append(ports['D'])
 def trace(roots):
  todo=list(roots);seen=set();instances=set();leaves=set()
  while todo:
   net=todo.pop()
   if net in seen:continue
   seen.add(net)
   if net in kind:instances.add(kind[net])
   if net in graph:todo.extend(graph[net])
   else:leaves.add(net)
  return instances,leaves
 result={}
 for name,roots in groups.items():
  instances,leaves=trace(roots)
  result[name]={'FF_D_roots':len(roots),'cone_primitives':dict(collections.Counter(t for t,n in instances)),'leaf_count':len(leaves),'sample_leaves':sorted(leaves)[:8]}
 record={'status':'READ_ONLY_TOP_MODULE_REGISTER_D_COMBINATIONAL_CONE_CENSUS','scope':'scalar primitive port connectivity and direct scalar/vector aliases; group cones overlap; not timing, resource attribution equivalence or source optimization proof','native_top_primitives_parsed':dict(allprims),'groups':result,'native_netlist_SHA256':hashlib.sha256(P.read_bytes()).hexdigest()}
 out=H/'event-capture-select-r2/mapped-register-cone-census.json';out.write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k.startswith('WRITE_DATA') or k in ['write_data','write_address','write_enable','next_sequence','count','wr','rd']},indent=2))
if __name__=='__main__':main()
