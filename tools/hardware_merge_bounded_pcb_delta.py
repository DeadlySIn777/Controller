"""Merge an exact reviewed native PCB transaction into a newer board copy.

Only explicitly listed footprint poses/layers and the donor's literal copper
delta may change. The electrical source, footprint lands, pin nets, unrelated
copper must remain unchanged. An existing-zone outline correction requires
its own exact reviewed before/after hashes; its net, layers and pour rules
cannot change. Concurrent edits are rejected rather than overwritten.
"""
import argparse,collections,copy,json,re,shutil,subprocess
from pathlib import Path
from hardware_build_assembly import parse,dump,children,child,value
from hardware_populate_motherboard_pcb import sha,write,pad_template,footprint_name
from hardware_route_logic_return import identity,mm
import pcbnew
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def objects(tree,kind):return {value(child(v,'uuid')[1]):v for v in children(tree,kind)}
def dump_board(tree):
    # Large reference pours can exceed KiCad's per-line parser buffer when a
    # generic sexpr dump puts the entire board on one line. Preserve every
    # parsed native object while separating only top-level records.
    return '('+tree[0]+'\n'+'\n'.join(dump(v) if isinstance(v,list) else v for v in tree[1:])+')\n'
def without_generated_fills(text):
    """Drop only derived filled_polygon objects before native zone refill.

    Quoted text is lexical, including parentheses. All source objects and zone
    outlines/rules remain byte-for-byte intact; the native CLI regenerates the
    derived polygons before any geometry or physical connectivity is accepted.
    """
    markers=re.compile(r'"(?:\\.|[^"\\])*"|\(filled_polygon(?=\s|\(|\))')
    brackets=re.compile(r'"(?:\\.|[^"\\])*"|\(|\)')
    cursor=0;pieces=[]
    for match in markers.finditer(text):
        if match.start()<cursor or match.group(0).startswith('"'):continue
        depth=1;end=None
        for token in brackets.finditer(text,match.end()):
            if token.group(0)=='(':depth+=1
            elif token.group(0)==')':
                depth-=1
                if not depth:end=token.end();break
        if end is None:raise ValueError('Unbalanced derived native filled_polygon')
        pieces.append(text[cursor:match.start()]);cursor=end
    pieces.append(text[cursor:]);return ''.join(pieces)
def reference(fp):return value(next(p[2]for p in children(fp,'property')if value(p[1])=='Reference'))
def zone_definition(z):
    t=copy.deepcopy(z)
    for v in list(children(t,'filled_polygon')):t.remove(v)
    return dump(t)
def pad_nets(fp):return collections.Counter((p.GetNumber(),p.m_Uuid.AsString(),str(p.GetNetname()))for p in fp.Pads())
def unchanged_properties(fp):return {value(p[1]):value(p[2])for p in children(fp,'property')}

def merge_reviewed_existing_zone_outlines(before,donor,target,reviews):
    """Apply reviewed outline corrections without changing electrical pour rules."""
    old=objects(before,'zone');new=objects(donor,'zone');current=objects(target,'zone')
    reviewed={r['uuid']:r for r in reviews}
    if len(reviewed)!=len(reviews):raise ValueError('Duplicate existing-zone review UUID')
    def non_outline_zone(z):
        item=copy.deepcopy(z)
        for part in list(children(item,'polygon'))+list(children(item,'filled_polygon')):item.remove(part)
        return dump(item)
    changes=[]
    for uid,z in old.items():
        if uid not in new:raise ValueError('Donor deletes existing plane '+uid)
        if zone_definition(new[uid])==zone_definition(z):continue
        review=reviewed.get(uid)
        if not review or not review.get('electrical_outline_correction_reason'):raise ValueError('Unreviewed existing-plane outline change '+uid)
        first,last=zone_definition(z),zone_definition(new[uid])
        if sha_text(first)!=review['before_definition_sha256']or sha_text(last)!=review['after_definition_sha256']:raise ValueError('Exact reviewed plane definition differs '+uid)
        if non_outline_zone(z)!=non_outline_zone(new[uid]):raise ValueError('Existing plane net/layers/clearance/pour rules changed '+uid)
        if uid not in current or zone_definition(current[uid])!=first:raise ValueError('Concurrent existing plane outline conflict '+uid)
        target[target.index(current[uid])]=copy.deepcopy(new[uid])
        changes.append(dict(uuid=uid,before_definition_sha256=review['before_definition_sha256'],after_definition_sha256=review['after_definition_sha256'],reason=review['electrical_outline_correction_reason']))
    if {r['uuid']for r in changes}!=set(reviewed):raise ValueError('Reviewed plane outline scope is not the actual delta')
    return changes

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('before','donor','target','scope','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    frozen={str(v.resolve()):sha(v)for v in (a.before,a.donor,a.target,a.scope)}
    scope=json.loads(a.scope.read_text());allowed=set(scope['reviewed_footprint_references'])
    if not scope['electrical_source_unchanged']or not scope.get('reviewed_scope_reason'):raise ValueError('Bounded electrical-source-preserving transaction required')
    boards={k:pcbnew.LoadBoard(str(v.resolve()))for k,v in (('before',a.before),('donor',a.donor),('target',a.target))}
    fps={k:{f.GetReference():f for f in b.GetFootprints()}for k,b in boards.items()}
    if not(set(fps['before'])==set(fps['donor'])==set(fps['target'])):raise ValueError('Full source population differs')
    trees={k:parse(without_generated_fills(v.read_text()))for k,v in (('before',a.before),('donor',a.donor),('target',a.target))}
    rawfps={k:{reference(f):f for f in children(t,'footprint')}for k,t in trees.items()}
    changed=[]
    for ref,old in rawfps['before'].items():
        new=rawfps['donor'][ref]
        if dump(old)==dump(new):continue
        if ref not in allowed:raise ValueError('Unreviewed footprint changed '+ref)
        if dump(rawfps['target'][ref])!=dump(old):raise ValueError('Concurrent footprint transaction conflict '+ref)
        if unchanged_properties(old)!=unchanged_properties(new):raise ValueError('Component identity/source properties changed '+ref)
        bf,df=fps['before'][ref],fps['donor'][ref]
        if pad_nets(bf)!=pad_nets(df)or footprint_name(bf)!=footprint_name(df):raise ValueError('Exact source lands/MPN pin nets changed '+ref)
        if bf.GetLayer()!=df.GetLayer():bf.Flip(bf.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        bf.SetPosition(df.GetPosition());bf.SetOrientationDegrees(df.GetOrientationDegrees())
        if collections.Counter(pad_template(q)for q in bf.Pads())!=collections.Counter(pad_template(q)for q in df.Pads()):raise ValueError('Physical mirrored manufacturer lands changed '+ref)
        changed.append(dict(ref=ref,before_sha256=sha_text(dump(old)),after_sha256=sha_text(dump(new)),new_pose=[*mm(df.GetPosition()),df.GetOrientationDegrees(),boards['donor'].GetLayerName(df.GetLayer())]))
        idx=trees['target'].index(rawfps['target'][ref]);trees['target'][idx]=copy.deepcopy(new)
    delta=[]
    for kind in ('segment','via','arc'):
        old=objects(trees['before'],kind);new=objects(trees['donor'],kind);target=objects(trees['target'],kind)
        for uid in sorted(set(old)|set(new)):
            first,last=old.get(uid),new.get(uid)
            if first is not None and last is not None and dump(first)==dump(last):continue
            if first is not None:
                if uid not in target or dump(target[uid])!=dump(first):raise ValueError('Concurrent old copper transaction conflict '+uid)
                trees['target'].remove(target[uid])
            elif uid in target:raise ValueError('New copper UUID already exists '+uid)
            if last is not None:trees['target'].append(copy.deepcopy(last))
            delta.append(dict(kind=kind,uuid=uid,before=dump(first)if first is not None else None,after=dump(last)if last is not None else None))
    added_zones=[]
    old=objects(trees['before'],'zone');new=objects(trees['donor'],'zone');target=objects(trees['target'],'zone')
    changed_zones=merge_reviewed_existing_zone_outlines(trees['before'],trees['donor'],trees['target'],scope.get('reviewed_existing_zone_outline_deltas',[]))
    for uid,z in new.items():
        if uid in old:continue
        if uid in target:raise ValueError('New reference-plane UUID conflicts')
        trees['target'].append(copy.deepcopy(z));added_zones.append(uid)
    if {r['uuid']for r in delta}!=set(scope['reviewed_copper_delta_UUIDs']):raise ValueError('Exact reviewed copper UUID scope differs')
    if set(added_zones)!=set(scope['reviewed_added_zone_UUIDs']):raise ValueError('Exact reviewed reference-plane UUID scope differs')
    # Edge cuts, schematic ancestry and project rules are owned by the target.
    a.out.mkdir(parents=True);dest=a.out/'motherboard-bounded-merged-candidate.kicad_pcb'
    for r in a.target.parent.iterdir():
        if r.is_dir()and(r.suffix=='.pretty'or r.name=='3dmodels'):shutil.copytree(r,a.out/r.name)
        elif r.name=='fp-lib-table':shutil.copyfile(r,a.out/r.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.target.with_suffix(suffix),dest.with_suffix(suffix))
    # Exact local graphics-only library changes must travel with their native
    # instances. A donor cannot replace a whole library or silently overwrite
    # a concurrently edited target resource.
    library_changes=[]
    for entry in scope.get('reviewed_library_file_deltas',[]):
        rel=Path(entry['relative_path'])
        if rel.is_absolute() or '..' in rel.parts or rel.suffix!='.kicad_mod' or not entry.get('graphics_only_no_manufacturer_land_change'):
            raise ValueError('Bounded footprint graphics resource required')
        first=a.before.parent/rel;last=a.donor.parent/rel;target=a.target.parent/rel
        if sha(first)!=entry['before_sha256'] or sha(last)!=entry['after_sha256'] or sha(target)!=entry['before_sha256']:
            raise ValueError('Concurrent or unreviewed footprint library resource '+str(rel))
        first_footprint=pcbnew.FootprintLoad(str(first.parent),first.stem)
        last_footprint=pcbnew.FootprintLoad(str(last.parent),last.stem)
        if first_footprint is None or last_footprint is None or collections.Counter(pad_template(v)for v in first_footprint.Pads())!=collections.Counter(pad_template(v)for v in last_footprint.Pads()):
            raise ValueError('Manufacturer library lands changed '+str(rel))
        shutil.copyfile(last,a.out/rel);library_changes.append(entry)
    dest.write_text(dump_board(trees['target']))
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True)
    (a.out/'drc.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native DRC did not execute successfully')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();current={f.GetReference():f for f in fresh.GetFootprints()}
    for ref,f in fps['target'].items():
        wanted=fps['donor'][ref]if ref in {r['ref']for r in changed}else f
        if pad_nets(current[ref])!=pad_nets(wanted):raise ValueError('Final exact pin/net/UUID mismatch '+ref)
        if (tuple(current[ref].GetPosition()),current[ref].GetOrientationDegrees(),current[ref].GetLayer())!=(tuple(wanted.GetPosition()),wanted.GetOrientationDegrees(),wanted.GetLayer()):raise ValueError('Final exact pose mismatch '+ref)
    target_copper={t.m_Uuid.AsString():identity(t)for t in boards['target'].GetTracks()};actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    changed_ids={r['uuid']for r in delta}
    if any(actual.get(uid)!=v for uid,v in target_copper.items()if uid not in changed_ids):raise ValueError('Unrelated target copper changed')
    wanted_copper={t.m_Uuid.AsString():identity(t)for t in boards['donor'].GetTracks()}
    if any(actual.get(r['uuid'])!=wanted_copper.get(r['uuid'])for r in delta):raise ValueError('Final literal copper delta/net differs')
    drc=json.loads((a.out/'drc.json').read_text())
    if drc.get('ignored_checks'):raise ValueError('Unexpected ignored native check')
    if any(sha(Path(path))!=digest for path,digest in frozen.items()):raise ValueError('Input changed during bounded merge')
    result=dict(input_sha256=frozen,scope=scope,exact_changed_footprints=changed,exact_copper_delta=delta,new_reference_zones=added_zones,reviewed_existing_zone_outline_deltas=changed_zones,reviewed_library_file_deltas=library_changes,board_sha256=sha(dest),source_population=len(current),track_via_count=len(actual),native_DRC_regular=len(drc['violations']),native_DRC_types=dict(collections.Counter(v['type']for v in drc['violations'])),ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),all_unrelated_native_copper_pin_nets_and_poses_preserved=True,manufacturing_ready=False)
    write(a.out/'receipt.json',result);print({k:result[k]for k in ('source_population','track_via_count','native_DRC_regular','native_DRC_types','uncapped_missing_joins','board_sha256')})

def sha_text(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()
if __name__=='__main__':main()
