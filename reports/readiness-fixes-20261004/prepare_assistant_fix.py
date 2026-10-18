"""Stage a non-actuating assistant replacement; never launch the external app."""
import hashlib
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXTERNAL = Path('Z:/Programming Projects/Genmitsu1030Cnc/fluidcnc/ai-assistant.js')
EXPECTED = '90a6624e36cba2bd0ab28e77eda844e605edfd17b20a25323f186eb03f32e948'
raw = EXTERNAL.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED, 'External source changed; do not overwrite.'
before = OUT / 'before' / 'external-ai-assistant.js'
before.parent.mkdir(parents=True, exist_ok=True)
if before.exists():
    assert before.read_bytes() == raw
else:
    before.write_bytes(raw)
text = raw.decode('utf-8')
newline = '\r\n' if '\r\n' in text else '\n'
text = text.replace('\r\n', '\n')
start = text.index('    async executeAction(')
end = text.index('    conversationalResponse(', start)
replacement = '''    async executeAction(action, params = {}, originalInput) {
        // Chat and voice are advisory only. Pattern matches are not operator intent,
        // reviewed machine configuration, or authority to send a machine command.
        // Keep this boundary here so direct callers cannot bypass it either.
        let response;
        let proposal = null;
        try {
            switch (action) {
                case 'status':
                    response = this.getStatusReport();
                    break;
                case 'suggestFS':
                    response = this.suggestFeedsAndSpeeds(params.material, params.toolDia);
                    break;
                case 'help':
                    response = this.getHelpText();
                    break;
                default: {
                    const controls = {
                        jog: 'Jog', moveTo: 'Move', rapidXY: 'Move', home: 'Home',
                        zero: 'Work Zero', spindleOn: 'Spindle', spindleOff: 'Spindle',
                        coolantOn: 'Coolant', coolantOff: 'Coolant', toolChange: 'Tool Change',
                        probeZ: 'Probe', probeCorner: 'Probe', probeTool: 'Probe',
                        runJob: 'Job', pause: 'Feed Hold', resume: 'Resume', stop: 'Stop',
                        estop: 'Emergency Stop', analyzeGcode: 'Analyze G-code'
                    };
                    if (!Object.prototype.hasOwnProperty.call(controls, action)) {
                        response = 'That assistant action is not supported. No machine command was sent.';
                        this.onResponse(response);
                        return { success: false, executed: false, response, gcode: null, proposal: null };
                    }
                    proposal = {
                        kind: 'manual-control-review',
                        action,
                        parameters: { ...params },
                        executable: false
                    };
                    response = `I found a reference to the ${controls[action]} operation. ` +
                        'This is an unvalidated suggestion, not an executed command. ' +
                        `Use the dedicated ${controls[action]} controls if you intend that operation. ` +
                        'Chat and voice never send machine commands or start control workflows.';
                }
            }
            this.conversationHistory.push({ role: 'assistant', content: response, time: Date.now() });
            this.onResponse(response);
            return { success: true, executed: false, response, gcode: null, proposal };
        } catch (err) {
            const errMsg = `Error: ${err.message}`;
            this.onError(errMsg);
            return { success: false, executed: false, response: errMsg, gcode: null, proposal: null };
        }
    }
    
'''
text = text[:start] + replacement + text[end:]
text = text.replace('        this.onCommand = options.onCommand || (() => {});\n', '')
text = text.replace('   - Natural language CNC commands', '   - Advisory natural language CNC proposals (no machine-command authority)')
text = text.replace('   - Voice command support', '   - Advisory voice input (dedicated controls execute operations)')
text = text.replace('Use "zero X Y Z" to set the current position as zero.', 'Use the dedicated Work Zero controls to set the current position as zero.')
text = text.replace('Say "change tool 3" to swap tools automatically.', 'Use the dedicated Tool Change controls after checking the machine setup.')
text = text.replace('return { success: true, response };', 'return { success: true, executed: false, response, gcode: null, proposal: null };')
text = text.replace('return `## 🤖 CNC Assistant Commands', 'return `## 🤖 CNC Assistant\n\nChat and voice provide explanations and unvalidated proposals only. They never operate the machine. Use the dedicated machine controls to perform any operation.\n\nThe phrases below identify topics for discussion:')
text = text.replace('Say "home all"', 'Use the dedicated Home controls')
text = text.replace('Say "probe corner" or "zero all"', 'Use the dedicated Probe or Work Zero controls')
text = text.replace('Say "analyze gcode"', 'Use Analyze G-code')
text = text.replace('Say "unlock" to clear alarm (after fixing issue!)', 'Use the dedicated alarm controls only after diagnosing and correcting the cause.')
text = text.replace("this.onResponse('🎤 Voice commands enabled. Speak clearly!');", "this.onResponse('🎤 Voice input enabled for explanations and proposals. Machine controls remain separate.');")
text = text.replace("this.onResponse('🔇 Voice commands disabled');", "this.onResponse('🔇 Voice input disabled');")
assert 'this.grbl.send(' not in text and 'this.onCommand(' not in text
(OUT / 'external-ai-assistant-candidate.js').write_bytes(text.replace('\n', newline).encode('utf-8'))
print('Preserved exact original; staged advisory-only candidate.')
