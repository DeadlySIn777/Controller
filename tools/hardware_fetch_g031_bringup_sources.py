"""Fetch unmodified official register headers; preserve third-party licenses."""
from pathlib import Path
import concurrent.futures,hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'firmware/motherboard_iol1_readonly/vendor';REPORT=ROOT/'reports/motherboard-iol1-firmware-20260930'
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Controller-source-audit'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.read()
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(exist_ok=True)
 commit=json.loads(get('https://api.github.com/repos/STMicroelectronics/cmsis-device-g0/commits/master'))['sha']
 jobs={}
 for file in ['stm32g031xx.h','system_stm32g0xx.h']:jobs['ST/'+file]=f'https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-g0/{commit}/Include/{file}'
 jobs['ST/LICENSE.md']=f'https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-g0/{commit}/LICENSE.md'
 for file in ['core_cm0plus.h','cmsis_version.h','cmsis_compiler.h','cmsis_gcc.h','mpu_armv7.h']:jobs['ARM/'+file]=f'https://raw.githubusercontent.com/ARM-software/CMSIS_5/5.9.0/CMSIS/Core/Include/{file}'
 jobs['ARM/LICENSE.txt']='https://raw.githubusercontent.com/ARM-software/CMSIS_5/5.9.0/LICENSE.txt'
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for name,url,raw in [(name,url,future.result()) for name,url,future in [(n,u,pool.submit(get,u)) for n,u in jobs.items()]]:
   p=OUT/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw);rows.append({'path':p.relative_to(ROOT).as_posix(),'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'unmodified_primary_vendor_code':True})
 (REPORT/'vendor-source-receipt.json').write_text(json.dumps({'ST_commit':commit,'ARM_CMSIS_tag':'5.9.0','original_controller_code_not_open_source_promised':True,'vendor_licenses_retained':True,'sources':rows},indent=2)+'\n')
 print(json.dumps({'sources':len(rows),'ST_commit':commit}))
if __name__=='__main__':main()
