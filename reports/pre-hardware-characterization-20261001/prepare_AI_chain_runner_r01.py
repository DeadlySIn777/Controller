"""Retain buffer proof and derive a separate, explicit INA149-chain experiment."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
src=HERE/'run_AI_buffer_SPICE_r03.py'
dest=HERE/'run_AI_chain_SPICE_r01.py'
assert not dest.exists()
text=src.read_text()
def swap(a,b):
    global text
    assert text.count(a)==1,(a,text.count(a))
    text=text.replace(a,b)
swap('Source26 four-channel divider/buffer/filter study with unchanged TI OPA model.',
     'Source26 four-channel INA149/divider/buffer/filter study with unchanged TI models.')
swap('matrix = list(itertools.product([14.39,15,15.61], [25,55], [-1,1]))',
     'matrix = list(itertools.product([15,14.39,15.61], [25,55], [-1,1]))')
swap("# Normal actual AGND=0 coordinate; the isolated OPA buffer model converges here.",
     '# Actual AGND=0; nodeset supplies an operating-point guess, not a held voltage or substituted device.')
swap('Source26 buffer-only partial path; unchanged TI OPA model; ideal upstream boundary',
     'Source26 INA149 and OPA active path; unchanged models; ideal power/reference and approximate ADC')
swap('enumerate([(-10,0,10),(-10,10,0),(10,4,6),(10,6,4)])',
     'enumerate([(-10,10,0),(10,10,0),(-10,6,4),(10,6,4)])')
swap("f'BSHIFT_APPROX{i} SHIFT{i} AGND V=v(D{i})+2.5',",
     "f'XINA{i} P{i} N{i} REF REF VCC AGND SHIFT{i} INA149',\n                  f'.nodeset v(shift{i})={initial+2.5} v(scaled{i})={(initial+2.5)*rlo/(rhi+rlo)} v(buf{i})={(initial+2.5)*rlo/(rhi+rlo)} v(adc{i})={(initial+2.5)*rlo/(rhi+rlo)} v(xina{i}.xu1.7)={rail/2}',")
swap("'ac dec 100 10 10Meg'", "'ac dec 100 10 10Meg'") # Preserve actual AC analysis.
swap("scope='Actual Source26 10k/10k divider -> OPA4197 unity buffer -> 47ohm/2.2nF filter; four independent active OPA macromodel cores. IDEAL INA149 output boundary and 1Mohm ADC load approximation. The actual INA149 macromodel FAILED the attempted full-path study; this scoped buffer run does not close that failure.',",
     "scope='Actual Source26 INA149 -> 10k/10k divider -> OPA4197 unity buffer -> 47ohm/2.2nF filter; four simultaneous unchanged INA149/OPA cores. Protected-terminal voltage sources, power/reference and 1Mohm ADC load are still ideal/approximate. This is not complete analog acquisition.',")
swap("'Unmodified OPAx197 model used under ngspice PSA compatibility, at actual AGND=0. INA149 is intentionally absent because its complete four-channel model did not converge. Ideal voltage boundary explicitly substitutes ONLY that upstream block and receives no device validation claim.',",
     "'Unmodified INA149 and OPAx197 models under ngspice PSA compatibility, actual AGND=0. Explicit nodeset guesses only assist initial operating-point convergence; they are not voltage sources and do not replace either active device. Initial conditions/power-up behavior remain unqualified.',")
swap("'Not the complete analog input circuit: NO INA149 model, TBU/current relay/burden/terminal surge behavior',",
     "'Not the complete analog input circuit: no TBU/current relay/burden/terminal surge behavior',")
swap("assert passed, 'Partial active circuit sweep failed; inspect actual retained analyses'",
     "assert passed, 'INA149 active-chain experiment failed; inspect actual retained analyses'")
dest.write_text(text,encoding='utf8')
receipt={'original_buffer_runner_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
         'new_chain_runner_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
         'new_path':str(dest),'original_unchanged':True,'execution_claim':False}
(HERE/'prepare-AI-chain-runner-r01.json').write_text(json.dumps(receipt,indent=2)+'\n')
