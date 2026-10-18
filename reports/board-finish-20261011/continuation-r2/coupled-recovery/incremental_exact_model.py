"""Fast isolated append to an exact frozen source model for path construction.

Unchanged native geometry/records are shared without rounding or alteration.
Only exact serialized new copper is appended, with conservative all6 via disks
and holes. This is a constructor optimization; every positive complete board
must still be rebuilt independently from its complete serialized inventory.
"""
import collections,copy,math
import coupled_screen as P
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
G,S=P.G,P.S

def append(model,chunks,identities):
    identities.assert_chunks(chunks)
    known={r['uuid'] for layer in model.records.values() for r in layer if r['kind'] in ('pad','track','via')}
    if known&set(chunks):raise ValueError('Append contains an existing source entity')
    result=copy.copy(model)
    result.g=dict(model.g);result.g['tracks']=list(model.g['tracks']);result.g['vias']=list(model.g['vias'])
    result.records={layer:list(records) for layer,records in model.records.items()}
    result.own=collections.defaultdict(list,{net:list(records) for net,records in model.own.items()})
    appended_vias=[]
    for uid,ch in chunks.items():
        r=G.parse(uid,ch,{});net=r['net'];domain=model.domains.get(net)
        if domain is None:raise ValueError('Appended exact native net has no existing domain')
        if r['kind']=='segment':
            track={'uuid':uid,'net':net,'a':r['a'],'b':r['b'],'w':r['w'],'layer':r['layer']}
            result.g['tracks'].append(track);line=LineString([r['a'],r['b']]);sites=[tuple(r['a']),tuple(r['b'])]
            sites += [tuple(line.interpolate(i/max(1,math.ceil(line.length)),normalized=True).coords[0]) for i in range(1,max(1,math.ceil(line.length)))]
            rec={'shape':S.overlay_tool.base.body(track),'net':net,'domain':domain,'kind':'track','uuid':uid,'key':('t',uid),'layer':r['layer'],'sites':sites}
            result.records[r['layer']].append(rec);result.own[net].append(rec)
        elif r['kind']=='via':
            via={'uuid':uid,'net':net,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'span':['F.Cu','B.Cu'],'flashed':list(model.g['copper_layers'])}
            result.g['vias'].append(via);appended_vias.append(uid);p=Point(r['at'])
            for layer in model.g['copper_layers']:
                rec={'shape':p.buffer(r['d']/2),'net':net,'domain':domain,'kind':'via','uuid':uid,'key':('v',uid),'layer':layer,'sites':[tuple(r['at'])]}
                result.records[layer].append(rec);result.own[net].append(rec)
                result.records[layer].append({'shape':p.buffer(r['drill']/2),'net':net,'kind':'hole','uuid':uid})
        else:raise ValueError('Only exact serialized straight tracks and ordinary vias supported')
    result.trees={layer:STRtree([r['shape'] for r in records]) for layer,records in result.records.items()}
    result.source_annulus_proof=copy.deepcopy(model.source_annulus_proof)
    result.source_annulus_proof['unattested_new_or_restored_six_layer_clearance_vias']+=appended_vias
    result.source_annulus_proof['constructor_incremental_append']={'uuids':sorted(chunks),'exact_serialized_coordinates':True,'unchanged_source_native_geometry_and_masks_preserved':True,'all_new_via_copper_holes_on_six_layers':True,'complete_positive_board_independent_rebuild_required':True}
    return result
