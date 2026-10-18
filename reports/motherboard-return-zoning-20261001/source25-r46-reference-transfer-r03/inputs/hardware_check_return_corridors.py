"""Check real adjacent return copper while allowing bounded signal-via antipads.

This module does not alter a board, add stitches or relax routing selection.
Use after native refill/DRC and complete source/pad validation. A signal via
may mask only its own bounded antipad at exact segment endpoints; the outer
return annulus and actual connected own-domain stitching must still exist.
"""
from __future__ import annotations
import math
import pcbnew
from hardware_route_selected_additive import corridor_polygon


def uid(item):return item.m_Uuid.AsString()


def circle(point,radius,segments=96):
    p=pcbnew.SHAPE_POLY_SET();p.NewOutline()
    for i in range(segments):
        a=2*math.pi*i/segments
        p.Append(round(point[0]+radius*math.cos(a)),round(point[1]+radius*math.sin(a)))
    return p


def copy_poly(poly):
    p=pcbnew.SHAPE_POLY_SET();p.Append(poly);return p


def covered(poly,fill):
    missing=copy_poly(poly);missing.BooleanSubtract(fill)
    return missing.OutlineCount()==0 and missing.Area()==0


class ReturnCheck:
    def __init__(self,board,rows):
        self.board,self.rows=board,rows
        board.BuildConnectivity()
        self.tracks=list(board.GetTracks())
        self.vias=[v for v in self.tracks if isinstance(v,pcbnew.PCB_VIA)]
        self.fills={};self.zone_clearance={};self.audits={}

    def reference(self,net,layer):
        key=net,layer
        if key not in self.fills:
            union=pcbnew.SHAPE_POLY_SET();clearances=[]
            for z in self.board.Zones():
                if not z.GetIsRuleArea() and z.GetNetname()==net and z.HasFilledPolysForLayer(layer):
                    union.BooleanAdd(z.GetFilledPolysList(layer));clearances.append(z.GetLocalClearance())
            union.Simplify();self.fills[key]=union
            self.zone_clearance[key]=max(clearances,default=0)
        if not self.fills[key].OutlineCount():
            raise ValueError('Actual filled own-reference plane is absent: '+net+' '+self.board.GetLayerName(layer))
        return self.fills[key]

    def layers_at(self,via,row):
        p=tuple(via.GetPosition());layers=set()
        for t in self.tracks:
            if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!=via.GetNetname():continue
            if p in [tuple(t.GetStart()),tuple(t.GetEnd())]:
                name=self.board.GetLayerName(t.GetLayer())
                if name not in row['reference_layers']:
                    raise ValueError('Signal-via leg uses an undeclared reference layer')
                layers.add(self.board.GetLayerID(row['reference_layers'][name]))
        if not layers:raise ValueError('Signal-via endpoint has no actual declared signal legs')
        return layers

    def source_anchors(self,stitch,return_net):
        # A net-name match alone cannot make a via a return path. Native physical
        # connectivity must reach numbered copper source pads; the caller has
        # already independently reconciled those exact pads against the source.
        peers=list(self.board.GetConnectivity().GetConnectedItems(stitch))
        anchors=[]
        for p in peers:
            if isinstance(p,pcbnew.PAD) and p.GetNumber() and p.IsOnCopperLayer() and p.GetNetname()==return_net:
                fp=p.GetParentFootprint()
                anchors.append(dict(reference=fp.GetReference(),pin=p.GetNumber(),pad_uuid=uid(p)))
        return sorted(anchors,key=lambda p:(p['reference'],p['pin'],p['pad_uuid']))

    def same_filled_piece(self,fill,annulus,stitch):
        # Boolean union preserves disconnected outlines. It is not enough that
        # the annulus and stitch happen to be in different same-named islands.
        point=stitch.GetPosition()
        for index in range(fill.OutlineCount()):
            piece=pcbnew.SHAPE_POLY_SET();piece.AddPolygon(fill.CPolygon(index))
            if piece.Contains(point) and covered(annulus,piece):return True
        return False

    def via(self,signal,row):
        key=uid(signal)
        if key in self.audits:return self.audits[key]
        if signal.GetViaType()!=pcbnew.VIATYPE_THROUGH or not row.get('allow_vias'):
            raise ValueError('Only declared actual signal through-vias are eligible')
        if signal.GetNetname() not in self.rows or row['return_net']==signal.GetNetname():
            raise ValueError('Signal and own return identities are invalid')
        if abs(pcbnew.ToMM(signal.GetWidth(pcbnew.F_Cu))-row['via_diameter_mm'])>1e-6 or abs(pcbnew.ToMM(signal.GetDrillValue())-row['via_drill_mm'])>1e-6:
            raise ValueError('Signal-via geometry differs from exact reviewed manifest')
        bound=row['return_stitch_distance_mm']
        if not 0<bound<=1:raise ValueError('Return-stitch bound must be explicit and at most1mm')
        layers=self.layers_at(signal,row);point=tuple(signal.GetPosition())
        candidates=[v for v in self.vias if uid(v)!=key and v.GetViaType()==pcbnew.VIATYPE_THROUGH
            and v.GetNetname()==row['return_net'] and math.dist(tuple(v.GetPosition()),point)<=pcbnew.FromMM(bound)]
        accepted=[];radii={}
        for layer in layers:
            fill=self.reference(row['return_net'],layer)
            # The20um allowance bounds polygon discretization, not an arbitrary
            # plane-hole exception. A larger void fails the outer annulus.
            radius=signal.GetWidth(pcbnew.F_Cu)/2+self.zone_clearance[row['return_net'],layer]+pcbnew.FromMM(.02)
            annulus=circle(point,radius+pcbnew.FromMM(.20));annulus.BooleanSubtract(circle(point,radius))
            if not covered(annulus,fill):
                raise ValueError('Signal-via antipad lacks a continuous own-return annulus')
            radii[layer]=radius
        for stitch in candidates:
            anchors=self.source_anchors(stitch,row['return_net'])
            if not anchors:continue
            valid=True
            for layer in layers:
                fill=self.reference(row['return_net'],layer);radius=radii[layer]
                annulus=circle(point,radius+pcbnew.FromMM(.20));annulus.BooleanSubtract(circle(point,radius))
                # The ground stitch must actually join the same filled connected
                # polygon on every intended side, rather than sit near its edge.
                if (not covered(circle(tuple(stitch.GetPosition()),stitch.GetWidth(pcbnew.F_Cu)/2-pcbnew.FromMM(.01)),fill)
                    or not self.same_filled_piece(fill,annulus,stitch)):
                    valid=False;break
            if valid:accepted.append(dict(uuid=uid(stitch),distance_mm=math.dist(tuple(stitch.GetPosition()),point)/1e6,source_pad_anchors=anchors))
        if not accepted:
            raise ValueError('Signal through-via lacks physically connected same-domain return stitch within1mm')
        audit=dict(signal_via_uuid=key,return_net=row['return_net'],return_stitches=accepted,
            intended_reference_layers=[self.board.GetLayerName(l)for l in sorted(layers)],
            bounded_antipad_radius_mm={self.board.GetLayerName(l):r/1e6 for l,r in radii.items()},
            continuous_reference_annulus_width_mm=.20,polygon_discretization_allowance_mm=.02)
        self.audits[key]=audit;return audit

    def segment(self,track,row):
        if not isinstance(track,pcbnew.PCB_TRACK) or isinstance(track,pcbnew.PCB_ARC):
            raise ValueError('Only actual reviewed straight signal segments are supported')
        layer_name=self.board.GetLayerName(track.GetLayer())
        if layer_name not in row['reference_layers']:raise ValueError('Segment reference layer is undeclared')
        layer=self.board.GetLayerID(row['reference_layers'][layer_name])
        fill=self.reference(row['return_net'],layer)
        corridor=corridor_polygon(tuple(track.GetStart()),tuple(track.GetEnd()),
            track.GetWidth()/2+pcbnew.FromMM(row['reference_corridor_margin_mm']))
        exceptions=[]
        for endpoint in [tuple(track.GetStart()),tuple(track.GetEnd())]:
            matching=[v for v in self.vias if v.GetNetname()==track.GetNetname() and tuple(v.GetPosition())==endpoint]
            for via in matching:
                audit=self.via(via,row)
                radius=pcbnew.FromMM(audit['bounded_antipad_radius_mm'][self.board.GetLayerName(layer)])
                # Subtract only actual missing reference copper within the
                # physically reviewed endpoint's bounded antipad circle.
                allowed=circle(endpoint,radius);allowed.BooleanSubtract(fill)
                corridor.BooleanSubtract(allowed);exceptions.append(uid(via))
        if not covered(corridor,fill):
            raise ValueError('New route crosses an unqualified reference boundary, slot or hole: '+track.GetNetname())
        return dict(uuid=uid(track),reference_net=row['return_net'],reference_layer=self.board.GetLayerName(layer),
            full_geometric_projected_corridor_covered=True,explicit_endpoint_antipad_vias=exceptions)


def return_corridor_check(board,added,rows):
    checker=ReturnCheck(board,rows);items=[]
    exact={uid(t):t for t in board.GetTracks()}
    if not set(added)<=set(exact):raise ValueError('Declared added copper UUID is absent')
    for ident in sorted(added):
        t=exact[ident]
        if t.GetNetname() not in rows:raise ValueError('Added signal copper lacks exact manifest net')
        row=rows[t.GetNetname()]
        items.append(checker.via(t,row)if isinstance(t,pcbnew.PCB_VIA)else checker.segment(t,row))
    return dict(passed=True,new_copper_items_checked=len(items),items=items,
        endpoint_exception_scope='exact reviewed same-net signal through-vias only',
        real_source_pad_and_same_connected_reference_piece_required=True,
        measured_return_impedance=False,physical_signal_integrity_qualified=False,
        no_source_or_pcb_mutation=True)
