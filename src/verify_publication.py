"""Verify displayed headline values and execute notebook Python cells in order.

A dependency-light execution check, not a Jupyter UI/rendering test. Notebook has
no magics or widget dependencies. Outputs are intentionally not committed.
"""
import json
import re
from pathlib import Path
import matplotlib.pyplot as plt
from src.build_evidence import main as verify_evidence

ROOT=Path(__file__).resolve().parents[1]

def verify_readmes():
    verify_evidence(check=True)
    claims={key:float(value) for key,value in re.findall(
        r'\| ([a-z0-9_]+) \| (-?[0-9.]+) \|',
        (ROOT/'docs/verified_claims.md').read_text(encoding='utf-8'))}
    for name in ['README.md','README_KR.md']:
        count=0
        for line in (ROOT/name).read_text(encoding='utf-8').splitlines():
            for key,value in re.findall(r'claim:([a-z0-9_]+):(-?[0-9.]+)',line):
                if claims[key] != float(value):
                    raise AssertionError(f'{name}: stale {key}')
                visible=line.split('<!--')[0].replace('−','-')
                if value not in visible:
                    raise AssertionError(f'{name}: claim not displayed: {key}')
                count+=1
        if count != 7:
            raise AssertionError(f'{name}: expected seven audited headline values, got {count}')
    print('Both README headline tables match source-derived evidence')

def verify_notebook():
    notebook=ROOT/'notebooks/game_user_behavior_analysis.ipynb'
    cells=json.loads(notebook.read_text(encoding='utf-8'))['cells']
    namespace={'__name__':'__notebook__'}
    count=0
    for i,cell in enumerate(cells):
        if cell['cell_type']=='code':
            exec(compile(''.join(cell['source']),f'{notebook.name}:cell{i}','exec'),namespace)
            plt.close('all')
            count+=1
    print(f'Notebook: all {count} Python code cells executed successfully')

def main():
    verify_readmes()
    verify_notebook()
    from PIL import Image
    for path in (ROOT/'images').glob('*.png'):
        with Image.open(path) as chart:
            chart.load()
    print('All generated chart files decode successfully')

if __name__=='__main__': main()
