import json

with open('notebook_extracted_metrics.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lines = []
for item in data:
    c = item['cell_idx']
    lines.append(f"=== CELL {c} ===")
    for o in item['outputs']:
        t = o['text']
        # Clean special unicode characters
        t_clean = t.encode('ascii', errors='replace').decode('ascii')
        lines.append(t_clean)

with open('clean_notebook_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Wrote clean_notebook_summary.txt")
