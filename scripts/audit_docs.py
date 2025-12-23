import json
from pathlib import Path

ROOT = Path('docs')
OUT = Path('artifacts/governance')
OUT.mkdir(parents=True, exist_ok=True)

categories = {
    'governance': [],
    'spec': [],
    'verification': [],
    'personas': [],
    'engine': [],
    'derived': []
}

for p in sorted(ROOT.rglob('*.md')):
    rel = str(p.relative_to(ROOT))
    if rel.startswith('governance'):
        categories['governance'].append(rel)
    elif rel.startswith('persona') or rel.startswith('personas'):
        categories['personas'].append(rel)
    elif rel.startswith('verification'):
        categories['verification'].append(rel)
    elif rel.startswith('engine'):
        categories['engine'].append(rel)
    elif rel.startswith('spec'):
        categories['spec'].append(rel)
    else:
        categories['derived'].append(rel)

report = {'categories': categories, 'total_files': sum(len(v) for v in categories.values())}
report_path = OUT / 'doc_classification_report.json'
report_path.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
