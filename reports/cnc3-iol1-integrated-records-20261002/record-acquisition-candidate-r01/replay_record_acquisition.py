from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {p.relative_to(H).as_posix():sha(p) for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')}
def main(out,distro,inventory):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True);before=snapshot();manifest=json.loads((H/'bundle-manifest.json').read_text());integrity=before==manifest['files'];start=time.time();rows=[];env=os.environ.copy();env['CNC3_WSL_DISTRO']=distro
 stages=[('actual_four_lane_record_config_SPI','run_record_acquisition.py','actual simulated SPI into exact r03 target C; all2048 bytes and applied DIC configuration echo; no target MMIO'),('shared_record_integrity_controls','run_stream_controls.py','actual compiled bit-serial CRC/shape/queue; independent20-case host vectors plus six compiled mutations'),('actual_previous_command_tuple_controls','run_wire_tuple_controls.py','actual wire frames into exact C; two compiled current-vs-cached response metadata mutations'),('composed_family_mapping','run_record_family.py','family mapping of actual twelve-axis motion/session plus acquisition; separate failed T20 cell screen, no vendor fit')]
 for name,runner,evidence in stages:
  row={'name':name,'runner':runner,'evidence_type':evidence,'status':'NOT_RUN'}
  if not integrity:row.update(status='FAIL',reason='frozen input hashes differ')
  elif inventory:row['reason']='inventory only'
  else:
   print('RUN '+name,flush=True)
   try:
    p=subprocess.run([sys.executable,'-X','utf8',str(H/runner),'--out',str(out/name)],env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=1500)
    (out/(name+'-command.log')).write_text(p.stdout+p.stderr,newline='\n');receipt=out/name/'receipt.json';r=json.loads(receipt.read_text()) if receipt.exists() else {};good=p.returncode==0 and r.get('status')=='PASS' and r.get('inputs_unchanged') is True
    row.update(status='PASS' if good else 'FAIL',exit_code=p.returncode,receipt=str(receipt),receipt_sha256=sha(receipt) if receipt.exists() else None)
    if name=='composed_family_mapping':row['coarse_T20_capacity_screen']=r.get('coarse_T20_capacity_screen',{'status':'NOT_RUN'})
   except Exception as e:row.update(status='FAIL',reason=repr(e))
   print(row['status']+' '+name,flush=True)
  rows.append(row);(out/'checkpoint.json').write_text(json.dumps({'stages':rows,'bundle_integrity':integrity},indent=2)+'\n')
 unchanged=before==snapshot();counts={s:sum(r['status']==s for r in rows) for s in ('PASS','FAIL','BLOCKED','NOT_RUN')};passed=integrity and unchanged and counts['PASS']==4
 capacity=next((r.get('coarse_T20_capacity_screen') for r in rows if r['name']=='composed_family_mapping'),None)
 report={'status':'PASS' if passed else 'NOT_RUN' if inventory and integrity and unchanged else 'FAIL','counts':counts,'stages':rows,'exact_inputs':before,'bundle_integrity':integrity,'inputs_unchanged':unchanged,'bundle_manifest_sha256':sha(H/'bundle-manifest.json'),'duration_seconds':round(time.time()-start,3),'coarse_T20_capacity_screen':capacity,'scope_flags':{'actual_simulated_IDENT_CONFIG_SPI':any(r['name']=='actual_four_lane_record_config_SPI' and r['status']=='PASS' for r in rows),'proposed_record_supplement_and_major1_profile_not_adopted':True,'actual_twelve_axis_motion_session_acquisition_composed_for_mapping':any(r['name']=='composed_family_mapping' and r['status']=='PASS' for r in rows),'factory_signature_UID_authentication_ACTIVE_output_ARM':False,'actual_flash_GPIO_MMIO_DMA_ISR_execution':False,'complete_HAL_machine_endpoint_or_physical_qualification':False,'vendor_T20_fit_timing_bitstream':False,'product_ratings_changed':False},'open_dependencies':['coarse T20 LUT4+ADD capacity failure requires arithmetic sharing/vendor resynthesis before fit','production trust registry and actual calibrated/factory records remain absent','read-only cached record integrity cannot grant ACTIVE or motion qualification','complete producer health/identity policy, actual target MMIO/flash/interrupt timing and full output permission remain separate','dormant IS2 CAP3 page mux not included in these composed resource tops']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'counts':counts,'capacity':capacity,'report':str(out/'report.json')}),flush=True);return 0 if report['status'] in ('PASS','NOT_RUN') else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--wsl-distro',default='GarciaMechBuilder');p.add_argument('--inventory',action='store_true');a=p.parse_args();raise SystemExit(main(a.out.resolve(),a.wsl_distro,a.inventory))
