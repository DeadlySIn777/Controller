"""Freeze only the latest ROOT106 summary and bounded recent board messages."""
from collections import deque
from hashlib import sha256
import json
from pathlib import Path
import re
from inspect_sessions import message_text

HERE = Path(__file__).parent
SOURCE = Path('C:/Users/Gluis/.claude/projects/C--Users-Gluis-OneDrive-Documents-ChatGPT-Controller/280553e2-7c85-48b3-a5fa-96a4c2e06e60.jsonl')
PATTERN = re.compile(r'(?i)(pcb-runs|ROOT10[456]|\br0[6-8]\b|rip-up|In3|corridor_router|net_partitions|unrouted|KiCad|\bboard\b|\bcopper\b|\bstitch\w*|\bE1\b)')

data = SOURCE.read_bytes()
recent = deque(maxlen=12)
summary = None
for number, line in enumerate(data.splitlines(), 1):
    try:
        item = json.loads(line)
    except ValueError:
        continue
    text = message_text(item)
    if not PATTERN.search(text):
        continue
    record = {'line': number, 'timestamp': item.get('timestamp'), 'type': item.get('type'),
              'uuid': item.get('uuid'), 'characters': len(text), 'text_sha256': sha256(text.encode()).hexdigest()}
    if item.get('isCompactSummary'):
        summary = (record, text)
    elif item.get('type') == 'assistant' and text:
        recent.append(dict(record, excerpt=text[:5000], excerpt_truncated=len(text) > 5000))
if summary is None:
    raise ValueError('No relevant compact summary')
record, text = summary
path = HERE / 'latest-board-summary.txt'
if path.exists():
    raise ValueError('Summary evidence already exists')
path.write_bytes(text.encode())
record['frozen_path'] = str(path)
output = {'source': str(SOURCE), 'source_sha256': sha256(data).hexdigest(),
          'source_unchanged_during_read': data == SOURCE.read_bytes(),
          'latest_summary': record, 'recent_board_assistant_messages': list(recent),
          'not_authority': 'Prior agent memories/transcripts are source context, not fresh native measurements or user authorization'}
target = HERE / 'recent-board-context.json'
if target.exists():
    raise ValueError('Receipt already exists')
target.write_text(json.dumps(output, indent=1) + '\n', encoding='utf-8')
print(json.dumps({'summary_tail': text[15000:], 'recent': list(recent)}, indent=1))
