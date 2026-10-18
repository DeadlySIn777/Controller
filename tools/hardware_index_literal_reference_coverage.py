"""Exact local native-fill prefilter; final full guard remains authoritative.

Create a new instance after every refill. The tile cache copies literal native
filled polygons and clips them with integer geometry; no hole or clearance is
approximated. A local pass is only routing-search evidence. Final acceptance
also requires the frozen full-union coverage and actual native Source contact.
"""
from __future__ import annotations
import math
import pcbnew
from hardware_route_local_signals import GeometryIndex
from hardware_zone_motherboard_returns import split_polygons
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact


class LiteralReferenceCoverage:
    def __init__(self,board,nets,layers,tile_mm=5):
        if tile_mm<=0:raise ValueError('Positive search tile required')
        self.board=board;self.nets=set(nets);self.layers=list(layers)
        self.tile=pcbnew.FromMM(tile_mm);self.indices={};self.cache={};self.full=None
        for z in board.Zones():
            if z.GetIsRuleArea()or z.GetNetname()not in self.nets:continue
            for layer in self.layers:
                if not z.IsOnLayer(layer):continue
                index=self.indices.setdefault((z.GetNetname(),layer),GeometryIndex())
                for shape in split_polygons(z.GetFilledPolysList(layer)):
                    if shape.Area()<=0:continue
                    b=shape.BBox();bounds=[pcbnew.ToMM(v)for v in[b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()]]
                    index.add(shape,bounds)

    def local_fill(self,subject,net,layer):
        box=subject.BBox();t=self.tile
        # The one-nanometre integer extension preserves exact boundary metal;
        # it is not a permitted gap/area tolerance in the coverage predicate.
        limits=(math.floor(box.GetX()/t)*t-1,math.floor(box.GetY()/t)*t-1,
                math.ceil(box.GetRight()/t)*t+1,math.ceil(box.GetBottom()/t)*t+1)
        key=(net,layer,*limits)
        if key in self.cache:return self.cache[key]
        clip=pcbnew.SHAPE_POLY_SET();clip.NewOutline()
        a,b,c,d=limits
        for x,y in[(a,b),(c,b),(c,d),(a,d)]:clip.Append(x,y)
        union=pcbnew.SHAPE_POLY_SET();index=self.indices.get((net,layer))
        if index:
            start=(pcbnew.ToMM(a),pcbnew.ToMM(b));end=(pcbnew.ToMM(c),pcbnew.ToMM(d))
            for original in index.candidates(start,end,0):
                part=pcbnew.SHAPE_POLY_SET();part.Append(original);part.BooleanIntersection(clip)
                if part.Area()>0:union.BooleanAdd(part)
        self.cache[key]=union
        return union

    def candidate_covered(self,subject,net,layer):
        """Search prefilter only; callers must not use it as acceptance."""
        return covered(subject,self.local_fill(subject,net,layer))

    def final_full_covered(self,subject,net,layer):
        """Retain frozen full-union coverage after a fast candidate passes."""
        if not self.candidate_covered(subject,net,layer):return False
        if self.full is None:self.full=collect_native_reference_fills(self.board,self.nets,self.layers)
        actual=self.full.get((net,layer))
        return bool(actual is not None and covered(subject,actual))

    def final_ground_stitch(self,via,layers,source_by_uuid,ring_mm=.24):
        """Actual same-net Source witness, annuli and both full guards."""
        self.board.BuildConnectivity();conn=self.board.GetConnectivity();net=via.GetNetname()
        peers=list(conn.GetConnectedItems(via));witness=None
        for item in peers:
            if not isinstance(item,pcbnew.PAD)or not item.GetNumber()or item.GetNetname()!=net:continue
            row=source_by_uuid.get(item.m_Uuid.AsString())
            if row and row['net']==net and not row.get('native_nc',False):witness=(item.GetParentFootprint().GetReference(),item.GetNumber());break
        if witness is None:return False
        shape=circle(tuple(via.GetPosition()),pcbnew.FromMM(ring_mm))
        return all(physical_reference_contact(via,l,conn)and self.final_full_covered(shape,net,l)for l in layers)
