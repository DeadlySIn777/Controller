from pathlib import Path
import shutil, json, hashlib
P=Path(__file__).resolve().parent
S=P/'record-config-replay-candidate-r02'
O=P/'stage-r03'
shutil.copytree(S,O,ignore=shutil.ignore_patterns('bundle-manifest.json','__pycache__'))

def replace(file,old,new):
 p=O/file;s=p.read_text();assert s.count(old)==1,(file,s.count(old));p.write_text(s.replace(old,new),newline='\n')

replace('iol1.h','uint32_t iol1_crc32c(const uint8_t *p,size_t n);',
'''uint32_t iol1_crc32c(const uint8_t *p,size_t n);
/* FFFF means unavailable. Caller latches invalid until an actual new sample,
 * so a full32-bit timer wrap cannot revive an already stale observation. */
uint16_t iol1_sample_age_us(uint32_t now_us,uint32_t sampled_us,uint8_t valid);''')
replace('iol1.c','void iol1_init(iol1_node *n,uint8_t c,uint8_t s){',
'''uint16_t iol1_sample_age_us(uint32_t now,uint32_t sampled,uint8_t valid){
    uint32_t elapsed=now-sampled;
    return !valid||elapsed>=65535u?0xffffu:(uint16_t)elapsed;
}
void iol1_init(iol1_node *n,uint8_t c,uint8_t s){''')
replace('target.c','static volatile uint32_t raw_di,filtered_di,last_di_us;',
'''static volatile uint32_t raw_di,filtered_di,last_di_us;
static volatile uint8_t di_valid;''')
replace('target.c','{raw_di=next_raw;filtered_di=next_filtered;last_di_us=t;}',
'''{raw_di=next_raw;filtered_di=next_filtered;last_di_us=t;di_valid=1;}''')
replace('target.c','uint16_t age=(uint16_t)(t-last_di_us);p[6]=(uint8_t)(age>>8);p[7]=(uint8_t)age;',
'''uint16_t age=iol1_sample_age_us(t,last_di_us,di_valid);
    if(age==0xffffu)di_valid=0; /* cannot wrap back to young without a sample */
    p[6]=(uint8_t)(age>>8);p[7]=(uint8_t)age;''')
replace('target.c','uint32_t elapsed=t-do_sample_us;uint16_t age=!do_valid||elapsed>65534u?0xffffu:(uint16_t)elapsed;',
'''uint16_t age=iol1_sample_age_us(t,do_sample_us,do_valid);
    if(age==0xffffu)do_valid=0;''')
replace('test_record_config.c',' iol1_node n;iol1_init(&n,IOL1_DIC,0);uint8_t f[40],reply[40];',
''' // Execute the same age helper linked into all four real targets.
 CK(iol1_sample_age_us(0,0,0)==65535,"cold DIC sample unavailable");
 CK(iol1_sample_age_us(100,100,1)==0,"actual current sample age0");
 CK(iol1_sample_age_us(65534,0,1)==65534,"DIC age65534");
 CK(iol1_sample_age_us(65535,0,1)==65535,"DIC age65535 unavailable");
 CK(iol1_sample_age_us(65536,0,1)==65535,"DIC age65536 must not wrap young");
 CK(iol1_sample_age_us(0xffffffffu,0,1)==65535,"very old sample saturated");
 CK(iol1_sample_age_us(0,0xffffffffu,1)==1,"timer rollover1us");
 CK(iol1_sample_age_us(0x0000ffeeu,0xfffffff0u,1)==65534,"rollover65534");
 CK(iol1_sample_age_us(0x0000ffefu,0xfffffff0u,1)==65535,"rollover65535");
 CK(iol1_sample_age_us(0x0000fff0u,0xfffffff0u,1)==65535,"rollover65536");
 uint8_t sample_valid=1;
 if(iol1_sample_age_us(65536,0,sample_valid)==65535)sample_valid=0;
 CK(iol1_sample_age_us(1,0,sample_valid)==65535,"latched stale cannot revive after full timerwrap");
 sample_valid=1;CK(iol1_sample_age_us(11,10,sample_valid)==1,"only actual resample restores young age");
 iol1_node n;iol1_init(&n,IOL1_DIC,0);uint8_t f[40],reply[40];''')
replace('run_record_config.py',"'factory_pages_reserved':'LENGTH = 60K' in linker",
"'DIC_and_DO_age_use_same_saturating_C':target.count('iol1_sample_age_us(')==2 and 'if(age==0xffffu)di_valid=0;' in target and 'if(age==0xffffu)do_valid=0;' in target,\n  'factory_pages_reserved':'LENGTH = 60K' in linker")
replace('run_mutations.py',"mutations=[",'''mutations=[
 ('sample_age_wraps_young','iol1.c','return !valid||elapsed>=65535u?0xffffu:(uint16_t)elapsed;','return !valid?0xffffu:(uint16_t)elapsed;','DIC age65536 must not wrap young'),''')
replace('run_mutations.py',"'actual_compiled_C_mutants':7", "'actual_compiled_C_mutants':8")
replace('replay_record_config.py','seven compiled C runtime-rejected mutations','eight compiled C runtime-rejected mutations')
(O/'stage-r03-delta.json').write_text(json.dumps({
 'prior_bundle_sha256':hashlib.sha256((S/'bundle-manifest.json').read_bytes()).hexdigest(),
 'finding':'retained target DIC uint16 age could wrap after65,535us while accepted IRQ frames refreshed IWDG',
 'changes':['one real shared C saturating sample-age function','DIC first-sample-valid/default-unavailable state','DIC and DO latch stale until actual fresh sample, preventing laterfulltimerwrap revival','same-C65534/65535/65536 and modulo timerrollover controls','compiled truncation mutation'],
 'actual_DMA_GPIO_IRQ_or_flash_execution':False,'outputs_ACTIVE_ARM':False
},indent=2)+'\n')
print(O)
