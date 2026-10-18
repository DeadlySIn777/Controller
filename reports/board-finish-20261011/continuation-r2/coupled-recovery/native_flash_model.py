"""Current-native source via annulus adapter; no nominal connectivity credit.

Prune only unchanged exact known198b via disks from unflashed layers. Drill
obstacles remain on all layers. Unattested new/restored vias remain six-layer
conservative clearance obstacles until a fresh candidate native export exists.
Callers must guard raw serialized net identity before typed geometry creation.
"""
import collections,math
import coupled_screen as P
from shapely.strtree import STRtree
S=P.S
class Model(S.Model):
    def __init__(self,g,reservations,exemptions,native_vias,actual_masks):
        super().__init__(g,reservations,exemptions)
        source={v['uuid']:v for v in native_vias}
        known={};conservative=[]
        for v in self.g['vias']:
            if v['uuid'] not in source:
                conservative.append(v['uuid']);continue
            s=source[v['uuid']]
            if (v['x'],v['y'],v['d'],v['drill'],S.norm(v['net']))!=(s['at'][0],s['at'][1],s['w'],s['drill'],S.norm(s['net'])):raise ValueError('Current native via geometry/role changed '+v['uuid'])
            if v['uuid'] not in actual_masks:raise ValueError('Known source via lacks actual native mask '+v['uuid'])
            known[v['uuid']]=set(actual_masks[v['uuid']]);v['flashed']=sorted(known[v['uuid']])
        removed=collections.Counter()
        for layer,records in list(self.records.items()):
            keep=[]
            for row in records:
                if row['kind']=='via' and row['uuid'] in known and layer not in known[row['uuid']]:removed[layer]+=1
                else:keep.append(row)
            self.records[layer]=keep
        for net,records in list(self.own.items()):
            self.own[net]=[r for r in records if r['kind']!='via' or r['uuid'] not in known or r['layer'] in known[r['uuid']]]
        self.trees={layer:STRtree([r['shape'] for r in records]) for layer,records in self.records.items()}
        self.source_annulus_proof={'exact_current_source_vias_checked':len(known),'suppressed_copper_disks_by_layer':dict(removed),'all_drill_obstacles_preserved':True,'unattested_new_or_restored_six_layer_clearance_vias':conservative,'native_candidate_actual_annuli':'MANDATORY'}
