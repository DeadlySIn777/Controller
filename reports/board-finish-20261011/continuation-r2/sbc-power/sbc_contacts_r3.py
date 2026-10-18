"""Original SBC pad/via/track partitions versus the concrete local F plane."""
import json,hashlib
from pathlib import Path
from shapely import from_wkb
import io3_contact_restore_r2 as Q
import local_copper_r3 as T
R=T.R
L=R.L;p=R.p
def records(poly):return [[list(x.exterior.coords),[list(h.coords) for h in x.interiors]] for x in p.hubs.components(poly)]
def main():
    g,h,_=T.model();d=json.loads((L.OUT/'SBC-F-bounded-bus-r3.json').read_text());row={'candidate_Cu_file':d['allocated_SBC_F_plane_file'],'sha256':d['allocated_plane_sha256']};plane=from_wkb(Path(row['candidate_Cu_file']).read_bytes())
    candidate={**h,'zones':h['zones']+[{'uuid':'prospective-SBC-F-plane','net':p.NET,'fills':{'F.Cu':records(plane)}}]}
    Q.NET=p.norm(p.NET);before,*_=Q.groups(g,return_details=True,plane_terminals=True);after,*_=Q.groups(candidate,return_details=True,plane_terminals=True)
    assign={r['uuid']:i for i,group in enumerate(after) for r in group};loss=[]
    for i,group in enumerate(before):
        # Removed private old tracks are separately ledgered, so preserve every
        # retained original contact plus all original functional pads/barrels.
        present=[r for r in group if r['uuid'] in assign];groups={assign[r['uuid']] for r in present}
        if len(groups)>1:loss.append({'old_group':i,'new_groups':sorted(groups),'retained_terminals':present})
    padgroups=[]
    for i,group in enumerate(after):
        pads=[r for r in group if not r['ref'].startswith('@')]
        if pads:padgroups.append({'group':i,'pads':pads})
    result={'exact_source_board':L.live.SHA,'before_groups':len(before),'after_groups':len(after),'retained_original_contact_partition_losses':loss,'pad_groups':padgroups,'every_SBC_load_pad_source_joined_host':len(padgroups)==1,'all_discrete_owned_removed_contact_obligations_require_external_ledger':True,'candidate_plane_sha256':row['sha256'],'native_refill_DRC_full_IR_return_gate_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'SBC-contact-partitions-r3.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('retained_original_contact_partition_losses','pad_groups')}));print('SBC_PAD_GROUPS',[(r['group'],[(t['ref'],t['pad']) for t in r['pads']]) for r in padgroups])
if __name__=='__main__':main()
