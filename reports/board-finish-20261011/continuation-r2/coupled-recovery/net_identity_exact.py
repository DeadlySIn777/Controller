"""Raw native net identity guard/serializer. Normalization never grants authority.

Every new serialized track uses the unique exact token from the frozen source.
A board containing two raw tokens with one normalized key is rejected before
any typed geometry/graph builder is called. No source/helper mutation.
"""
import collections,re
import coupled_screen as P
NET_TOKEN=re.compile(rb'\(net(?:[ \t]+[0-9]+)?[ \t]+"((?:\\.|[^"\\])*)"\)')
class SourceNets:
    def __init__(self,raw):
        self.raw_tokens={t.decode('utf-8') for t in NET_TOKEN.findall(raw) if t}
        self.by_normalized=collections.defaultdict(set)
        for token in self.raw_tokens:self.by_normalized[P.S.norm(token)].add(token)
        self.assert_no_collisions(raw)
    def assert_no_collisions(self,raw):
        grouped=collections.defaultdict(set)
        for token in NET_TOKEN.findall(raw):
            if token:grouped[P.S.norm(token.decode('utf-8'))].add(token.decode('utf-8'))
        collisions={k:sorted(v) for k,v in grouped.items() if len(v)>1}
        if collisions:raise ValueError('Distinct native net tokens normalize to one key: '+repr(collisions))
        return {'raw_net_count':sum(len(v) for v in grouped.values()),'normalization_collisions':0}
    def raw(self,logical):
        names=self.by_normalized[P.S.norm(logical)]
        if len(names)!=1:raise ValueError('Missing/ambiguous source native net token '+repr(logical))
        return next(iter(names))
    def assert_chunks(self,chunks):
        tokens=[P.S.overlay_tool.netname(ch) for ch in chunks.values()]
        for raw in tokens:
            if raw and raw!=self.raw(raw):raise ValueError('Copper uses non-source native net token '+repr(raw))
        return self.assert_no_collisions(b''.join(chunks.values()))
    def geometry(self,chunks,template):
        self.assert_chunks(chunks)
        return P.geometry(chunks,template)
    def serial_segment(self,net,layer,a,b,width=.2):
        return P.serial_segment(self.raw(net),layer,a,b,width)
