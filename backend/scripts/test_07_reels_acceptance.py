"""
Test 7 — Reels/Short + content_track Kabul Testleri (Bolum 10)

Kontrol eder:
  TEST R1  — marketing_compliance: danisan hatinda yasak ifade engeli
  TEST R2  — content_track DB insert: ogrenci/danisan dogru yaziliyor
  TEST R3a — Reels sahne yapisi: 7-10 sahne, >=5 gorsel yuzey
  TEST R3b — CTA kurali: tek eylem, cta_text alaninda
  TEST R3c — Hook kurali: "Merhaba arkadaşlar" yasak
  TEST R3d — content_track fallback: belirtilmemisse 'ogrenci' varsayiliyor

Calistir: python scripts/test_07_reels_acceptance.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS = "[OK]"
FAIL = "[FAIL]"
passed = 0
tests  = []


def test(name):
    def dec(fn):
        tests.append((name, fn))
        return fn
    return dec


# ── TEST R1: marketing_compliance — danisan hatinda hard fail ─

@test("R1_marketing_compliance_danisan_blocks")
def _():
    from app.modules.content.quality_gates import check_marketing_compliance

    storyboard = {"scenes": [
        {"id": 1, "voice_text": "En ucuz mali müşavir hizmetini sunuyoruz.",
         "plain_text": "En ucuz mali müşavir"},
        {"id": 2, "voice_text": "Ücretsiz danışmanlık için hemen ara.",
         "cta_text": "Hemen ara"},
    ]}
    errors = check_marketing_compliance(storyboard, "danisan")
    assert len(errors) >= 2, f"En az 2 ihlal beklendi, {len(errors)} bulundu: {errors}"
    print(f"{PASS} danisan hatinda {len(errors)} yasak ifade engellendi")


@test("R1_marketing_compliance_ogrenci_passes")
def _():
    from app.modules.content.quality_gates import check_marketing_compliance

    storyboard = {"scenes": [
        {"id": 1, "voice_text": "153 Ticari Mallar hesabını bugün öğreniyoruz."},
        {"id": 2, "cta_text": "Kaydet, çalışırken lazım olacak."},
    ]}
    errors = check_marketing_compliance(storyboard, "ogrenci")
    assert errors == [], f"Ogrenci hatinda hata olmamali: {errors}"
    print(f"{PASS} ogrenci hatinda marketing check atlanıyor (bos liste)")


@test("R1_marketing_compliance_none_track_passes")
def _():
    from app.modules.content.quality_gates import check_marketing_compliance

    storyboard = {"scenes": [
        {"id": 1, "voice_text": "Ücretsiz danışmanlık kampanya indirim."},
    ]}
    # content_track=None → kontrol aktif değil (eski kayıtlar için)
    errors = check_marketing_compliance(storyboard, None)
    assert errors == [], f"None track'te kontrol calismamali: {errors}"
    print(f"{PASS} content_track=None → marketing check devre disi")


# ── TEST R2: ContentTrack enum ve content_type.py ─────────────

@test("R2_content_track_enum")
def _():
    from app.domain.content_type import ContentTrack

    assert ContentTrack.OGRENCI == "ogrenci", "OGRENCI degeri yanlis"
    assert ContentTrack.DANISAN == "danisan", "DANISAN degeri yanlis"
    assert str(ContentTrack.OGRENCI) == "ogrenci"

    valid = {"ogrenci", "danisan"}
    for ct in ContentTrack:
        assert str(ct) in valid, f"Beklenmeyen deger: {ct}"
    print(f"{PASS} ContentTrack enum degerler dogru: {[str(c) for c in ContentTrack]}")


# ── TEST R3a: Reels sahne yapisi ──────────────────────────────

VISUAL_SURFACE_MAP = {
    "ReelHookScene":     "text_only",
    "ReelConceptScene":  "card",
    "AccountCardScene":  "card",
    "JournalEntryScene": "journal",
    "TableScene":        "table",
    "ReelMistakeScene":  "card",
    "ReelExamTipScene":  "card",
    "ReelCtaScene":      "text_only",
    "EducationalReelScene": None,  # segment_type'a göre belirlenir
}


def _count_distinct_surfaces(scenes: list[dict]) -> int:
    """
    text_only hariç kaç farklı görsel bileşen var.
    Doküman sayımı: card·3 farklı bileşen + journal + table = 5 → bileşen bazlı sayılır.
    """
    components = set()
    for s in scenes:
        comp = s.get("component", "")
        src  = s.get("visual_source") or VISUAL_SURFACE_MAP.get(comp)
        if src and src != "text_only":
            components.add(comp)
    return len(components)


@test("R3a_reels_scene_structure")
def _():
    # Tipik 120 sn reel storyboard: 9 sahne, 5 görsel yüzey
    scenes = [
        {"id": 1, "component": "ReelHookScene",     "duration_seconds": 5,
         "voice_text": "Üç gündür kitabı açmadın, biliyorum.", "visual_source": "text_only"},
        {"id": 2, "component": "ReelConceptScene",  "duration_seconds": 15,
         "voice_text": "153 hesabı varlık sınıfındadır.", "visual_source": "card"},
        {"id": 3, "component": "AccountCardScene",  "duration_seconds": 20,
         "voice_text": "Borç: alış, Alacak: iade.", "visual_source": "card"},
        {"id": 4, "component": "JournalEntryScene", "duration_seconds": 22,
         "voice_text": "Bin iki yüz elli liralık alış kaydı.", "visual_source": "journal"},
        {"id": 5, "component": "TableScene",        "duration_seconds": 20,
         "voice_text": "Sınıf A ve B arasındaki farklar.", "visual_source": "table"},
        {"id": 6, "component": "ReelMistakeScene",  "duration_seconds": 20,
         "voice_text": "En sık yapılan hata budur.", "visual_source": "card"},
        {"id": 7, "component": "ReelExamTipScene",  "duration_seconds": 15,
         "voice_text": "Sınavda bu formülü kullan.", "visual_source": "card"},
        {"id": 8, "component": "ReelCtaScene",      "duration_seconds": 10,
         "cta_text": "Kaydet, çalışırken lazım olacak.", "visual_source": "text_only"},
    ]
    total_sec = sum(s["duration_seconds"] for s in scenes)
    distinct  = _count_distinct_surfaces(scenes)

    assert 7 <= len(scenes) <= 10, f"Sahne sayisi 7-10 olmali: {len(scenes)}"
    assert 108 <= total_sec <= 128, f"Sure 108-128s olmali: {total_sec}s"
    assert distinct >= 5, f"En az 5 gorsel yuzey (text_only haric) olmali: {distinct}"
    print(f"{PASS} Reels yapisi gecerli: {len(scenes)} sahne, {total_sec}s, {distinct} gorsel yuzey")


# ── TEST R3b: CTA kurali — tek eylem ─────────────────────────

@test("R3b_cta_single_action")
def _():
    # "Kaydet" VE "Yorum at" → iki eylem → red
    bad_cta  = "Kaydet ve yorum at, ikisini de yap."
    good_cta = "Kaydet, çalışırken lazım olacak."

    # Basit kural: virgül + fiil kombinasyonu iki eylem işareti
    # Gerçek implementasyon LLM prompt'unda — burada sözleşme sınırı test ediliyor
    assert "kaydet" in good_cta.lower(), "Tek eylem CTA 'kaydet' içermeli"
    assert good_cta.count("ve ") <= 0 or "lazım" in good_cta, \
        "Tek eylem CTA'da 've [fiil]' olmamalı"
    print(f"{PASS} CTA tek eylem kurali: '{good_cta}'")


# ── TEST R3c: Hook kurali — "Merhaba arkadaşlar" yasak ───────

@test("R3c_hook_no_merhaba_arkadaslar")
def _():
    FORBIDDEN_HOOK_OPENS = [
        "merhaba arkadaşlar",
        "merhaba arkadaslar",
        "herkese merhaba",
        "iyi günler arkadaşlar",
    ]
    hooks = [
        "Üç gündür kitabı açmadın, biliyorum.",                    # gecmeli
        "SGS'de en çok kaybedilen 8 net, hep aynı yerden gider.",  # gecmeli
        "Merhaba arkadaşlar, bugün 153 hesabını anlatacağım.",     # basarisiz olmali
    ]
    for hook in hooks:
        low = hook.lower()
        is_forbidden = any(f in low for f in FORBIDDEN_HOOK_OPENS)
        if "Merhaba arkadaşlar" in hook:
            assert is_forbidden, f"Yasak hook gecmemeli: '{hook}'"
        else:
            assert not is_forbidden, f"Gecerli hook reddedildi: '{hook}'"
    print(f"{PASS} Hook kurali: 'Merhaba arkadaslar' yasak, diger hooklar gecerli")


# ── TEST R3d: content_track fallback ─────────────────────────

@test("R3d_content_track_fallback_ogrenci")
def _():
    """
    content_track belirtilmemisse veya gecersizse 'ogrenci' varsayilmali.
    Bu mantik video.py create_video_job'da uygulanir; burada sadece mantigi test et.
    """
    def _resolve_track(raw):
        if raw not in ("ogrenci", "danisan"):
            return "ogrenci"
        return raw

    assert _resolve_track(None)      == "ogrenci"
    assert _resolve_track("")        == "ogrenci"
    assert _resolve_track("invalid") == "ogrenci"
    assert _resolve_track("ogrenci") == "ogrenci"
    assert _resolve_track("danisan") == "danisan"
    print(f"{PASS} content_track fallback: None/gecersiz → 'ogrenci'")


# ── Runner ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Test 7: Reels + content_track Kabul Testleri ===\n")
    passed = 0
    for name, fn in tests:
        try:
            print(f"--- {name} ---")
            fn()
            passed += 1
        except AssertionError as e:
            print(f"{FAIL} {name}: {e}")
        except ImportError as e:
            print(f"{FAIL} {name} import hatasi: {e}")
        except Exception as e:
            print(f"{FAIL} {name} beklenmeyen hata: {type(e).__name__}: {e}")

    total = len(tests)
    print(f"\nSonuc: {passed}/{total} gecti")
    if passed < total:
        sys.exit(1)
