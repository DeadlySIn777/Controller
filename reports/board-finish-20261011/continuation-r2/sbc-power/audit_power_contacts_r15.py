"""Complete old power contact obligations on the coupled crossing candidate."""
import pickle,json,hashlib
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
import complete_geometry_r2 as G
import io3_contact_restore_r2 as Q
L=G.L;p=G.p;SBC='/motherboard_power_entry/SBC_5V';OUT=L.OUT/'power-contact-audit-r15b'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();cache=L.OUT/'io3-field-crossings-r15/model.pkl';g,h,binding,zones,candidate=pickle.loads(cache.read_bytes());rows=[];allgroups={}
    for net in (p.norm(L.stage.caps.CORE),SBC,'/CORE_1V2','/IO_3V3'):
        Q.NET=net;before,_,_=Q.groups(g,return_details=True);after,parts,assign=Q.groups(candidate,return_details=True);allgroups[net]=(before,after,parts,assign)
        oldids={q['uuid'] for group in before for q in group};byid={q['uuid']:i for i,group in enumerate(after) for q in group};lost=[];missing=[]
        for oldindex,group in enumerate(before):
            split={}
            for q in group:
                if q['uuid'] not in byid:missing.append(q)
                else:split.setdefault(byid[q['uuid']],[]).append(q)
            if len(split)>1:lost.append({'old_group':oldindex,'old_contacts':len(group),'new_groups':[{'id':i,'contacts':qs} for i,qs in split.items()]})
        source_ref=('L11001','2') if net==p.norm(L.stage.caps.CORE) else ('U11012','8') if net==SBC else ('U2001','2') if net=='/CORE_1V2' else ('U2002','2')
        source=[(i,q) for i,group in enumerate(after) for q in group if (q['ref'],str(q['pad']))==source_ref];sourceids={i for i,q in source}
        zones_in_source=[]
        for q in zones:
            if p.norm(q['net'])!=net:continue
            partsids={i for part,i in zip(parts[q['layer']],assign[q['layer']]) if part.intersects(q['shape'])};zones_in_source.append({'uuid':q['uuid'],'label':q['label'],'layer':q['layer'],'source_connected':bool(partsids&sourceids),'groups':sorted(x for x in partsids if x is not None),'area_mm2':q['shape'].area})
        loads=[{'group':i,**q,'source_connected':i in sourceids} for i,group in enumerate(after) for q in group if not q['ref'].startswith('@')]
        row={'net':net,'before_groups':len(before),'after_groups':len(after),'old_physical_contacts':len(oldids),'lost_old_relationships':lost,'missing_old_contacts':missing,'source_endpoint':source_ref,'source_groups':sorted(sourceids),'new_zones':zones_in_source,'all_named_pads':loads};rows.append(row);print('POWER_CONTACT',net,'groups',len(before),len(after),'lost',len(lost),'missing',len(missing),'source',sourceids,'new_zone_disconnected',sum(not q['source_connected'] for q in zones_in_source),flush=True)
        (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n')
    (OUT/'groups.pkl').write_bytes(pickle.dumps(allgroups,protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'HOST_CONTACT_AUDIT','model_sha256':sha(cache),'binding':binding,'rows':rows,'native_jobs':0,'board_written':False,'full_current_and_pad_free_plane_branches_open':True},indent=2)+'\n')
if __name__=='__main__':main()
