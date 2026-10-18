from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_COM_U14624_complete_domain_F_ground_r670.generated.py';s=p.read_text();rows=[]
for rev,ly in((680,'In4.Cu'),(682,'In1.Cu')):
 text=s
 changes=[('AO1-COM-U14624-3-complete-domain-F-ground-current-R20-R656-r670',f'AO1-COM-C19506-1-real-SOURCE-{ly}-ground-current-peers-r{rev}'),("LY='F.Cu'",f"LY='{ly}'"),("islands['islands'][1]","islands['islands'][3]"),("p['ref']=='U14624'and p['pin']=='3'","p['ref']=='C19506'and p['pin']=='1'"),('19434a4b-d4ed-4193-90b1-b90a71062411','41004407-03be-4571-be77-ee721df93cd9'),('win=box(332,102,390,172)','win=box(334,154,374,186)'),('[[355.898,143.9],[356.898,143.85]]','[[354.15168,177],[352.448318,169.4]]'),('U14624_3', 'C19506_1'),('R670_COMPLETE',f'R{rev}_COMPLETE')]
 for a,b in changes:
  assert a in text,a;text=text.replace(a,b)
 out=H/f'construct_AO1_C19506_SOURCE_ground_{ly.replace(".","_")}_r{rev}.generated.py';assert not out.exists();out.write_text(text);rows.append({'file':str(out.resolve()),'SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'layer':ly,'revision':rev})
(H/'derive-AO1-C19506-ground-r678.json').write_text(json.dumps({'parent_file':str(p.resolve()),'parent_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':rows,'scope':'nominate DC SOURCE connection into genuine AO1_COM side of retained 4.7nF X1/Y2 HF coupling cap; other domain/PE material held'},indent=1)+'\n')
