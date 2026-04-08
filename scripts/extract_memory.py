import json
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path(__file__).resolve().parent.parent / 'memory' / 'memories.json'


def append_memory(summary, tags, kind='note'):
    items = json.loads(MEMORY_FILE.read_text())
    items.append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'kind': kind,
        'summary': summary,
        'tags': tags,
    })
    MEMORY_FILE.write_text(json.dumps(items, indent=2))


if __name__ == '__main__':
    append_memory('Manual test memory appended.', ['test', 'manual'])
