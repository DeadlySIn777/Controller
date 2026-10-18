"""Read only Controller-encoded Claude sessions; emit bounded board context."""
from collections import Counter, deque
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path('C:/Users/Gluis/.claude/projects/C--Users-Gluis-OneDrive-Documents-ChatGPT-Controller')
BOARD = re.compile(r'(?i)(pcb-runs|ROOT10[456]|r0[6-8].{0,25}(ripup|stitch|power|connect)|rip-up|In3 bridge|corridor_router|net_partitions)')


def message_text(item):
    value = item.get('summary') if item.get('type') == 'summary' else item.get('message', {}).get('content')
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(block.get('text', '') for block in value
                         if isinstance(block, dict) and block.get('type') == 'text')
    return ''


def main():
    output = []
    for path in sorted(ROOT.glob('*.jsonl')):
        data = path.read_bytes()
        counts = Counter()
        latest = deque(maxlen=10)
        compact = deque(maxlen=1)
        cwd = set()
        errors = []
        for line_no, line in enumerate(data.splitlines(), 1):
            try:
                item = json.loads(line)
            except ValueError:
                errors.append(line_no)
                continue
            counts[item.get('type', 'UNKNOWN')] += 1
            if item.get('cwd'):
                cwd.add(item['cwd'])
            text = message_text(item)
            if not BOARD.search(text):
                continue
            record = {'line': line_no, 'timestamp': item.get('timestamp'),
                      'type': item.get('type'), 'uuid': item.get('uuid'),
                      'characters': len(text), 'text_sha256': sha256(text.encode()).hexdigest(),
                      'is_compact_summary': bool(item.get('isCompactSummary'))}
            if item.get('isCompactSummary') or item.get('type') == 'summary':
                compact.append(dict(record, excerpt=text[:15000], excerpt_truncated=len(text) > 15000))
            if item.get('type') in ('assistant', 'user'):
                latest.append(dict(record, excerpt=text[:1000], excerpt_truncated=len(text) > 1000))
        after = path.read_bytes()
        output.append({'path': str(path), 'bytes': len(data), 'sha256': sha256(data).hexdigest(),
                       'unchanged_during_read': data == after,
                       'mtime_ns_after': path.stat().st_mtime_ns,
                       'types': dict(counts), 'cwd_values': sorted(cwd),
                       'parse_error_lines': errors, 'last_relevant_compact_summary': list(compact),
                       'last_relevant_messages': list(latest),
                       'coverage': 'Structured main-session scan and bounded relevant text only; tool payloads/subagent transcripts not reviewed'})
    target = Path(__file__).parent / 'controller-session-context.json'
    if target.exists():
        raise ValueError('New receipt required; existing evidence is not overwritten')
    target.write_text(json.dumps(output, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(output, indent=1))


if __name__ == '__main__':
    main()
