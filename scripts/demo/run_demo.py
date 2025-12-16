#!/usr/bin/env python3
"""Demo runner: runs a series of demo specs through self-host and collects results.

Usage: python scripts/demo/run_demo.py
"""
import json
import os
import shutil
from pathlib import Path


DEMO_SPECS = {
    "raw": "demos/raw_input.txt",
    "convertible": "demos/convertible.json",
    "structured": "demos/structured.json",
    "valid": "demos/valid.json",
}

OUTPUT_DIR = Path("demo_outputs")


def run():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from shieldcraft.main import run_self_host

    results = []
    for name, path in DEMO_SPECS.items():
        print(f"[DEMO] Running {name} -> {path}")
        # Clean selfhost outputs
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        try:
            run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        except Exception as e:
            print(f"[DEMO] self-host run for {name} errored: {e}")
        # Copy outputs
        outdir = OUTPUT_DIR / name
        outdir.mkdir(parents=True, exist_ok=True)
        for fname in ['summary.json', 'manifest.json', 'governance_bundle.json', 'audit_index.json']:
            s = Path('.selfhost_outputs') / fname
            if s.exists():
                shutil.copy(s, outdir / fname)
        results.append((name, outdir))

    # Generate demo report
    report_lines = ["# ShieldCraft Demo Report", ""]
    for name, outdir in results:
        report_lines.append(f"## {name}")
        sum_path = outdir / 'summary.json'
        if sum_path.exists():
            s = json.loads(sum_path.read_text())
            report_lines.append(f"- conversion_state: {s.get('conversion_state')}")
            cp = s.get('conversion_path') or {}
            if cp:
                report_lines.append(f"- next_state: {cp.get('next_state')}")
                br = cp.get('blocking_requirements') or []
                report_lines.append(f"- blocking_requirements: {[b.get('code') for b in br]}")
            if s.get('execution_preview'):
                ep = s.get('execution_preview')
                report_lines.append(f"- hypothetical artifacts: {ep.get('would_generate')}")
                report_lines.append(f"- risk_level: {ep.get('risk_level')}")
        else:
            report_lines.append("- no summary emitted")
        report_lines.append("")

    (OUTPUT_DIR / 'demo_report.md').write_text('\n'.join(report_lines))
    print(f"[DEMO] report written to {OUTPUT_DIR / 'demo_report.md'}")


if __name__ == '__main__':
    run()
