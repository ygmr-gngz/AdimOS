"""Gerçek premium carousel üretip yerel QA kopyalarını indirir."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.content.illustrated_carousel import generate_carousel_pngs


def main() -> None:
    topic = sys.argv[1] if len(sys.argv) > 1 else "Safha Maliyetinde Miktar Hareketleri"
    mode = sys.argv[2] if len(sys.argv) > 2 else "illustrated"
    plan_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    output_dir = Path(__file__).resolve().parents[2] / "tmp" / "carousel-preview-v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    fixed_plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path else None
    plan, urls = generate_carousel_pngs("local-quality-preview-v2", topic, mode, plan=fixed_plan)
    for index, url in enumerate(urls, 1):
        response = httpx.get(url, timeout=60, follow_redirects=True)
        response.raise_for_status()
        (output_dir / f"card-{index:02d}.png").write_bytes(response.content)
    (output_dir / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK: {len(urls)} kart -> {output_dir}")


if __name__ == "__main__":
    main()
