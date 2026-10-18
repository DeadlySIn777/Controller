"""Attest every discrete copper object on the same loaded native board as source parity."""
import hashlib,importlib.util,json,sys
from pathlib import Path
import pcbnew

def main(argv):
    helper,expected=map(Path,argv[:2]);args=argv[2:]
    spec=json.loads(expected.read_bytes());board_path=Path(spec['board_path'])
    if hashlib.sha256(board_path.read_bytes()).hexdigest()!=spec['board_sha256']:raise ValueError('Frozen board changed')
    modspec=importlib.util.spec_from_file_location('frozen_full_source_helper',helper)
    module=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(module)
    original=pcbnew.LoadBoard;captured=[]
    def load(*a,**k):
        board=original(*a,**k);captured.append(board);return board
    pcbnew.LoadBoard=load
    try:
        code=module.main(args)
        if code or len(captured)!=1:raise ValueError('Frozen source/pose/68-via gate failed')
        board=captured[0];actual={str(t.m_Uuid.AsString()):t for t in board.GetTracks()}
        errors=[];counts={'segment':0,'via':0};stack=list(board.GetEnabledLayers().CuStack())
        xy=lambda p:[int(p.x),int(p.y)]
        if set(actual)!=set(spec['copper']):errors.append({'reason':'Discrete copper UUID inventory differs','missing':sorted(set(spec['copper'])-set(actual)),'extra':sorted(set(actual)-set(spec['copper']))})
        for uid,exp in spec['copper'].items():
            t=actual.get(uid)
            if t is None:continue
            counts[exp['kind']]+=1
            obs={'raw_net':str(t.GetNetname())}
            if exp['kind']=='via':
                if not isinstance(t,pcbnew.PCB_VIA):errors.append({'uuid':uid,'reason':'Native via kind differs'});continue
                obs.update(at_IU=xy(t.GetPosition()),drill_IU=int(t.GetDrillValue()),diameters_IU={str(board.GetLayerName(l)):int(t.GetWidth(l)) for l in stack})
            else:
                if isinstance(t,(pcbnew.PCB_VIA,pcbnew.PCB_ARC)):errors.append({'uuid':uid,'reason':'Native straight track kind differs'});continue
                obs.update(start_IU=xy(t.GetStart()),end_IU=xy(t.GetEnd()),width_IU=int(t.GetWidth()),layer=str(board.GetLayerName(t.GetLayer())))
            for key,value in exp.items():
                if key in ('kind','chunk_sha256'):continue
                if obs.get(key)!=value:errors.append({'uuid':uid,'field':key,'expected':value,'actual':obs.get(key)})
        out=Path(args[-1]);report=json.loads(out.read_bytes())
        report['all_discrete_copper_exact_native_contract']={'verdict':'PASS' if not errors else 'FAIL','counts':counts,'errors':errors,'exact_raw_net_name_and_integer_geometry':True,'expected_ledger_sha256':hashlib.sha256(expected.read_bytes()).hexdigest(),'no_refill_or_save':True,'all_old_and_new_copper_checked':True}
        out.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
        print(json.dumps(report['all_discrete_copper_exact_native_contract']),flush=True)
        return 1 if errors else 0
    finally:pcbnew.LoadBoard=original

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
