from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_C19506_SOURCE_ground_In4_Cu_r680.generated.py';s=p.read_text();rows=[]
for rev,ly in((700,'B.Cu'),(702,'F.Cu')):
 text=s
 for a,b in [('AO1-COM-C19506-1-real-SOURCE-In4.Cu-ground-current-peers-r680',f'AO1-COM-C19506-1-real-SOURCE-{ly}-ground-current-peers-r{rev}'),("LY='In4.Cu'",f"LY='{ly}'"),('R680_COMPLETE',f'R{rev}_COMPLETE'),('[[354.15168,177],[352.448318,169.4]]','[[358.028603,180.368079],[351.354231,168.757319]]')]:
  assert a in text,a;text=text.replace(a,b)
 out=H/f'construct_AO1_C19506_SOURCE_ground_{ly.replace(".","_")}_r{rev}.generated.py';assert not out.exists();out.write_text(text);rows.append({'file':str(out.resolve()),'SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'layer':ly,'revision':rev})
(H/'derive-AO1-C19506-surface-ground-r700.json').write_text(json.dumps({'parent_file':str(p.resolve()),'parent_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':rows,'scope':'specific remaining AO1 COM coupling-cap island; surface Cu only; actual old SOURCE finite contact; every foreign plane/Cu/hole/barrier held'},indent=1)+'\n')
