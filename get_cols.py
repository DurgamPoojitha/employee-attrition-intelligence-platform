import json
with open("Enterprise_Attrition_Intelligence_Platform_UPGRADED.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell.get('source', []))
        if "pd.read_csv" in source or "load_dataset" in source or "url" in source:
            print("DATA LOADING CELL:")
            print(source)
            break
