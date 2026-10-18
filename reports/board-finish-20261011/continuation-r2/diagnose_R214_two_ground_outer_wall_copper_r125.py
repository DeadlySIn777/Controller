"""Exact local existing outer wall attribution for two literal ground pins."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
OUT=H/'R214-two-field-ground-exact-outer-wall-copper-r125'
NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());records,trees=F.build(full,layers={'F.Cu','B.Cu'});oldids={q['uuid'] for k in ('tracks','vias','pads') for q in g[k]};diag=json.loads((H/'R214-field-ground-direct-outer-source-escape-diagnosis-r120/receipt.json').read_bytes());rows=[]
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch
    for d in diag['rows']:
        ref,pin,layer=d['ref'],d['pin'],d['layer'];pad=next(p for p in h['pads'] if (p['ref'],p['num'])==(ref,pin));pt=Point(pad['x'],pad['y']);goal=Point(d['closest_pair_mm'][1]);axis=LineString([pt,goal]);body=axis.buffer(.1,quad_segs=256);win=box(pt.x-5,pt.y-5,pt.x+7,pt.y+5);walls=[];locals=[]
        for i in trees[layer].query(win,predicate='intersects'):
            q=records[layer][int(i)];locals.append(q)
            if C.norm(q['net'])==NET:continue
            required=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET] else .6)+.025
            if body.distance(q['shape'])<required:
                walls.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'ref':q.get('ref'),'pin':q.get('pin'),'old_discrete_UUID':q['uuid'] in oldids,'actual_required_gap_mm':required,'actual_Cu_gap_to_direct_new_.20mm_chord_mm':body.distance(q['shape']),'obstacle_bounds_mm':q['shape'].bounds,'old_source_row':q.get('source')})
        rows.append({'ref':ref,'pin':pin,'layer':layer,'pad_mm':[pt.x,pt.y],'direct_source_goal_mm':[goal.x,goal.y],'walls':walls})
        fig,ax=plt.subplots(figsize=(11,7));ax.set_aspect('equal');ax.set_xlim(win.bounds[0],win.bounds[2]);ax.set_ylim(win.bounds[3],win.bounds[1]);ax.set_title(ref+'.'+pin+' '+layer+' actual R214 copper; proposed direct ground chord is diagnostic')
        for q in locals:
            s=q['shape'].intersection(win);parts=[s] if s.geom_type=='Polygon' else list(getattr(s,'geoms',[]));col='#1565c0' if C.norm(q['net'])==NET else '#aa7777';alpha=.30 if q['kind']=='fill' else .75
            for part in parts:
                if part.geom_type=='Polygon':ax.add_patch(Patch(list(part.exterior.coords),facecolor=col,edgecolor=col,alpha=alpha))
            if any(q['uuid']==w['UUID'] for w in walls) and q['kind']!='fill':
                pos=s.representative_point();ax.annotate(q['uuid'][:8]+' '+q['net'].split('/')[-1],(pos.x,pos.y),fontsize=7,rotation=10)
        ax.plot([pt.x,goal.x],[pt.y,goal.y],color='#00a000',linewidth=2,linestyle='--');ax.scatter([pt.x],[pt.y],s=80,color='#ffff00',edgecolors='black');ax.grid(alpha=.2);ax.set_xlabel('mm');ax.set_ylabel('mm');fig.tight_layout();fig.savefig(OUT/(ref+'-exact-local-copper.png'),dpi=160);plt.close(fig)
    record={'verdict':'EXACT_OUTER_GROUND_ESCAPE_WALL_ATTRIBUTION_NO_CU_EDITS','parent_model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
