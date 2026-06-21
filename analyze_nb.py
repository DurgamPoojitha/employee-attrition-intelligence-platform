import json

with open("Enterprise_Attrition_Intelligence_Platform_UPGRADED.ipynb", "r") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
md_cells = []
code_cells = []
for i, cell in enumerate(nb['cells']):
    cell_type = cell['cell_type']
    source = "".join(cell.get('source', []))
    if cell_type == 'markdown':
        md_cells.append(source[:200]) # save memory
    elif cell_type == 'code':
        code_cells.append(source)

print("\n--- Markdown Headers ---")
for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source = "".join(cell.get('source', []))
        for line in source.split('\n'):
            if line.startswith('#'):
                print(line.strip())

print("\n--- Code Imports ---")
for code in code_cells:
    for line in code.split('\n'):
        if line.startswith('import ') or line.startswith('from '):
            print(line.strip())

