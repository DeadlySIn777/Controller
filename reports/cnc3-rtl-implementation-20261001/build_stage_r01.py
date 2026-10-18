"""Report-local, exact frozen CNC3 structural rule generator; no external writes."""
from pathlib import Path
import hashlib, importlib.util, json, shutil

HERE = Path(__file__).resolve().parent
OUT = HERE / 'stage-r01'
EXTERNAL = Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec')
ERRORS = ['valid', 'UNKNOWN_CS', 'LENGTH', 'CRC', 'MAGIC', 'ABI', 'UNKNOWN_OPCODE', 'WRONG_CS', 'MASK_WIDTH', 'SEQUENCE_RULE', 'SESSION_RULE', 'MASK_RULE', 'RATE_ON_NON_UPDATE', 'FIELD_NOT_ALLOWED', 'PAYLOAD_NONZERO', 'FIELD_RANGE', 'EMBEDDED_FRAME', 'RESERVED_NONZERO', 'FIELD_BITS', 'FIELD_RELATION', 'UNMASKED_RATE']
HEADERS = {'magic','abi','opcode','channel_mask','crc16','crc32c','sof','version','expected_slot','epoch','control'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    frozen = OUT/'frozen'
    files = {'spec/protocol.json': EXTERNAL/'spec/protocol.json', 'protocol_v3.py':EXTERNAL/'gateware/v3/tools/protocol_v3.py', 'vectors.json':EXTERNAL/'gateware/v3/vectors/protocol_v3_vectors.json'}
    for rel, src in files.items():
        dest=frozen/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
    m=importlib.util.spec_from_file_location('cnc3_frozen',frozen/'protocol_v3.py'); p=importlib.util.module_from_spec(m);m.loader.exec_module(p)
    p._SPEC=p.Spec(str(frozen/'spec/protocol.json')); s=p.spec()
    lines=['`timescale 1ns/1ps','// SPDX-License-Identifier: LicenseRef-Proprietary', '// GENERATED: exact frozen IS-1 static acceptance only; never grants ARM or output authority.',
           '// Byte zero is frame[1407:1400]; CMD occupies high 768 bits, low 640 bits are padding.',
           'module cnc3_command_validate(input wire [1407:0] frame, input wire cs_fb,',
           ' input wire [8:0] frame_bytes, input wire crc_good, input wire embedded_crc_good, output reg [7:0] result);',
           'wire [7:0] opcode=frame[1367:1360];', 'wire [15:0] mask=frame[1359:1344];',
           'wire [31:0] session=frame[1343:1312], sequence_value=frame[1311:1280];', 'always @* begin', 'result=0;']
    def val(off,size=1): return f"frame[{1407-8*off} -: {size*8}]"
    def check(cond,error,indent=''):
        lines.append(f'{indent}if (result==0 && ({cond})) result=8\'d{ERRORS.index(error)};')
    def nz(lo,hi): return '|'+val(lo,hi-lo+1)
    def allowed(v,ranges,width=8):
        terms=[]
        for lo,hi in ranges:
            parts=[]
            if lo:parts.append(f'{v} >= {width}\'d{lo}')
            if hi<(1<<width)-1:parts.append(f'{v} <= {width}\'d{hi}')
            terms.append('('+' && '.join(parts)+')' if parts else "1'b1")
        return ' || '.join(terms)
    def layout(name,base,owned):
        lay=s.layout(name)
        for f in lay.fields:
            if f.name in HEADERS or not f.rules or any(i in owned for i in range(base+f.offset,base+f.offset+f.size)): continue
            r=f.rules; off=base+f.offset
            if f.count is not None: es=p._SCALAR[f.elem][0]; count=f.count
            elif f.type in p._SCALAR: es=f.size;count=1
            else: es=0;count=1
            if not es:
                if r.get('zero'):check(nz(off,off+f.size-1),'RESERVED_NONZERO')
                continue
            for e in range(count):
                v=val(off+e*es,es)
                if r.get('zero'):check(v+' != 0','RESERVED_NONZERO')
                if r.get('allowed') and r['allowed']!=[(0,(1<<(es*8))-1)]:check('!('+allowed(v,r['allowed'],es*8)+')','FIELD_RANGE')
                if r.get('nonzero'):check(v+' == 0','FIELD_RANGE')
                if r.get('zero_bits'):check(f"({v} & {es*8}'h{r['zero_bits']:x}) != 0",'FIELD_BITS')
        for f in lay.fields:
            r=f.rules;v=val(base+f.offset,f.size)
            if 'disjoint_with' in r:
                other=lay.field(r['disjoint_with']);check(f'({v} & {val(base+other.offset,other.size)}) != 0','FIELD_RELATION')
            if 'subset_of' in r:
                other=lay.field(r['subset_of']);check(f'({v} & ~{val(base+other.offset,other.size)}) != 0','FIELD_RELATION')
            if 'bits_require' in r:
                bits,other_name,need=r['bits_require'];other=lay.field(other_name)
                missing=f"{val(base+other.offset,other.size)} {'==' if need=='nonzero' else '!='} {0 if need=='nonzero' else need}"
                check(f"({v} & {f.size*8}'h{bits:x}) != 0 && ({missing})",'FIELD_RELATION')
    check('frame_bytes != (cs_fb ? 176 : 96)','LENGTH')
    check('!crc_good','CRC');check(val(0,4)+" != 32'h434e4333",'MAGIC');check(val(4)+" != 8'd3",'ABI')
    check('!('+' || '.join(f"opcode==8'h{x:02x}" for x in s.opcodes)+')','UNKNOWN_OPCODE')
    check('(cs_fb && !('+' || '.join(f"opcode==8'h{x:02x}" for x in s.cs_opcodes['CS_FB'])+')) || (!cs_fb && !('+' || '.join(f"opcode==8'h{x:02x}" for x in s.cs_opcodes['CS_CMD'])+'))','WRONG_CS')
    check("(mask & 16'hf000) != 0",'MASK_WIDTH')
    lines.append('case(opcode)')
    for op,r in s.opcode_rules.items():
        lines.append(f"8'h{op:02x}: begin")
        owned=p._opcode_owned_bytes(r)
        if r['sequence']=='zero':check('sequence_value != 0','SEQUENCE_RULE')
        if r['sequence']=='nonzero':check('sequence_value == 0','SEQUENCE_RULE')
        if r['session_nonzero']:check('session == 0','SESSION_RULE')
        if r['paired']:check('(session==0) != (sequence_value==0)','SEQUENCE_RULE')
        if r['mask_zero']:check('mask != 0','MASK_RULE')
        if r['mask_nonzero']:check('mask == 0','MASK_RULE')
        if s.cs_for_opcode(op)=='CS_CMD':
            for f in s.layout('cmd_command').fields:
                if f.rules.get('only_opcodes') and s.opcodes[op]['name'] not in f.rules['only_opcodes']:
                    span=[i for i in range(f.offset,f.offset+f.size) if i not in owned]
                    if span:check(' || '.join(val(i)+' != 0' for i in span),'RATE_ON_NON_UPDATE' if f.name.startswith('rate_') else 'FIELD_NOT_ALLOWED')
        for lo,hi in r['zero_ranges']:check(nz(lo,hi),'PAYLOAD_NONZERO')
        if r['byte16'] is not None:check('!('+allowed(val(16),r['byte16'])+')','FIELD_RANGE')
        if r['embedded_iol1']:
            lo,hi,bit=r['embedded_iol1']
            # Exact C oracle order collapses any embedded failure to EMBEDDED_FRAME.
            check(f"!embedded_crc_good || {val(lo)}!=8'ha7 || {val(lo+1)}!=1 || ({val(lo+3)} & 8'hf0)!=0 || {val(lo+4,2)}==0 || ({val(lo+8)} & 8'hc0)!=0 || (({val(lo+8)} & 1)!=0) != ({val(lo+6,2)}==0) || ({val(lo+8)} & 8'h{1<<bit:02x})==0",'EMBEDDED_FRAME')
        if r['rest_zero']:
            indices=[i for i in range(16,(174 if s.cs_for_opcode(op)=='CS_FB' else 94)) if i not in owned]
            if indices:check(' || '.join(val(i)+' != 0' for i in indices),'PAYLOAD_NONZERO')
        layout('fb_command' if s.cs_for_opcode(op)=='CS_FB' else 'cmd_command',0,owned)
        if s.cs_for_opcode(op)=='CS_CMD':
            for ch in range(12):
                if ch==0 and 16 in owned:continue
                check(f'!mask[{ch}] && {val(16+4*ch,4)} != 0','UNMASKED_RATE')
        if r['payload_layout']:layout(r['payload_layout'],16,set())
        elif r['payload_pages']:
            lines.append('case('+val(16)+')')
            for name in r['payload_pages']:
                pf=s.layout(name).field('page'); ranges=pf.rules['allowed']
                cases=', '.join("8'd"+str(v) for lo,hi in ranges for v in range(lo,hi+1))
                lines.append(cases+': begin');layout(name,16,set());lines.append('end')
            lines.append("default: if(result==0) result=8'd15; endcase")
        lines.append('end')
    lines.extend(['default: begin end','endcase','end','endmodule',''])
    rtl=OUT/'rtl';rtl.mkdir(parents=True,exist_ok=True);(rtl/'cnc3_command_validate.v').write_text('\n'.join(lines),encoding='utf8')
    for name,magic,module in [('fb_response_CNF3','CNF3','cnc3_feedback_pack'),('cmd_response_CNS3','CNS3','cnc3_status_pack')]:
        lay=s.layout(name);width=(lay.length-2)*8
        fields=[f for f in lay.fields if f.name not in {'magic','abi','crc16'} and not f.must_be_zero]
        ports=[f'input wire [{f.size*8-1}:0] {f.name}' for f in fields]
        text=['`timescale 1ns/1ps','// SPDX-License-Identifier: LicenseRef-Proprietary',
              '// GENERATED from exact frozen IS-1 field offsets. All values are real-provider inputs.',
              '// No ready/valid/safety observations are synthesized or assumed here; transport supplies CRC.',
              'module '+module+' (',',\n'.join(ports)+f',\noutput wire [{width-1}:0] payload);',
              f'assign payload[{width-1} -: 32]=32\'h{magic.encode().hex()};',
              f'assign payload[{width-1-32} -: 8]=8\'d3;']
        for f in lay.fields:
            if f.name in {'magic','abi','crc16'}:continue
            text.append(f"assign payload[{width-1-8*f.offset} -: {f.size*8}]="+('0;' if f.must_be_zero else f.name+';'))
        text+=['endmodule',''];(rtl/(module+'.v')).write_text('\n'.join(text),encoding='utf8')
    (OUT/'frozen-inputs.json').write_text(json.dumps({'external_original_hashes':{str(src):sha(src) for src in files.values()},'copied_hashes':{str((frozen/rel).relative_to(OUT)):sha(frozen/rel) for rel in files},'generator_sha256':sha(Path(__file__)),'rule_scope':'full stateless C command validator; stateful session/ARM/SELFTEST/IOL1 not granted'},indent=2)+'\n')
    return p,s
if __name__=='__main__':build()
