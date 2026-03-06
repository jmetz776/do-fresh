from __future__ import annotations

from typing import Dict


SYSTEM_LAYER = (
    "You are a high-quality content generation engine. "
    "Be clear, concise, and conversion-oriented. Avoid fluff."
)

PRODUCT_LAYER = (
    "Output must be channel-ready and practical. "
    "Prioritize readability, scannability, and strong hooks."
)


def build_effective_prompt(task: str, source_input: str, workspace_tone: str = 'direct') -> Dict[str, str]:
    task_layer = f"Task: {task}. Create polished output from this source: {source_input.strip()[:400]}"
    workspace_layer = f"Workspace tone: {workspace_tone}. Keep language simple and human."

    composed = "\n\n".join([
        f"[SYSTEM]\n{SYSTEM_LAYER}",
        f"[PRODUCT]\n{PRODUCT_LAYER}",
        f"[WORKSPACE]\n{workspace_layer}",
        f"[TASK]\n{task_layer}",
    ])

    return {
        'system': SYSTEM_LAYER,
        'product': PRODUCT_LAYER,
        'workspace': workspace_layer,
        'task': task_layer,
        'effective_prompt': composed,
    }
