"""Exact zone-only S-expression profile and native integer contour checks."""
from fractions import Fraction
import re


def tree(chunk):
    tokens=re.findall(rb'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',chunk)
    i=0
    def read():
        nonlocal i
        t=tokens[i];i+=1
        if t!=b'(':return t
        row=[]
        while tokens[i]!=b')':row.append(read())
        i+=1
        return row
    result=read()
    assert i==len(tokens) and result[0]==b'zone'
    return result


def normalized(value):
    if isinstance(value,list):return tuple(map(normalized,value))
    if value.startswith(b'"'):return value
    try:return Fraction(value.decode('ascii'))
    except (ValueError,ZeroDivisionError):return value


def profile(chunk,ignore_name=False):
    result=[]
    for row in tree(chunk)[1:]:
        assert isinstance(row,list)
        if row[0] in (b'polygon',b'filled_polygon',b'uuid'):continue
        if ignore_name and row[0]==b'name':continue
        if row[0]==b'fill':row=[x for x in row if x!=b'yes']
        result.append(normalized(row))
    return tuple(sorted(result,key=repr))


def contours(chunk):
    rings=[]
    for row in tree(chunk)[1:]:
        if row[0]!=b'polygon':continue
        assert len(row)==2 and row[1][0]==b'pts'
        ring=[]
        for xy in row[1][1:]:
            assert xy[0]==b'xy' and len(xy)==3
            point=[]
            for token in xy[1:]:
                n=Fraction(token.decode('ascii'))*1000000
                assert n.denominator==1,'Non-native coordinate in polygon'
                point.append(int(n))
            ring.append(point)
        assert len(ring)>=3
        rings.append(ring)
    assert rings
    # Native format assigns every ring after the first to a hole. Native API
    # save/reload must separately prove that these are the intended hole roles.
    return rings


def filled_count(chunk):
    return sum(x[0]==b'filled_polygon' for x in tree(chunk)[1:])
