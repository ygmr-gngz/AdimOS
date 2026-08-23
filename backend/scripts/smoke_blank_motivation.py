"""Boş konu -> banka fallback -> gerçek storyboard smoke testi."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.video import _resolve_motivation_topic
from app.modules.content.motivation_generator import generate_motivation_storyboard


def main() -> None:
    title, prompt_topic = _resolve_motivation_topic("   ")
    result = generate_motivation_storyboard(
        topic=prompt_topic,
        duration=45,
        platform="reels",
        job_id="blank-motivation-smoke",
    )
    scenes = []
    for index, raw in enumerate(result.get("scenes") or [], 1):
        scene = dict(raw)
        scene["id"] = index
        scene["duration_seconds"] = 4
        scene["voice_text"] = scene.get("narration") or scene.get("message") or ""
        scenes.append(scene)
    if not scenes:
        raise RuntimeError("blank_motivation_smoke_failed: sahne üretilmedi")
    storyboard = {
        "video_type": "motivasyon",
        "title": title,
        "format": "9:16",
        "language": "tr",
        "brand": {
            "primary_color": "#0B2A4A",
            "secondary_color": "#F28C28",
            "background_color": "#FFFEFB",
            "font_heading": "Noto Sans",
            "font_body": "Noto Sans",
            "handle": "@adimmusavir",
        },
        "scenes": scenes,
    }
    output = Path(__file__).resolve().parents[2] / "tmp" / "blank-motivation-props.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"storyboard": storyboard}, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"topic": title, "scene_count": len(scenes), "props": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
