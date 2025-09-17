
import pandas as pd
import importlib.util
from pathlib import Path

def load_parser(bank):
    spec = importlib.util.spec_from_file_location(f"{bank}_parser", Path(f"custom_parsers/{bank}_parser.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse

def test_parser_output_matches_csv():
    bank = "sbi"
    parse = load_parser(bank)
    csv_path = Path(f"data/{bank}/result.csv")
    pdf_path = Path(f"data/{bank}/sample.pdf")
    file_to_parse = csv_path if csv_path.exists() else pdf_path

    df_out = parse(str(file_to_parse))
    assert not df_out.empty, "Parser returned empty DataFrame"

    if csv_path.exists():
        df_ref = pd.read_csv(csv_path)

        # Fill NaN consistently
        for df in [df_out, df_ref]:
            for col in df.columns:
                if df[col].dtype != 'object':
                    df[col] = df[col].fillna(0.0)
                else:
                    df[col] = df[col].fillna("")

        assert len(df_out) == len(df_ref), f"Row count mismatch: Parsed={len(df_out)}, Reference={len(df_ref)}"

        common_cols = set(df_ref.columns).intersection(set(df_out.columns))
        mismatches = []
        for col in common_cols:
            try:
                pd.testing.assert_series_equal(
                    df_out[col].reset_index(drop=True),
                    df_ref[col].reset_index(drop=True),
                    check_dtype=False
                )
                print(f"OK Column '{col}' matches")
            except AssertionError:
                mismatches.append(col)
                print(f"X Column '{col}' does NOT match")

        if mismatches:
            assert False, f"Mismatched columns: {mismatches}"
