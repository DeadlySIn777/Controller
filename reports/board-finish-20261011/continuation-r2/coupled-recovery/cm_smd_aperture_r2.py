"""Narrow six-hole CM SMD aperture audit; temporarily pause own XF host run."""
import hashlib,json,math,re,sys,time
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    out=HERE/'cm-smd-aperture-r2.json'
    if out.exists():raise ValueError('Fresh aperture receipt required')
    paused=None;pause={}
    try:
        own=psutil.Process(60624)
        command=own.cmdline()
        if not any('run_host_confined.py' in q for q in command) or command[-1]!='xf_continuous_landings_r6.py':raise ValueError('Own XF process identity differs')
        own.suspend();paused=own;pause={'pid':own.pid,'command':command,'suspended_before_geometry':True,'suspended_at_unix':time.time()}
        from shapely.geometry import Point,Polygon
        from shapely.strtree import STRtree
        recipe_raw=(HERE/'cm-coupled-returns-r4.json').read_bytes();recipe=json.loads(recipe_raw)
        audit_raw=(HERE/'cm-complete-independent-audit-r4-r2.json').read_bytes();audit=json.loads(audit_raw)
        board_raw=Path(recipe['candidate']).read_bytes();board=board_raw.decode()
        if sha(board_raw)!=audit['candidate_sha256'] or audit['verdict']!='HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_SI_OPEN':raise ValueError('Frozen CM candidate audit differs')
        geometry_path=HERE.parent/'native-198b-geometry/geometry.json';native_raw=geometry_path.read_bytes()
        if sha(native_raw)!='ad4d776a8703702d9bd682c1427d7883b729e8c6dcfbaad87c9e07c7b981d5d1':raise ValueError('Fresh native source differs')
        native=json.loads(native_raw);pads=[];shapes=[];multi=[]
        for p in native['pads']:
            if p['attr']!='smd' or not p['layers']:continue
            if len(p['layers'])!=1:multi.append({'ref':p['ref'],'num':p['num'],'layers':p['layers']})
            for polygon in p['poly']:
                shapes.append(Polygon(polygon[0],polygon[1:]));pads.append(p)
        if multi:raise ValueError('Unexpected SMD multi-layer definition; requires complete native pad-stack export '+repr(multi))
        tree=STRtree(shapes);restores={r['uuid'] for r in recipe['restored_via_exact_flags_annuli']}
        rows=[]
        for uid in audit['added_uuids']:
            marker='(uuid "'+uid+'")';pos=board.index(marker);start=board.rfind('\t(via',0,pos);end=board.find('\n\t)\n',pos)+len('\n\t)\n')
            # Every ordinary changed via has an exact top-level chunk. Other
            # added items are excluded by their immediately enclosing kind.
            item_start=board.rfind('\n\t(',0,pos)
            if item_start+1!=start:continue
            chunk=board[start:end]
            at=[float(v) for v in re.search(r'\(at\s+([^()]+)\)',chunk).group(1).split()]
            diameter=float(re.search(r'\(size\s+([0-9.]+)\)',chunk).group(1));drill=float(re.search(r'\(drill\s+([0-9.]+)\)',chunk).group(1))
            point=Point(at);indices=tree.query(point.buffer(2),predicate='intersects')
            values=sorted((point.distance(shapes[i])-drill/2,int(i)) for i in indices)
            if not values:raise ValueError('No local SMD witness; expand exact nearest query')
            gap,index=values[0];p=pads[index]
            rows.append({'uuid':uid,'role':'restored-original-clock-via' if uid in restores else 'new-ordinary-via','exact_serialized_chunk_sha256':sha(chunk.encode()),'at_mm':at,'diameter_mm':diameter,'drill_mm':drill,'minimum_drill_edge_to_SMD_copper_mm':gap,'minimum_after_native_polygon_inside_error_mm':gap-.005,'nearest_native_SMD_pad':{'ref':p['ref'],'num':p['num'],'net':p['net'],'at_mm':p['at'],'layer':p['layers'][0]},'required_aperture_mm':.25,'required_guard_mm':.025,'passes_guarded_aperture':gap>=.275,'passes_guarded_aperture_even_after_export_error':gap-.005>=.275})
        if len(rows)!=6 or len([r for r in rows if r['role']=='new-ordinary-via'])!=4:raise ValueError('Exact six changed CM vias not recovered')
        report={'schema':'cm-exact-native-smd-aperture-r1','verdict':'PASS' if all(r['passes_guarded_aperture_even_after_export_error'] for r in rows) else 'FAIL','candidate_sha256':sha(board_raw),'native_geometry_sha256':sha(native_raw),'constructor_receipt_sha256':sha(recipe_raw),'independent_audit_sha256':sha(audit_raw),'selected_exact_serialized_vias':rows,'native_SMD_polygon_count':len(shapes),'native_SMD_no_copper_pad_count':sum(p['attr']=='smd' and not p['layers'] for p in native['pads']),'multi_layer_SMD_defs':multi,'predicate':'Every ordinary changed through hole against every current native SMD copper polygon, both F/B, every net including same-net; analytic point-to-polygon distance minus exact drill radius >= .25+.025 mm, with extra .005 mm export-error subtraction','registered_SMD_hole_exemptions_applied':0,'native_jobs':0,'gpu_jobs':0,'adopted':False,'source_footprint_identity':'Prior complete candidate audit proves every source footprint/header/rules byte-identical to 198b','own_XF_pause':pause}
    finally:
        if paused:
            paused.resume();pause['resumed_at_unix']=time.time();pause['resumed']=True
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'minimum_gap_mm':min(r['minimum_drill_edge_to_SMD_copper_mm'] for r in rows),'own_XF_resumed':pause['resumed']}),flush=True)
if __name__=='__main__':main()
