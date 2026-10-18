"""Use alternate controlled head; requalify original prospective de03 site."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-de03-small-prospective-move-r445.py').read_text(encoding='utf-8')
s=s.replace('CM73-only-prospective-de03-80um-shift-two-owned-F-source-tracks-r445','CM73-original-prospective-de03-site-alternate-CDONE-LG16-r450')
a=s.index("mp=Path(selected['R435_minimal_patch_dependency']);");b=s.index("uid='de03bc75",a)
replace="""alternate=P/'CM79-alternate-CDONE-LG16-ONLY_NEW-CM85-leg-controlled-r448';assert sha(alternate/'receipt.json')=='e53622a3d6bcca7a2ad5818758e2464db63cbcff69cb70b8264ba26394fd5b05';mp=alternate/'only-qualified-minimal-pose-and-new-tracks.pkl';alt=pickle.loads(mp.read_bytes());minimal={'moved_original_via':alt['moved_original_barrel'],'only_new_vias':[],'only_new_tracks':alt['only_new_tracks']};r443=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443';assert sha(r443/'receipt.json')=='486886b6fe8000cf1b64a4e0e54a6bddea15411f2c3bb0c59daaf96c6b51f351';p443=r443/'only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl';extra=pickle.loads(p443.read_bytes());c['vias']=[minimal['moved_original_via']if v['uuid']==minimal['moved_original_via']['uuid']else v for v in c['vias']]+selected['vias'];c['tracks']+=minimal['only_new_tracks']+selected['tracks']+[t for t in extra['new_tracks']if t['uuid']!='65f3a90e-a953-5caa-8493-4623cfc05f2f'];"""
s=s[:a]+replace+s[b:]
s=s.replace("'x':118.437505","'x':118.357505").replace("'delta_from_saved_prospective_mm':[.08,0]","'delta_from_saved_prospective_mm':[0,0]")
s=s.replace("'CM73-R445-","'CM73-R450-").replace("print('R445_COMPLETE'","print('R450_COMPLETE'")
s=s.replace("QUALIFIED_PROSPECTIVE_DE03_80UM_SHIFT_CM73_FINITE_SOURCE_BEFORE_HANDOFF","QUALIFIED_ORIGINAL_PROSPECTIVE_DE03_CM73_ON_ALTERNATE_CDONE_LG16")
s=s.replace("'only_prospective_saved_de03_move':True","'only_prospective_saved_de03_move':False,'original_de03_saved_site_requalified_no_active_native_via_move':True")
E=P/'exact-expanded-original-prospective-de03-alternate-head-r450.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
