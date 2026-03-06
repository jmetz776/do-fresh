#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.model_registry import pick_model_with_policy
from app.services.prompt_layering import build_effective_prompt

ROOT = Path('/Users/jaredmetz/.openclaw/workspace/business/demandorchestrator')
PROMPTS = ROOT / 'quality' / 'benchmark-prompts.json'
OUT = ROOT / 'quality' / 'benchmark-results.json'


def _anti_echo(text: str) -> str:
    banned_starts = (
        'write ',
        'reply to ',
        'explain ',
        'share ',
        'tell ',
        'announce ',
        'create ',
    )
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.lower().startswith(banned_starts):
            continue
        lines.append(ln)
    return '\n'.join(lines).strip()


def generate_stub(task: str, prompt: str, model_id: str) -> str:
    p = prompt.strip()

    if task == 'email':
        body = (
            "Subject: A faster way to publish content that actually converts\n\n"
            "Hey — quick note. Most teams don’t struggle with ideas, they struggle with execution.\n\n"
            "DemandOrchestrator helps you turn one idea into channel-ready drafts, review quickly, publish safely, and see which posts generate real leads.\n\n"
            "If you want, I can send a 5-minute walkthrough and get you early access.\n\n"
            "— Jared"
        )
        return body

    if task == 'hook':
        hooks = [
            "Your content strategy isn’t broken — your workflow is.",
            "If posting feels chaotic, you don’t need more ideas. You need a system.",
            "Most creators lose consistency in execution, not creativity.",
            "Stop scheduling noise. Start shipping content that drives pipeline.",
            "One idea. Multiple channels. Zero fire drills.",
        ]
        return '\n'.join(f"{i+1}) {h}" for i, h in enumerate(hooks))

    if task == 'script':
        script = (
            "[0-3s] Hook: Most creators don’t fail from bad ideas — they fail from messy execution.\n"
            "[4-10s] Problem: Drafting, reviewing, posting, and tracking live in different tools, so consistency dies.\n"
            "[11-22s] Solution: DemandOrchestrator turns one idea into publish-ready content, with approvals and retries built in.\n"
            "[23-30s] CTA: If you want content output without chaos, join early access and I’ll show you the workflow."
        )
        return script

    if task == 'reply':
        return (
            "You don’t need a full team to stay consistent — you need a repeatable workflow. "
            "Batch 3-5 source ideas weekly, turn them into drafts in one session, and schedule with a built-in review step. "
            "That removes daily context switching and keeps output steady."
        )

    # social_post default (X/LinkedIn)
    post = (
        "Most content teams don’t have an idea problem — they have an execution problem.\n\n"
        "When draft, review, publish, and lead tracking are disconnected, output drops and pipeline suffers.\n\n"
        "DemandOrchestrator fixes that loop: one idea in, channel-ready content out, plus clear lead attribution.\n\n"
        "If you want the early-access walkthrough, comment \"DO\" and I’ll send it."
    )
    return _anti_echo(post)


def main() -> int:
    prompts = json.loads(PROMPTS.read_text(encoding='utf-8'))
    rows = []
    for p in prompts:
        chosen = pick_model_with_policy('text', p.get('task', 'social_post'), preference='quality')
        layered = build_effective_prompt(task=p.get('task', 'social_post'), source_input=p.get('prompt', ''), workspace_tone='direct')
        output = generate_stub(p.get('task', 'social_post'), p.get('prompt', ''), chosen.get('id', 'unknown'))
        rows.append({
            'prompt_id': p.get('id'),
            'channel': p.get('channel'),
            'task': p.get('task'),
            'goal': p.get('goal'),
            'model_id': chosen.get('id'),
            'provider': chosen.get('provider'),
            'effective_prompt_preview': layered['effective_prompt'][:220],
            'output': output,
            'scores': {
                'clarity': None,
                'channel_fit': None,
                'hook_strength': None,
                'conversion_intent': None,
                'brand_voice': None,
                'specificity': None,
                'safety_trust': None
            },
            'average': None,
            'keep_or_rewrite': None,
            'rewrite_notes': ''
        })

    OUT.write_text(json.dumps({'items': rows}, indent=2), encoding='utf-8')
    print(json.dumps({'wrote': str(OUT), 'count': len(rows)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
