"""Decide whether the PR gate passes, from pql-test output files.

Reads, from --results-dir:
  results-<Model>.json      `pql-test run-tests --output` for each model
  env-<ENV>-<Model>.json    `pql-test retrieve-tests --env <ENV>` for each env check

and ci/gate.json for the suites that must fail and the suites each --env
filter must return.

The gate fails when:
  - any result outside an expected-failure suite fails or errors
  - an expected-failure suite passes, or never runs
  - a model has no results, or every result was skipped
  - an --env filter returns a different set of suites than gate.json expects
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def annotate(level, message):
    """Emit a GitHub Actions annotation when running in Actions, else plain text."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::{level}::{message}")
    else:
        print(f"{level.upper()}: {message}")


def evaluate_runs(results_dir, expected):
    problems, rows, seen_expected = [], [], set()
    files = sorted(results_dir.glob("results-*.json"))
    if not files:
        problems.append(f"No results-*.json files found in {results_dir}")
    for path in files:
        model = path.stem[len("results-"):]
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.get("results", [])
        unexpected, expected_ok = [], 0
        for r in results:
            suite = r.get("suite_name") or r.get("test_name")
            if r.get("skipped"):
                continue
            if suite in expected:
                seen_expected.add(suite)
                if r.get("passed"):
                    unexpected.append(f"{suite} / {r.get('test_name')}: expected to fail but passed")
                else:
                    expected_ok += 1
            elif not r.get("passed"):
                detail = r.get("error") or f"expected {r.get('expected')}, actual {r.get('actual')}"
                unexpected.append(f"{suite} / {r.get('test_name')}: {detail}")
        total, skipped = data.get("total", len(results)), data.get("skipped", 0)
        if total == 0:
            problems.append(f"{model}: no tests were discovered")
        elif skipped == total:
            problems.append(f"{model}: every result was skipped (no XMLA connection?)")
        problems += [f"{model}: {u}" for u in unexpected]
        rows.append((model, data.get("passed", 0), data.get("failed", 0), expected_ok, skipped, total, len(unexpected)))
    for suite in sorted(set(expected) - seen_expected):
        problems.append(f"Expected-failure suite {suite} did not run")
    return problems, rows


def evaluate_env_checks(results_dir, env_checks):
    problems, rows = [], []
    for env, models in env_checks.items():
        for model, want in models.items():
            path = results_dir / f"env-{env}-{model}.json"
            if not path.exists():
                problems.append(f"--env {env} check for {model}: {path.name} not found")
                continue
            got = sorted(t["name"] for t in json.loads(path.read_text(encoding="utf-8")) or [])
            ok = got == sorted(want)
            if not ok:
                problems.append(f"--env {env} for {model} returned {got}, expected {sorted(want)}")
            rows.append((env, model, len(got), "pass" if ok else "FAIL"))
    return problems, rows


def write_summary(run_rows, env_rows, problems):
    lines = ["## PQL.Assert test gate", "",
             "| Model | Passed | Failed | Expected failures | Skipped | Total | Unexpected |",
             "|---|---|---|---|---|---|---|"]
    lines += [f"| {m} | {p} | {f} | {e} | {s} | {t} | {u} |" for m, p, f, e, s, t, u in run_rows]
    if env_rows:
        lines += ["", "| Env filter | Model | Suites | Result |", "|---|---|---|---|"]
        lines += [f"| `{e}` | {m} | {n} | {r} |" for e, m, n, r in env_rows]
    lines += ["", f"**{'FAILED' if problems else 'PASSED'}**"]
    if problems:
        lines += [""] + [f"- {p}" for p in problems]
    text = "\n".join(lines) + "\n"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text)
    print(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-dir", default="ci-results")
    parser.add_argument("--config", default=str(REPO / "ci" / "gate.json"))
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    results_dir = Path(args.results_dir)
    run_problems, run_rows = evaluate_runs(results_dir, config.get("expected_failures", {}))
    env_problems, env_rows = evaluate_env_checks(results_dir, config.get("env_checks", {}))
    problems = run_problems + env_problems

    for p in problems:
        annotate("error", p)
    write_summary(run_rows, env_rows, problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
