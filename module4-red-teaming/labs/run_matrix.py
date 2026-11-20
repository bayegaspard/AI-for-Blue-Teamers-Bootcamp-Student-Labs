#!/usr/bin/env python3
"""
run_matrix.py - run every Module 4 payload against one or more real models, in both
postures, N times each, and print a Markdown results table.

It uses exactly the same prompts (common/soc_assistant.py) and the same scoring
(inject.assess) as the student lab, so the table shows what students will see.

    python3 run_matrix.py                                   # OLLAMA_MODEL from .env, 3 runs
    python3 run_matrix.py --models llama3.1:8b llama3.2:3b --runs 3 > results.md

Point OLLAMA_HOST at the Ollama you want to test (the GPU VM or a local install).
Defensive/educational tooling: the payloads only flip a verdict or leak a demo prompt.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inject                                              # noqa: E402
from common.ollama_client import OllamaClient, OllamaError  # noqa: E402  (path set by inject)
from common import soc_assistant as soc                     # noqa: E402


def short(assessment: str) -> str:
    """Collapse an assess() read-out to a one-word outcome for the table."""
    a = assessment.upper()
    if a.startswith("ATTACK SUCCEEDED"):
        return "WIN"
    if a.startswith("CAUGHT"):
        return "caught"
    if a.startswith("MODEL REFUSED"):
        return "refused"
    if a.startswith("NO VERDICT"):
        return "no-verdict"
    if a.startswith("ATTACK STOPPED"):
        return "stopped"
    if "PLAYED ALONG" in a:
        return "WIN"
    if "STAYED IN ITS ANALYST ROLE" in a:
        return "stopped"
    if "CORRECTLY KEPT" in a:
        return "correct"
    if "MISS" in a:
        return "MISS"
    return "?"


def cell(outcomes: list[str]) -> str:
    """e.g. ['WIN','WIN','stopped'] -> 'WIN 2/3'; mixed non-wins listed briefly."""
    n = len(outcomes)
    wins = outcomes.count("WIN") + outcomes.count("MISS")
    if wins:
        label = "MISS" if "MISS" in outcomes else "WIN"
        return f"**{label} {wins}/{n}**"
    uniq = sorted(set(outcomes))
    return " / ".join(f"{u} {outcomes.count(u)}/{n}" for u in uniq)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--models", nargs="+", default=[os.environ.get("OLLAMA_MODEL", "llama3.1:8b")])
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--payloads", nargs="+", default=list(inject.PAYLOADS))
    args = p.parse_args()

    for model in args.models:
        client = OllamaClient(model=model)
        print(f"\n### {model}  ({args.runs} runs per cell, host {client.host})\n")
        print("| Payload | Kind | Vulnerable | Hardened |")
        print("| --- | --- | --- | --- |")
        for name in args.payloads:
            _desc, text, kind = inject.PAYLOADS[name]
            row = []
            for mode in ("vulnerable", "hardened"):
                outs = []
                for _ in range(args.runs):
                    try:
                        r = soc.triage(client, text, mode)
                    except OllamaError as e:
                        print(f"[FAIL] {model}: {e}", file=sys.stderr)
                        return 1
                    outs.append(short(inject.assess(r, kind, mode)))
                row.append(cell(outs))
            print(f"| `{name}` | {kind} | {row[0]} | {row[1]} |", flush=True)
    print("\nWIN = the attack landed (verdict forced to benign, or prompt disclosed). "
          "MISS = the control alert was called benign with no injection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
