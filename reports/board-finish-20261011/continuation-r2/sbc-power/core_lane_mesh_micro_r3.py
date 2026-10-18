"""Read-only, single-thread sheet+barrel IR preflight for the frozen CORE lane.

Missing F-side pad/control geometry is explicitly excluded: this is a lower-bound
subnetwork solve and does not establish source, return or full board qualification.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
import json,hashlib,math,sys,time
from pathlib import Path
import numpy as np
import shapely
from shapely import from_wkb
from scipy import sparse
from scipy.sparse.linalg import cg,LinearOperator
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
def main():
    receipt=HERE/'CORE-banks-micro-preserved-r3.json';d=json.loads(receipt.read_text());geom=Path(d['candidate_CORE_plane_file']);assert hashlib.sha256(geom.read_bytes()).hexdigest()==d['candidate_plane_sha256']
    plane=from_wkb(geom.read_bytes());step=float(sys.argv[1]) if len(sys.argv)>1 else .2
    x0,y0,x1,y1=plane.bounds;x=np.arange(math.floor(x0/step)*step,x1+step/2,step);y=np.arange(math.floor(y0/step)*step,y1+step/2,step)
    xx,yy=np.meshgrid(x,y);mask=shapely.contains_xy(plane,xx,yy);idx=np.full(mask.shape,-1,np.int64);idx[mask]=np.arange(mask.sum());n=int(mask.sum());terminal=n
    horizontal=mask[:,1:]&mask[:,:-1];vertical=mask[1:,:]&mask[:-1,:]
    a=np.concatenate([idx[:,1:][horizontal],idx[1:,:][vertical]]);b=np.concatenate([idx[:,:-1][horizontal],idx[:-1,:][vertical]])
    cc=sparse.coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(n,n)).tocsr();_,labels=connected_components(cc)
    # Branches across square mesh cells have one square of sheet resistance.
    conduct=1/(.57003672e-3);row=list(np.r_[a,b,a,b]);col=list(np.r_[a,b,b,a]);values=list(np.r_[np.full(2*len(a),conduct),np.full(2*len(a),-conduct)])
    banks=[];vias=[];barrel_R=.0022
    for bank in d['ordinary_via_banks']:
        one=[]
        for via in bank['sites']:
            px,py=via['at'];disc=(xx-px)**2+(yy-py)**2<=.29**2;nodes=idx[mask&disc]
            assert len(nodes)>0
            # Parallel contacts sum to exactly one conservative full-barrel R.
            gv=1/(barrel_R*len(nodes));r={'name':bank['name'],'at':[px,py],'nodes':nodes,'g':gv};vias.append(r);one.append(r)
            for node in nodes:
                row.append(int(node));col.append(int(node));values.append(gv)
                if bank['name']=='load':
                    row.extend([terminal,terminal,int(node)]);col.extend([terminal,int(node),terminal]);values.extend([gv,-gv,-gv])
        banks.append(one)
    source_labels=set(int(labels[node]) for via in banks[0] for node in via['nodes']);load_labels=set(int(labels[node]) for via in banks[1] for node in via['nodes'])
    if not load_labels.issubset(source_labels):raise ValueError('Rasterized load portions not source-connected '+str((source_labels,load_labels)))
    # Remove raster debris that contains neither source nor load terminals.
    allowed=np.r_[np.isin(labels,list(source_labels|load_labels)),True];keep=np.nonzero(allowed)[0]
    A=sparse.coo_matrix((values,(row,col)),shape=(n+1,n+1)).tocsr()[keep][:,keep];rhs=np.zeros(n+1);rhs[terminal]=-d['planning_current_A'];rhs=rhs[keep]
    diag=A.diagonal();assert np.all(diag>0);pre=LinearOperator(A.shape,lambda v:v/diag)
    started=time.time();solution,info=cg(A,rhs,M=pre,rtol=1e-9,atol=1e-12,maxiter=15000);assert info==0,info
    voltage=np.full(n+1,np.nan);voltage[keep]=solution;loadvoltage=float(voltage[terminal]);actual=[]
    for via in vias:
        other=0. if via['name']=='source' else loadvoltage
        amps=float(np.sum((other-voltage[via['nodes']])*via['g']));actual.append({'bank':via['name'],'at':via['at'],'current_A':amps,'maximum_planning_A':.5,'planning_limit_pass':abs(amps)<=.5+1e-7})
    sums={name:sum(v['current_A'] for v in actual if v['bank']==name) for name in ('source','load')}
    result={'verdict':'HOST_SUBNETWORK_IR_SOLVE_ONLY','frozen_plane_sha256':d['candidate_plane_sha256'],'frozen_geometry_receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'step_mm':step,'Cu_nodes':n,'matrix_nodes':len(keep),'runtime_seconds':time.time()-started,'current_A':d['planning_current_A'],'sheet_mOhm_60C':.57003672,'each_barrel_R_mOhm':2.2,'source_to_load_subnetwork_drop_mV':-loadvoltage*1000,'subnetwork_resistance_mOhm':-loadvoltage*1000/d['planning_current_A'],'via_currents':actual,'bank_sums':sums,'max_via_current_A':max(abs(r['current_A']) for r in actual),'via_count_alone_not_used_for_sharing':True,'excluded_required_geometry':['source_R11022/shunt/core-bulk common bus','F-bank-to-C11088/source-pad and F-bank-to-U11012-VIN fanout','full current return, connector/module contacts and SBC output power','IO_3V3 restoration after carve','new-via native refill/antipad/current extraction'], 'native_jobs':0,'board_written':False,'threads':1,'physical_power_qualified':False}
    dest=HERE/('CORE-In2-mesh-micro-preserved-r3-'+str(step).replace('.','p')+'.json');dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('via_currents','excluded_required_geometry')}))
if __name__=='__main__':main()
