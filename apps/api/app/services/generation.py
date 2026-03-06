from __future__ import annotations

from datetime import datetime, timezone

from app.models.core import Asset
from app.services.model_registry import pick_model_with_policy
from app.services.prompt_layering import build_effective_prompt


def _generate_text(task_tag: str, source_input: str, preference: str = 'balanced') -> tuple[str, dict]:
    model = pick_model_with_policy(capability='text', task_tag=task_tag, preference=preference)
    prompt_pack = build_effective_prompt(task=task_tag, source_input=source_input, workspace_tone='direct')

    base = source_input.strip()[:180]
    if task_tag == 'hook':
        out = f"Stop guessing: {base}"
    elif task_tag == 'script':
        out = f"Problem → pain → solution: {base}"
    elif task_tag == 'social_post':
        out = f"Here’s the simple way to fix this: {base}"
    elif task_tag == 'email':
        out = f"Quick idea for your team: {base}"
    else:
        out = base

    rendered = f"{out}\n\n[model:{model.get('id')}] [provider:{model.get('provider')}]"
    meta = {
        'model': model,
        'prompt_pack': {
            'version': 'v1',
            'task': task_tag,
            'effective_prompt_preview': prompt_pack['effective_prompt'][:220],
        },
    }
    return rendered, meta


def generate_seed_assets(campaign_id: int, source_input: str):
    hook, _ = _generate_text('hook', source_input)
    script, _ = _generate_text('script', source_input, preference='quality')
    post, _ = _generate_text('social_post', source_input, preference='speed')
    email, _ = _generate_text('email', source_input)

    return [
        Asset(campaign_id=campaign_id, asset_type='hook', channel='generic', content=hook, score=7.6, status='draft'),
        Asset(campaign_id=campaign_id, asset_type='script', channel='short-form', content=script, score=7.4, status='draft'),
        Asset(campaign_id=campaign_id, asset_type='post', channel='x', content=post, score=7.8, status='draft'),
        Asset(campaign_id=campaign_id, asset_type='email', channel='email', content=email, score=7.5, status='draft'),
    ]


def regenerate_asset_content(asset: Asset, guidance: str = ''):
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
    task_map = {
        'hook': 'hook',
        'script': 'script',
        'post': 'social_post',
        'email': 'email',
    }
    task_tag = task_map.get(asset.asset_type, 'draft')
    regenerated, _ = _generate_text(task_tag, f"{asset.content}\nGuidance: {guidance}", preference='quality')

    asset.content = f"{asset.asset_type.title()} v2 ({stamp}): {regenerated}"
    asset.score = min(9.5, round(asset.score + 0.25, 2))
    asset.status = 'draft'
    return asset
