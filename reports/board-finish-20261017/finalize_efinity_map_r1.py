"""Review the completed vendor map without rerunning it or rewriting its outputs."""
import copy
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

H = Path(__file__).resolve().parent
RUN = H / 'efinity-functional-SIM2-map-r1'
OUT = H / 'efinity-functional-SIM2-map-review-r1'


def sha(p):
    with Path(p).open('rb') as s:
        return hashlib.file_digest(s, 'sha256').hexdigest()


def semantic(e):
    return (e.tag, tuple(sorted(e.attrib.items())), (e.text or '').strip(), tuple(map(semantic, e)))


def main():
    assert not OUT.exists()
    plan = json.loads((RUN / 'plan.json').read_bytes())
    runner = H / 'run_efinity_sim2_map_guarded.py'
    assert sha(runner) == plan['input_SHA256'][str(runner)]
    for row in plan['source_inventory']:
        assert sha(row['source']) == sha(row['copy']) == row['SHA256']
    bat = Path('C:/Efinity/2026.1/bin/efx_run.bat')
    assert sha(bat) == plan['input_SHA256'][str(bat)]
    # Reconstruct exactly the pre-run XML builder from its frozen, hashed runner.
    # Execute only the declaration-free construction section, not any tool/process code.
    source = runner.read_text()
    builder = source[source.index('    ns = "http://www.efinixinc.com/enf_proj"'):source.index('    xml = OUT / "cnc3_runtime_sim.xml"')]
    scope = {'ET': ET, 'Path': Path, 'inventory': plan['source_inventory']}
    exec('\n'.join(line[4:] for line in builder.splitlines()), scope)
    expected = scope['project']
    ET.indent(expected)
    initial = io.BytesIO()
    ET.ElementTree(expected).write(initial, encoding='UTF-8', xml_declaration=True)
    xml = RUN / 'cnc3_runtime_sim.xml'
    # ElementTree's pathname writer uses platform newlines; BytesIO does not.
    original_bytes = initial.getvalue().replace(b'\n', b'\r\n')
    assert hashlib.sha256(original_bytes).hexdigest() == plan['input_SHA256'][str(xml)]
    observed = ET.parse(xml).getroot()
    assert semantic(expected) == semantic(observed), 'Unexpected vendor XML semantic edit'
    log = (RUN / 'vendor-map.log').read_text()
    assert re.search(r'\bmap\s*:\s*PASS\b', log)
    report = (RUN / 'outflow/cnc3_runtime_sim.map.rpt').read_text()
    summary = report.split('### ### Resource Summary (begin) ### ### ###')[-1]
    resources = {key: int(value) for key, value in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)', summary, re.M)}
    assert resources == {'EFX_ADD': 2156, 'EFX_LUT4': 50336, 'EFX_MULT': 1, 'EFX_FF': 48144, 'EFX_GBUFCE': 1}
    state = (RUN / 'outflow/cnc3_runtime_sim.proj_state.ini').read_text()
    assert 'last_run_state = pass' in state and 'last_run_flow = syn' in state
    native = (RUN / 'outflow/cnc3_runtime_sim.log').read_text()
    assert 'Stage completed: map' in native
    warnings = (RUN / 'outflow/cnc3_runtime_sim.warn.log').read_text()
    async_rows = [x for x in warnings.splitlines() if 'because read port is not synchronous' in x]
    assert len(async_rows) == 8 and all('cnc3_event_bank.v:7' in x for x in async_rows)
    samples = [json.loads(x) for x in (RUN / 'resource-samples.jsonl').read_text().splitlines()]
    record = {
        'status': 'NATIVE_VENDOR_MAP_COMPLETED_SIM2_RESOURCE_DIAGNOSTIC_REVIEWED_FIT_NOT_CLOSED',
        'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'vendor_map_reported_PASS': True,
        'supervisor_completion': 'FAILED final byte-hash assertion: vendor rewrote XML serialization; original runner/output retained',
        'project_before_bytes_reconstructed_and_hash_matched': True,
        'project_after_semantics_exact': True,
        'sources_and_runner_unchanged': True,
        'functional_top': 'cnc3_runtime_sim', 'device': 'T20F256', 'timing_model': 'I4',
        'resources': resources, 'block_RAMs_reported': 0,
        'native_async_read_memory_warnings': len(async_rows),
        'resource_cause': 'Eight 32x160 event banks mapped into logic; memory inference and large combinational event logic need correction',
        'scope': 'Full functional simulation boundary, not the missing physical 135-pin motherboard wrapper',
        'physical_fit_place_route_static_timing': 'OPEN_UNEXECUTED',
        'all_ports_inputs': 451, 'all_ports_outputs': 2380,
        'peak_sampled_total_CPU_percent': max(x['CPU_percent'] for x in samples),
        'samples_at_or_above_80_percent': sum(x['CPU_percent'] >= 80 for x in samples),
        'native_reports_and_input_SHA256': {str(p): sha(p) for p in [Path(__file__), RUN/'plan.json', runner, xml,
            RUN/'vendor-map.log', RUN/'resource-samples.jsonl', *sorted((RUN/'outflow').glob('*'))] if p.is_file()},
        'PNR_bitstream_or_programming': False, 'adopted': False, 'manufacturing_ready': False,
    }
    OUT.mkdir()
    (OUT/'reconstructed-original-project.xml').write_bytes(original_bytes)
    (OUT/'receipt.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: record[k] for k in ('status', 'resources', 'native_async_read_memory_warnings', 'peak_sampled_total_CPU_percent')}))


if __name__ == '__main__':
    main()
