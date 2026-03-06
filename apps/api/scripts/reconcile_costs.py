#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator')
ACTUALS = ROOT / 'finance' / 'cost-actuals-history.csv'
INVOICES = ROOT / 'finance' / 'provider-invoice-template.csv'
OUT = ROOT / 'finance' / 'cost-reconciliation.md'


def load_actuals_monthly() -> dict[str, float]:
    out = defaultdict(float)
    if not ACTUALS.exists():
        return out
    with ACTUALS.open() as f:
        r = csv.DictReader(f)
        for row in r:
            ts = row.get('captured_at_utc', '')
            try:
                month = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m')
            except Exception:
                continue
            out[month] += float(row.get('estimated_cost_usd') or 0.0)
    return out


def load_invoices_monthly() -> dict[str, float]:
    out = defaultdict(float)
    if not INVOICES.exists():
        return out
    with INVOICES.open() as f:
        r = csv.DictReader(f)
        for row in r:
            month = (row.get('month') or '').strip()
            if not month:
                continue
            out[month] += float(row.get('billed_usd') or 0.0)
    return out


def main() -> int:
    est = load_actuals_monthly()
    inv = load_invoices_monthly()
    months = sorted(set(est.keys()) | set(inv.keys()))

    lines = [
        '# Cost Reconciliation (Estimated vs Billed)',
        '',
        '| Month | Estimated USD | Billed USD | Variance USD | Variance % |',
        '|---|---:|---:|---:|---:|',
    ]

    for m in months:
        e = round(est.get(m, 0.0), 6)
        b = round(inv.get(m, 0.0), 6)
        v = round(b - e, 6)
        vp = 0.0 if e == 0 else round((v / e) * 100.0, 2)
        lines.append(f'| {m} | {e:.6f} | {b:.6f} | {v:.6f} | {vp:.2f}% |')

    if not months:
        lines.append('| (none) | 0.000000 | 0.000000 | 0.000000 | 0.00% |')

    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(OUT), 'months': months}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
