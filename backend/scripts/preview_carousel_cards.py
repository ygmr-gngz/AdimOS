"""Onaylı plandan seçili kartları yeniden üretip yerel QA kopyası indirir."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.content.illustrated_carousel import generate_carousel_card_png


def main() -> None:
    plan_path = Path(sys.argv[1])
    indexes = [int(value) for value in sys.argv[2:]]
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    output_dir = Path(__file__).resolve().parents[2] / "tmp" / "carousel-preview-v3"
    output_dir.mkdir(parents=True, exist_ok=True)
    for index in indexes:
        url = generate_carousel_card_png(
            "local-quality-preview-v3", plan["topic"], plan["cards"][index - 1], index
        )
        response = httpx.get(url, timeout=60, follow_redirects=True)
        response.raise_for_status()
        (output_dir / f"card-{index:02d}.png").write_bytes(response.content)
    print(f"OK: {indexes} -> {output_dir}")


if __name__ == "__main__":
    main()
