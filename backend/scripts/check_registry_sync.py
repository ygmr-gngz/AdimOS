#!/usr/bin/env python3
"""
check_registry_sync.py — remotion/src/registry.ts (Remotion tarafı izinli
sahne adları) ile backend/app/pipelines/registry.py (backend tarafı
allowed_scenes) arasındaki senkronu doğrular.

NEDEN VAR: registry.ts kendi docstring'inde "registry.test.ts bu kayıttaki
adların src/scenes/ dışa aktarımlarıyla birebir eşleşmesini doğrular" diyordu
— ama böyle bir dosya hiç yazılmamıştı (remotion/'da hiçbir test framework'ü
bile kurulu değil). Bu, 2026-08-06'da gerçek bir routing_failed'e yol açtı:
backend/app/pipelines/registry.py'nin educational_reel.allowed_scenes'i
TableScene/CommonMistakeScene/RuleBoxScene eklendikten sonra hiç güncellenmedi
— iki dosya bağımsız, elle tutulan kopyalardı, sync mekanizması yoktu.

İKİ YÖN kontrol edilir:
  A) registry.ts'in izin verdiği her ad, gerçekten src/scenes/ veya
     src/compositions/'da export edilmiş mi? (registry'de var, kodda yok)
  B) backend/app/pipelines/registry.py'nin izin verdiği her ad, aynı
     composition için registry.ts'de de izinli mi? (backend'de var,
     Remotion tarafında yok — TAM OLARAK bugünkü hatanın sınıfı)
     Ters yön (registry.ts izin veriyor ama backend hiç üretmiyor) de
     bilgi amaçlı raporlanır — hata sayılmaz (registry.ts genelde daha
     geniş, örn. LessonVideo altında AccountCardScene gibi henüz hiçbir
     generator'ın üretmediği ama ileride kullanılacak adlar olabilir).

Kullanım:
  python backend/scripts/check_registry_sync.py           # rapor + hata varsa exit 1
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_TS = ROOT / "remotion" / "src" / "registry.ts"
SCENES_DIR = ROOT / "remotion" / "src" / "scenes"
COMPOSITIONS_DIR = ROOT / "remotion" / "src" / "compositions"

sys.path.insert(0, str(ROOT / "backend"))
from app.pipelines.registry import CONTENT_PIPELINES  # noqa: E402


def parse_registry_ts() -> dict[str, dict]:
    """registry.ts'deki SCENE_REGISTRY'yi kaba regex ile ayrıştırır.
    Format sabit ve basit (düz string dizisi) — tam TS parser gerekmez."""
    text = REGISTRY_TS.read_text(encoding="utf-8")
    result: dict[str, dict] = {}
    # Her composition bloğu: "  Key: {\n ... compositionId: "X", ... components: [ ... ],"
    block_re = re.compile(
        r'^\s{2}(\w+):\s*\{.*?compositionId:\s*"([^"]+)".*?components:\s*\[(.*?)\]',
        re.DOTALL | re.MULTILINE,
    )
    for m in block_re.finditer(text):
        key, comp_id, comps_block = m.group(1), m.group(2), m.group(3)
        # '//' yorum satırlarını at — regex TS yorumu anlamıyor, yorumdaki
        # tırnaklı string'leri de gerçek dizi elemanıymış gibi yakalıyordu
        # (örn. "// Gelecekte eklenecek: 'MistakeScene', ...").
        code_only = "\n".join(
            line.split("//", 1)[0] for line in comps_block.splitlines()
        )
        names = re.findall(r'"([^"]+)"', code_only)
        result[key] = {"compositionId": comp_id, "components": names}
    return result


def scan_real_exports() -> set[str]:
    """
    src/scenes/ ve src/compositions/'daki TÜM bileşen tanımlarını toplar —
    üç kalıp: `export function Name`, `export const Name: React.FC` (ok
    fonksiyonu), ve compositions/ dosyaları içinde YEREL (export edilmemiş)
    `function Name` — bazı composition'lar (QuizBoardVideo gibi) alt sahneleri
    kendi dosyaları içinde yerel fonksiyon olarak tanımlayıp bir switch/case
    ile dispatch ediyor, ayrı dosyaya export etmiyor. İlk sürüm yalnızca
    `export function` arıyordu, bu iki kalıbı kaçırıp yanlış pozitif üretti.
    """
    names: set[str] = set()
    exported = re.compile(r"^export (?:function|const) (\w+)", re.MULTILINE)
    local_fn = re.compile(r"^function (\w+)", re.MULTILINE)
    # Saf sanal alias — hiç fonksiyon yok, yalnızca switch/case string'i
    # (örn. EducationalReel120.tsx: case 'ReelHookScene': -> EducationalReelScene
    # segment_type enjekte ederek çağırır, ReelHookScene diye bir fonksiyon YOK).
    case_literal = re.compile(r"case '(\w+)':", re.MULTILINE)
    for f in SCENES_DIR.glob("*.tsx"):
        text = f.read_text(encoding="utf-8")
        names.update(exported.findall(text))
    for f in COMPOSITIONS_DIR.glob("*.tsx"):
        text = f.read_text(encoding="utf-8")
        names.update(exported.findall(text))
        names.update(local_fn.findall(text))     # yerel dispatch hedefleri
        names.update(case_literal.findall(text))  # sanal dispatch alias'ları
    return names


def main() -> int:
    if not REGISTRY_TS.exists():
        print(f"[HATA] {REGISTRY_TS} bulunamadı", file=sys.stderr)
        return 1

    ts_registry = parse_registry_ts()
    real_exports = scan_real_exports()

    errors: list[str] = []
    warnings: list[str] = []

    # ── Yön A: registry.ts'de var, gerçek export yok ─────────────────
    print("=== Yön A: registry.ts adları gerçekten export ediliyor mu? ===\n")
    for key, entry in ts_registry.items():
        missing = [c for c in entry["components"] if c not in real_exports]
        if missing:
            errors.append(f"[{key}] registry.ts izin veriyor ama export YOK: {missing}")
            print(f"  [HATA] {key}: {missing}")
        else:
            print(f"  [OK] {key}: {len(entry['components'])} bileşenin hepsi export ediliyor")

    # ── Yön B: backend allowed_scenes, registry.ts'de karşılığı var mı? ──
    print("\n=== Yön B: backend allowed_scenes <-> registry.ts (composition eşleşmesi) ===\n")
    # backend 'composition' adları bazen registry.ts'deki key'den farklı olabilir
    # (örn. educational_reel -> composition="EducationalReel120" ama registry.ts
    # anahtarı "EducationalReel" — ikisi de aynı Remotion Composition id'sine
    # (EducationalReel120.tsx component'i) karşılık geliyor, registry.ts'in kendi
    # docstring'i de "EducationalReel / EducationalReel120" diyor). Bu yüzden
    # compositionId ÖNEKİ ile eşleştiriyoruz, tam string eşitliği değil.
    for pipeline_key, cfg in CONTENT_PIPELINES.items():
        backend_composition = cfg["composition"]
        ts_entry = None
        for key, entry in ts_registry.items():
            if entry["compositionId"] == backend_composition or backend_composition.startswith(entry["compositionId"]):
                ts_entry = entry
                break
        if ts_entry is None:
            warnings.append(f"[{pipeline_key}] composition={backend_composition!r} registry.ts'de hiç yok — eşleşme atlandı")
            print(f"  [ATLA] {pipeline_key} (composition={backend_composition}): registry.ts'de karşılığı yok")
            continue

        backend_allowed = set(cfg["allowed_scenes"])
        ts_allowed = set(ts_entry["components"])

        backend_only = sorted(backend_allowed - ts_allowed)
        ts_only = sorted(ts_allowed - backend_allowed)

        if backend_only:
            errors.append(
                f"[{pipeline_key}] backend izin veriyor ama registry.ts'de YOK (render'da patlar): {backend_only}"
            )
            print(f"  [HATA] {pipeline_key}: backend-only (registry.ts'de yok) {backend_only}")
        if ts_only:
            print(f"  [BİLGİ] {pipeline_key}: registry.ts-only (backend hiç üretmiyor, zararsız) {ts_only}")
        if not backend_only:
            print(f"  [OK] {pipeline_key}: backend'in izin verdiği her ad registry.ts'de de var")

    print(f"\n=== Sonuç: {len(errors)} hata, {len(warnings)} uyarı ===")
    for e in errors:
        print(f"  HATA: {e}")
    for w in warnings:
        print(f"  UYARI: {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
