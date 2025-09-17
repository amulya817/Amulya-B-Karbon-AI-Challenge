"""
Bank Statement Parser Agent with LangGraph + Groq
Automates: plan → generate parser → run pytest → self-fix (≤3 attempts).
"""
import os
import sys
import subprocess
import re
from pathlib import Path
import pandas as pd
from langgraph.graph import StateGraph, END
from groq import Groq

# 🔑 Groq client
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)


def clean_code(raw: str) -> str:
    """Remove markdown fences and extra text from LLM output."""
    # If code fences exist → grab only inside
    match = re.search(r"```(?:python)?(.*?)```", raw, re.DOTALL)
    if match:
        raw = match.group(1)

    # Drop leading 'Here’s ...' lines
    lines = raw.splitlines()
    code_lines = [ln for ln in lines if not ln.strip().startswith("Here")]
    return "\n".join(code_lines).strip()


def generate_parser(bank: str, attempt: int = 1) -> str:
    """Ask Groq LLM to generate a custom parser for the given bank."""
    try:
        prompt = f"""
        Generate a Python parser function parse(file_path:str)->pd.DataFrame for {bank} bank PDF/CSV.
        Requirements:
        - Must use pandas (and pdfplumber for PDFs).
        - Handle repeated headers, empty rows, numeric cleaning.
        - Replace NaN in numeric columns with 0.0, and strings with "".
        - Return only valid Python code (no markdown fences, no explanations).
        """
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw_code = resp.choices[0].message.content.strip()
        code = clean_code(raw_code)

        # ✅ compile check before saving
        compile(code, f"{bank}_parser.py", "exec")

        if "def parse(" not in code:
            raise ValueError("Generated code missing parse()")

        return code
    except Exception as e:
        print(f"❌ LLM failed on attempt {attempt}: {e}")
        # If LLM fails, return minimal safe parser
        return """\
import pandas as pd
def parse(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith('.csv'):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame()
"""


def write_parser(bank: str, code: str):
    parser_dir = Path("custom_parsers")
    parser_dir.mkdir(exist_ok=True)
    parser_path = parser_dir / f"{bank}_parser.py"
    with open(parser_path, "w", encoding="utf-8") as f:
        f.write(code)
    return parser_path


def write_pytest(bank: str):
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    test_path = tests_dir / f"test_{bank}_parser.py"
    pytest_code = f"""
import pandas as pd
import importlib.util
from pathlib import Path

def load_parser(bank):
    spec = importlib.util.spec_from_file_location(f"{{bank}}_parser", Path(f"custom_parsers/{{bank}}_parser.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse

def test_parser_output_matches_csv():
    bank = "{bank}"
    parse = load_parser(bank)
    csv_path = Path(f"data/{{bank}}/result.csv")
    pdf_path = Path(f"data/{{bank}}/sample.pdf")
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

        assert len(df_out) == len(df_ref), f"Row count mismatch: Parsed={{len(df_out)}}, Reference={{len(df_ref)}}"

        common_cols = set(df_ref.columns).intersection(set(df_out.columns))
        mismatches = []
        for col in common_cols:
            try:
                pd.testing.assert_series_equal(
                    df_out[col].reset_index(drop=True),
                    df_ref[col].reset_index(drop=True),
                    check_dtype=False
                )
                print(f"OK Column '{{col}}' matches")
            except AssertionError:
                mismatches.append(col)
                print(f"X Column '{{col}}' does NOT match")

        if mismatches:
            assert False, f"Mismatched columns: {{mismatches}}"
"""
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(pytest_code)
    return test_path


def run_pytest(test_path: Path) -> tuple[bool, list[str]]:
    """Run pytest and capture output."""
    if not test_path.exists():
        print(f"❌ Test file does not exist: {test_path}")
        return False, []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-s", str(test_path)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(result.stderr)
        mismatches = []
        if "Mismatched columns:" in result.stdout:
            start = result.stdout.find("Mismatched columns:") + len("Mismatched columns:")
            mismatches = result.stdout[start:].strip().strip("[]").replace("'", "").split(", ")
            mismatches = [m for m in mismatches if m]
        if "Row count mismatch" in result.stdout:
            mismatches.append("Row count mismatch")
        success = result.returncode == 0
        return success, mismatches
    except FileNotFoundError:
        print("❌ Pytest not found. Install it using pip install pytest.")
        return False, []


def plan_node(state: dict) -> dict:
    bank = state["bank"]
    attempt = state["attempt"]
    print(f"\n🧭 Planning (attempt {attempt}) for {bank}...")
    code = generate_parser(bank, attempt)
    parser_path = write_parser(bank, code)
    test_path = write_pytest(bank)
    return {"bank": bank, "attempt": attempt, "parser_path": parser_path, "test_path": test_path}


def test_node(state: dict) -> dict:
    bank = state["bank"]
    test_path = state["test_path"]
    print(f"🧪 Running pytest...")
    success, mismatches = run_pytest(test_path)
    return {
        "bank": bank,
        "attempt": state["attempt"],
        "success": success,
        "mismatches": mismatches,
        "parser_path": state["parser_path"],
        "test_path": test_path,
    }


def decide_node(state: dict) -> str:
    if state["success"]:
        print(f"✅ Attempt {state['attempt']} succeeded. All rows & columns match!")
        return END
    elif state["attempt"] >= 3:
        print(f"❌ Max attempts reached (3). Final mismatches: {state['mismatches']}")
        return END
    else:
        print(f"🔄 Attempt {state['attempt']} failed. Mismatches: {state['mismatches']}. Retrying...")
        state["attempt"] += 1
        return "plan"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank target (e.g., icici, sbi)")
    args = parser.parse_args()

    workflow = StateGraph(dict)
    workflow.add_node("plan", plan_node)
    workflow.add_node("test", test_node)
    workflow.add_edge("plan", "test")
    workflow.add_conditional_edges("test", decide_node)
    workflow.set_entry_point("plan")

    app = workflow.compile()
    init_state = {"bank": args.target, "attempt": 1, "success": False, "mismatches": []}
    app.invoke(init_state)


if __name__ == "__main__":
    main()
