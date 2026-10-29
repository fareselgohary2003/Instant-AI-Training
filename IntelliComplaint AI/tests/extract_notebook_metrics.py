import json

with open('notebook6caffa8944.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

extracted = []
target_cells = [30, 38, 40, 42, 50, 52, 54, 62, 64, 66, 76, 84, 86, 88]

for c_idx in target_cells:
    if c_idx < len(nb['cells']):
        cell = nb['cells'][c_idx]
        src = ''.join(cell.get('source', []))
        outs = []
        for out in cell.get('outputs', []):
            if out.get('name') == 'stdout':
                txt = out.get('text', '')
                if isinstance(txt, list): txt = ''.join(txt)
                outs.append({'type': 'stdout', 'text': txt})
            if 'data' in out:
                for k, v in out['data'].items():
                    if k in ['text/plain', 'text/html']:
                        val = ''.join(v) if isinstance(v, list) else str(v)
                        outs.append({'type': f'data_{k}', 'text': val})
        extracted.append({
            'cell_idx': c_idx,
            'source_snippet': src[:400],
            'outputs': outs
        })

with open('notebook_extracted_metrics.json', 'w', encoding='utf-8') as f:
    json.dump(extracted, f, indent=2, ensure_ascii=False)

print("Extracted to notebook_extracted_metrics.json successfully.")
