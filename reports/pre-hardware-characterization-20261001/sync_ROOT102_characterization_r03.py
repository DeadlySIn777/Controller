"""Update current evidence links/counts; retain original snapshots in reports."""
from pathlib import Path
import hashlib,json
root=Path.cwd();out=root/'reports/pre-hardware-characterization-20261001/ROOT102-current-document-sync-r03';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101'
new='reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06'
reg='reports/pre-hardware-characterization-20261001/characterization-register-r02'
full='reports/pre-hardware-validation-20261001/full-two-cap-r05/report.json'
updates=[]
for name in ['PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md','docs/CURRENT_ACCEPTANCE_GATES.md','hardware/board_review/README.md']:
 p=root/name;before=sha(p);backup=out/'before'/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(p.read_bytes())
 original=root/'reports/pre-hardware-characterization-20261001/ROOT102-current-document-sync-r02/before'/name
 raw=original.read_bytes() if original.exists() else p.read_bytes()
 try:s=raw.decode('utf8')
 except UnicodeDecodeError:
  # Known legacy README encoded only the multiplication sign as single-byte0xd7.
  assert name=='hardware/board_review/README.md'
  s=raw.replace(b'\xd7','×'.encode('utf8')).decode('utf8')

 # Only these current r101/26 passages are replaced. Older numbered evidence remains in its original files.
 replacements={
  '20261001-26':'20261001-28','Source26/r101':'Source26/r102','Source26/ROOT101':'Source26/ROOT102',
  '**adopted working PCB r101**':'**adopted working PCB r102**',
  '81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226':'769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5',
  '11,635':'11,641','3,528':'3,524','3528 required':'3524 required',
  '106 actual owned-bypass loops, 217 receiving-return endpoint checks':'108 actual owned-bypass loops, 221 receiving-return endpoint checks',
  '106 bypass loops, 217 receiving-return endpoints':'108 bypass loops, 221 receiving-return endpoints',
  old+'/adoption.json':new+'/adoption.json',old+'/independent-connectivity/review.json':new+'/independent-connectivity/review.json',
  'characterization-register-r01/requirements-and-coverage.json':'characterization-register-r02/requirements-and-coverage.json',
  'characterization-register-r01/provisional-datasheet.json':'characterization-register-r02/provisional-datasheet.json',
 }
 for a,b in replacements.items():s=s.replace(a,b)
 prefix='' if name=='PROJECT_MEMORY.md' else ('../../' if name.startswith('hardware/') else '../')
 paragraph=(f'**Latest verified increment — Source26/ROOT102:** two existing capacitor poses and six conductors complete two additional owned bypass loops; no electrical source, parts, pin nets or rating changed. Actual native and independent connectivity agree on **3,524 required joins remaining**, with zero orphan copper. Native regular DRC is **0 errors/0 warnings/no ignored checks**; ERC remains **0 errors/70 unsuppressed warnings**. [Full disconnected r05]({prefix}{full}) passed **17 stages**, left **9 blocked** and **1 physical stage unrun**, with **0 failed stages**; **1,876 host cases and 235 native KiCad cases pass**, five Windows symlink cases remain skipped, and all **3,327 scoped source hashes** stayed unchanged. This supersedes the earlier r101 regression as the current exact-board run. [Current adoption]({prefix}{new}/adoption.json).\n\n'
 f'[Updated characterization]({prefix}{reg}/requirements-and-coverage.json) retains all 15 subsystem, 22 fault and nine machine requirements. Twelve changing-speed/reversal pulse generators pass 43,200,324 edge/count checks; four ideal-input encoder components and actual CNC3 structural SPI/codec RTL pass their scoped sweeps. The real manufacturer OPA buffer model passes 12 simultaneous four-channel cases, alongside 96 passive filter cases and two numerical-sensitivity studies. **Complete stateful CNC3/HAL/machine integration and whole-circuit analog qualification remain open.** Failed full-chain amplifier convergence and the encrypted ADC model are recorded; ideal boundaries are not physical substitutes.\n\n'
 f'[Native drill/land screening]({prefix}reports/motherboard-pcb-integration-20261001/two-cap-full-drill-SMD-audit-r01/receipt.json) identifies **275 existing drilled vias overlapping 279 same-net paste SMD lands**. This is a lower bound: exact tangency and assembly registration margins need further checking. Each location needs layout correction or an explicitly qualified filled/capped fabrication/assembly disposition; ordinary DRC and tenting do not close this work. No fabrication package or manufacturing readiness is claimed.\n\n')
 i=s.index('\n',s.index('#'))+1;s=s[:i]+'\n'+paragraph+s[i:].lstrip('\n')
 if name=='hardware/board_review/README.md':
  s=s.replace('Failed publication revision 20261001-25 is retained as an unpublished attempt and is not in the revision selector.',
    'Failed publication revisions 20261001-25 and 20261001-27 are retained as unpublished attempts and are not in the revision selector. Revision28 packages the exact previously checked local footprints and 3D resources with the unchanged ROOT102 board bytes.')
 if name=='docs/CURRENT_ACCEPTANCE_GATES.md':
  s=s.replace('Fresh ROOT101 regression passed 1,847 host and 235 actual KiCad cases; five Windows symlink cases remain skipped.',
    'Fresh ROOT102 r05 regression passed 1,876 host and235actual KiCad cases; five Windows symlink cases remain skipped.')
  s=s.replace('Partial component evidence:144 twelve-generator scenarios plus four real copied-RTL mutation controls pass. Actual complete CNC3 endpoint/HAL and full electrical/vendor/physical stages remain unfinished.',
    'Partial actual component evidence:144 steady twelve-generator cases plus dynamic/reversal and four-encoder sweeps pass; CNC3 structural SPI/codec/family mapping and selected passive/buffer SPICE pass. Stateful CNC3/HAL,complete analog chain,full-load machine,vendor fit and physical qualification remain unfinished.')
 p.write_text(s,encoding='utf8',newline='\n');updates.append(dict(path=name,before_sha256=before,after_sha256=sha(p)))
(out/'receipt.json').write_text(json.dumps(dict(passed=True,changes=updates,source_or_PCB_bytes_changed=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,files=len(updates),source_revision=26,board='ROOT102',published='20261001-28')))
