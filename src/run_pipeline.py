"""One-command, fail-fast reproduction from committed CSVs."""
import argparse
import importlib
from src.analyze_game_data import project_root,load_data
from src.build_evidence import main as build_evidence
from src.verify_sql import verify
from src.analyze_sensitivity import sensitivity_tables


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--regenerate',action='store_true',help='Explicitly overwrite synthetic source CSVs')
    parser.add_argument('--refresh-docs',action='store_true',help='Refresh generated evidence after reviewed changes')
    args=parser.parse_args()
    if args.regenerate:
        importlib.import_module('src.generate_synthetic_data').main()
    from src.user_retention import run as user_retention
    user_retention(regenerate=args.regenerate, check_docs=not args.refresh_docs)
    load_data(project_root())
    for name in ['game_data','lifecycle','retention','pve','monetization','incident','regional']:
        importlib.import_module('src.analyze_'+name).main()
    output=project_root()/'outputs'
    verify().to_csv(output/'sql_python_parity.csv',index=False)
    payer,baseline=sensitivity_tables()
    payer.to_csv(output/'payer_assumption_sensitivity.csv',index=False)
    baseline.to_csv(output/'baseline_sensitivity.csv',index=False)
    build_evidence(check=not args.refresh_docs)
    print('Pipeline, SQL parity and evidence checks passed')

if __name__=='__main__':main()
