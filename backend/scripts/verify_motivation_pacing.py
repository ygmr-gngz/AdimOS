#!/usr/bin/env python3
"""Motivasyon pacing kalibrasyonunu gerçek voice_text ile ölçer.

LLM çağrısı yaptığı için canlı OpenAI anahtarı gerektirir. ``narration`` ve
``spoken_text`` asla toplanmaz; üretim pipeline'ıyla aynı seçim sırası kullanılır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.content_constants import TR_SPS, budget_params
from app.modules.content.motivation_generator import (
    _syllable_count,
    _voice_text,
    generate_motivation_storyboard,
)


TOPICS = (
    "Finansal muhasebe netlerin düşük",
    "Deneme netin düştü",
    "Çalışma programın bozuldu",
)


def main() -> None:
    rows: list[dict] = []
    for index, topic in enumerate(TOPICS, 1):
        storyboard = generate_motivation_storyboard(
            topic,
            duration=45,
            job_id=f"pacing-{index}",
        )
        scenes = storyboard.get("scenes", [])
        actual = sum(_syllable_count(_voice_text(scene)) for scene in scenes)
        target, _, _, _ = budget_params(45, len(scenes), "motivasyon")
        per_scene = actual / max(1, len(scenes))
        rows.append({
            "topic": topic,
            "scenes": len(scenes),
            "target_syllables": target,
            "actual_syllables": actual,
            "deviation_pct": round((actual / target - 1) * 100, 1),
            "syllables_per_scene": round(per_scene, 2),
            "natural_scene_seconds": round(per_scene / TR_SPS, 2),
        })
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
