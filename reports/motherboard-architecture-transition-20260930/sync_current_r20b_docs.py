"""Bounded current-paragraph sync; preserve all historical engineering sections."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motherboard-architecture-transition-20260930/r20b-current-doc-sync'
assert not OUT.exists(),'Immutable documentation receipt already exists'
files=['PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir(parents=True)
before={f:sha(ROOT/f) for f in files}
for f in files:
    dst=OUT/'before'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,dst)

source=('The adopted **r20b electrical source contains 2,663 physical footprints: 2,627 purchased fitted parts, 33 bare PCB test pads, one bare chassis bond pad and two DNP footprints**, across 27 source regions. '
        'It includes all twelve motor interfaces, four ABZ receiving paths, 24 general DI, 16 smart DO at the retained 0.5 A/channel and 2 A/four-channel-group limits, actual acquisition/control MCUs, power-entry/rail supervision, protected probe/pendant supplies, process control, two isolated AO channels, four isolated AI channels, RS-485/CAN, compute/ESP sockets, protected microSD/HDMI/USB/Ethernet circuits, actual status indicators and field terminals/chassis coupling. '
        'Native integrated ERC is **zero errors, 68 unsuppressed warnings and no ignored checks**. Independent native source/pin/MPN/footprint/provider and original 327-part/1,229-pin-net preservation checks pass, with **50 focused parent integration tests passed**. '
        'The bounded r20b corrections replace the analog converters with actual wide-input TMR4WI devices, add the AI5 regulator/factory-window monitor and correct monitor VDD, implement the CORE5 seven-ampere source candidate, and correct ten FPGA ghost pads. '
        'These are schematic/source checks, not a full firmware, routed-PCB or physical qualification.')
cad=('Published native CAD **20260930-23** is a separate **1,780-footprint** snapshot with **5,928 track/via items and five filled zones**, board SHA-256 `54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5`. '
     'The fresh independent physical connectivity review finds **2,893 missing joins: 514 fully joined multi-pad nets and 646 incomplete multi-pad nets**. Native DRC has **zero regular geometry violations, no ignored checks and 499 capped unconnected items**; routing does not pass. '
     'The **460 × 340 mm, six-layer, 1.6 mm** outline/stackup remains provisional. It is not the complete 2,663-part source population.')
remaining=('Continue populating/reconciling the full electrical source onto the retained routed PCB, close every required connection and whole-board power/return path, and verify connector mating orientation, card/socket clearance, analog/isolation keepouts, rail/current/thermal budgets and manufacturing rules. '
           'Compute/storage, analog/comms, indicators and field-terminal circuitry now exist in the electrical source; their presence does not prove boot images, device drivers, calibration, cable behavior or assembly qualification. '
           'The 20 ms fault-to-inhibit requirement, unconfigured/missing/partial-power states, loaded target firmware/protocol, vendor FPGA package fit/timing and physical/EMC/thermal behavior remain unqualified. Gerbers, drills, final assembly CPL/drawings and final stackup are not released; `manufacturing_ready` remains false. '
           'Original six-joint/two-encoder runtime results remain historical baseline evidence; twelve fitted interfaces are not twelve proven coordinated axes.')
cost=('The immutable **r20b 2,663-footprint source cost audit** separates 2,627 purchased board parts from bare geometry, DNPs, purchased modules and accessories. It prices **101 exact MPNs and leaves 188 unpriced (748 purchased fitted pieces per board)**. '
      'Known-priced consumed inventory per board at **1/10/100 controllers is US$1,037.19/$839.71/$761.20**. Catalogue purchase cash for those complete build quantities is **US$60,966.48/$67,042.95/$127,501.50**, including unused exact-package MOQ inventory; zero/insufficient stock remains distinct from price. '
      'Those are partial exact-source catalogue baskets, not PCBWay quotations or complete board/kit costs. All complete manufacturing/controller/package totals remain null. The selected ESP module and six standard power mates are priced separately; compute/storage/AI/screens, other mates/accessories, fabrication, assembly, programming/test and kit costs remain unknown. '
      'Independent verification checks 165 frozen files, 873 quantity rows and 13 adversarial controls. The earlier 980-part basket remains historical evidence, never the current total.')
compute=('The user-adopted CM4/CM5 dual-100-pin bay and actual three-bit DIP readout are now present in the native compute source. The selector does not route power or bypass permission. '
         'CM4/CM5 contact mappings have primary source checks; exact Linux images/pinmux, compatibility and thermal/loading still need target qualification. Automatic pre-power hardware ID and software profiles are not implemented. '
         'AUTO remains service-only until exact identity is verified; CB1/CB2 variants remain separately unqualified and machine use disabled. Connector shape alone does not establish electrical compatibility; no routine FPGA/ESP reflash is intended for a previously qualified exchange.')

def replace_line(lines,prefix,new):
    ids=[i for i,l in enumerate(lines) if l.startswith(prefix)]
    assert len(ids)==1,(prefix,ids)
    lines[ids[0]]=new

memory=(ROOT/files[0]).read_text(encoding='utf-8').splitlines()
replace_line(memory,'- **Live physical CAD view','- **Live physical CAD view (30 September 2026):** '+cad+' [Current board review](hardware/board_review/README.md).')
replace_line(memory,'- **Current engineering execution','- **Current engineering execution following that priority:** '+source+' '+remaining+' Source and published PCB snapshots are distinct. [r20b adoption](reports/motherboard-integration-20260930/r20b-2663-adoption.json).')
replace_line(memory,'- **Latest compute-bay decision','- **Latest compute-bay decision (user, 30 September 2026):** '+compute+' See `docs/COMPUTE_CARRIER_STRATEGY.md` and actual `hardware/motherboard_compute/design.json`.')
for i,l in enumerate(memory):
    if l.startswith('- **Latest compute selection and storage detail'):
        old='Storage/provisioning remains a requirement and investigation in `docs/BOOT_STORAGE_AND_PROVISIONING.md`, not fitted hardware or a verified boot image;'
        new='The protected microSD socket and power/signal-isolation circuitry are implemented in the current source; exact cards, boot images, provisioning and optional NVMe remain unqualified in `docs/BOOT_STORAGE_AND_PROVISIONING.md`;'
        assert old in l;memory[i]=l.replace(old,new)
    if l.startswith('- **Latest status-indicator requirement'):
        start=l.index('`docs/STATUS_INDICATORS.md` defines')
        tail=l.index('The shared CLI/UI diagnostics',start)
        memory[i]=l[:start]+'`docs/STATUS_INDICATORS.md` defines the behavior; actual ordinary RGB/single-color indicators, drivers, isolated observations and independent hardware fault overrides are now in the electrical source. Firmware freshness/visual behavior, panel mechanics, full supply loading and physical qualification remain unproved. '+l[tail:]
replace_line(memory,'- **Current exact-MPN sourcing boundary','- **Current exact-MPN sourcing boundary:** '+cost+' [Frozen source/cost receipt](reports/motherboard-cost-20260930/source-r20b-2663-complete-cost-v5/README.md). Earlier MC/r0.3 pricing and package-change records remain historical evidence.')
(ROOT/files[0]).write_text('\n'.join(memory)+'\n',encoding='utf-8')

build=(ROOT/files[1]).read_text(encoding='utf-8').splitlines()
replace_line(build,'**Current physical implementation:**','**Current physical implementation:** '+source+' '+cad+' '+remaining+' [Adoption](../reports/motherboard-integration-20260930/r20b-2663-adoption.json); [uncapped CAD connectivity](../hardware/board_review/revisions/20260930-23/publication-connectivity-routed-r01/review.json).')
replace_line(build,'**Current procurement evidence:**','**Current procurement evidence:** '+cost+' [Frozen current cost receipt](../reports/motherboard-cost-20260930/source-r20b-2663-complete-cost-v5/README.md).')
replace_line(build,'**Compute bay adopted by the user','**Compute bay adopted by the user, 30 September 2026:** '+compute+' See [carrier contract](COMPUTE_CARRIER_STRATEGY.md).')
(ROOT/files[1]).write_text('\n'.join(build)+'\n',encoding='utf-8')

road=(ROOT/files[2]).read_text(encoding='utf-8').splitlines()
replace_line(road,'**Current implementation boundary:**','**Current implementation boundary:** '+source+' '+cad+' '+remaining)
replace_line(road,'Current source costing preserves','Current source costing preserves earlier exact-part/source records without treating old subsets as the current board. '+cost+' [Current audit](../reports/motherboard-cost-20260930/source-r20b-2663-complete-cost-v5/README.md).')
replace_line(road,'**Latest physical compute decision:**','**Latest physical compute decision:** '+compute+' See [carrier contract](COMPUTE_CARRIER_STRATEGY.md).')
(ROOT/files[2]).write_text('\n'.join(road)+'\n',encoding='utf-8')

status=(ROOT/files[3]).read_text(encoding='utf-8')
history='## Historical runtime and circuit records'
assert history in status
oldhead,oldhistory=status.split(history,1)
regression=next(l for l in oldhead.splitlines() if l.startswith('**Full regression scope:**'))
links=('[Current adopted source](motherboard-integration-20260930/r20b-2663-adoption.json), '
       '[native ERC](motherboard-integration-20260930/r20b-native-erc.json), '
       '[independent native source checks](motherboard-integration-20260930/r20b-independent-validation.json), '
       '[published CAD uncapped connectivity](../hardware/board_review/revisions/20260930-23/publication-connectivity-routed-r01/review.json), '
       '[exact source cost and independent verification](motherboard-cost-20260930/source-r20b-2663-complete-cost-v5/README.md).')
newhead='# Controller engineering status — 30 September 2026\n\n'+source+'\n\n'+cad+'\n\n'+remaining+'\n\n'+cost+'\n\n'+links+'\n\n'+regression+'\n\n'
(ROOT/files[3]).write_text(newhead+history+oldhistory,encoding='utf-8')
assert (ROOT/files[3]).read_text(encoding='utf-8').split(history,1)[1]==oldhistory

after={f:sha(ROOT/f) for f in files}
for f in files:
    text=(ROOT/f).read_text(encoding='utf-8')
    assert '2,663' in text and '2,893' in text and '748' in text
    assert sha(OUT/'before'/f)==before[f]
    dst=OUT/'after'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,dst)
receipt=dict(created_utc=datetime.now(timezone.utc).isoformat(),scope='Only current/top paragraphs of four authorized documentation files; engineering status historical section preserved byte-for-byte as text.',
    before_sha256=before,after_sha256=after,source_design_sha256=sha(ROOT/'hardware/motherboard/design.json'),
    adopted_source_receipt_sha256=sha(ROOT/'reports/motherboard-integration-20260930/r20b-2663-adoption.json'),
    source_parts=2663,purchased_source_parts=2627,published_CAD_revision='20260930-23',published_CAD_parts=1780,
    published_CAD_sha256='54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5',
    published_CAD_missing_joins=2893,current_cost_snapshot='source-r20b-2663-complete-cost-v5',
    manufacturing_ready=False,source_hardware_changed=False,historical_status_section_preserved=True)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
