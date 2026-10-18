"""Static exact-raw project membership audit; no native effective-class claim."""
import collections, fnmatch, hashlib, json, sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'field-power'))
import inventory as I
OUT=H/'static-raw-domain-contract-r2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
    project=H/'field-power-native-trial-r1/measure/copy/board.kicad_pro'
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),source,project,Path(I.__file__))}
    assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
    I.NET=source
    parts,nodes,nets=I.load()
    settings=json.loads(project.read_bytes())['net_settings']
    assignments=settings['netclass_assignments']; patterns=settings['netclass_patterns']
    domains={r['name'] for r in settings['classes'] if r['name'].startswith('DOM_')}
    rows=[]; errors=[]
    for raw in sorted(nets):
        exact=assignments.get(raw,[])
        if isinstance(exact,str): exact=[exact]
        hit=[r for r in patterns if raw==r['pattern'] or fnmatch.fnmatchcase(raw,r['pattern'])]
        classes=set(exact)|{r['netclass'] for r in hit}
        ds=sorted(classes&domains)
        row={'raw_net':raw,'explicit_assignments':exact,'matching_patterns':hit,'static_classes':sorted(classes),'domains':ds}
        rows.append(row)
        if len(ds)!=1: errors.append({'raw_net':raw,'domains':ds})
    assert len(nets)==2388 and len(parts)==2723
    assert all(sha(p)==v for p,v in pins.items())
    OUT.mkdir()
    record={'verdict':'PASS_STATIC_EXACT_RAW_DOMAIN_MEMBERSHIP' if not errors else 'FAIL_STATIC_EXACT_RAW_DOMAIN_MEMBERSHIP','source_parts':len(parts),'raw_net_count':len(nets),'domain_counts':dict(collections.Counter(r['domains'][0] for r in rows if len(r['domains'])==1)),'errors':errors,'rows':rows,'input_sha256':pins,'matching':'Exact raw assignment and literal pattern first, plus case-sensitive glob diagnostic; no slash/token normalization or raw-net merging','scope':'STATIC project/source inspection only; native KiCad effective class, clearance execution and filled copper require separate native gates','native_jobs':0,'source_project_or_board_changed':False}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('verdict','raw_net_count','domain_counts','errors')}))
if __name__=='__main__':main()
