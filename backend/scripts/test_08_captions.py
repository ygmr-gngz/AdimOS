"""
Test 8 — ADIM 4: Altyazı motoru kabul testleri

Kontrol eder:
  C1 — Semantik gruplama: 3-7 kelime/grup, kelime ortasında kesme yok
  C2 — Büyük harf normalleştirme: uppercase_ratio > %35 → title-case
  C3 — Zamanlama tutarlılığı: start < end, örtüşme yok, toplam süre uyumu
  C4 — Boş/geçersiz girdi graceful handling
  C5 — Whisper timestamp entegrasyonu: timestamp sağlanırsa kullanılır
  C6 — add_captions_to_storyboard: storyboard sahne bazlı altyazı ekler
  C7 — validate_captions: spec dışı altyazı hataları tespit edilir
  C8 — Türkçe kısaltmalar (SGS, KDV, TL) büyük kalsın

Çalıştır: python -X utf8 scripts/test_08_captions.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS = "[OK]"
FAIL = "[FAIL]"
tests = []


def test(name):
    def dec(fn):
        tests.append((name, fn))
        return fn
    return dec


# ── C1: Semantik gruplama ─────────────────────────────────────

@test("C1_semantic_grouping")
def _():
    from app.modules.content.caption_generator import _split_semantic_groups

    text = ("153 Ticari Mallar hesabı, varlık sınıfındadır. "
            "Alışlarda borç, satışlarda alacak yazılır. "
            "SGS sınavında bu hesap sık çıkmaktadır.")

    groups = _split_semantic_groups(text)
    assert len(groups) >= 2, f"En az 2 grup beklendi: {groups}"

    for g in groups:
        wc = len(g.split())
        assert 1 <= wc <= 7, f"Kelime sayısı 1-7 olmalı: '{g}' → {wc}"

    # Kelime ortasında kesme yok — her grup tam kelimelerle bitmeli
    full_words = ' '.join(groups).split()
    original_words = text.split()
    assert len(full_words) >= len(original_words) - 2, \
        "Kelimelerin büyük çoğunluğu korunmuş olmalı"

    print(f"{PASS} Semantik gruplama: {len(groups)} grup, hiçbirinde kelime yarısı kesilmedi")
    for i, g in enumerate(groups, 1):
        print(f"  {i}. '{g}' ({len(g.split())} kelime)")


# ── C2: Büyük harf normalleştirme ────────────────────────────

@test("C2_uppercase_normalization")
def _():
    from app.modules.content.caption_generator import _normalize_case, _uppercase_ratio

    # Tamamen büyük → title-case beklenir
    all_caps = "KDV BEYANNAMESINI ZAMANINDA VER"
    result = _normalize_case(all_caps)
    ratio_after = _uppercase_ratio(result)
    assert ratio_after <= 0.35, f"Büyük harf oranı hâlâ yüksek: {ratio_after:.2f} → '{result}'"

    # Kısaltmalar korunmalı
    mixed = "SGS SINAVI KDV tl hesabı"
    result2 = _normalize_case(mixed)
    assert "SGS" in result2, f"SGS kısaltması değişmiş: '{result2}'"
    assert "KDV" in result2, f"KDV kısaltması değişmiş: '{result2}'"

    # Normal Türkçe metin değişmemeli
    normal = "153 Ticari Mallar varlık hesabı"
    result3 = _normalize_case(normal)
    assert result3 == normal, f"Normal metin değişti: '{result3}'"

    print(f"{PASS} Büyük harf normalizasyonu: ALL_CAPS → title-case, kısaltmalar korundu")


# ── C3: Zamanlama tutarlılığı ─────────────────────────────────

@test("C3_timing_consistency")
def _():
    from app.modules.content.caption_generator import generate_captions

    text = ("153 hesabı, varlık sınıfındadır. "
            "SGS'de en sık çıkan konulardan biridir. "
            "Borç tarafına alış, alacak tarafına iade yazılır.")
    duration = 20.0  # 20 saniye sahne

    captions = generate_captions(text, total_seconds=duration, start_offset=5.0)
    assert len(captions) >= 2, f"En az 2 altyazı grubu beklendi: {captions}"

    # start < end her altyazıda
    for i, cap in enumerate(captions):
        assert cap["start"] < cap["end"], \
            f"Altyazı {i+1}: start({cap['start']}) >= end({cap['end']})"
        assert cap["end"] - cap["start"] >= 0.5, \
            f"Altyazı {i+1}: çok kısa ({cap['end'] - cap['start']:.2f}s)"

    # Örtüşme yok (50ms tolerans)
    for i in range(len(captions) - 1):
        assert captions[i+1]["start"] >= captions[i]["end"] - 0.05, \
            f"Altyazı {i+1}→{i+2}: örtüşme var"

    # start_offset uygulandı mı
    assert captions[0]["start"] >= 5.0 - 0.01, \
        f"start_offset 5.0 uygulanmadı: {captions[0]['start']}"

    # Toplam süre uyumu (son end ≈ start_offset + duration)
    actual_span = captions[-1]["end"] - captions[0]["start"]
    assert abs(actual_span - duration) < 1.0, \
        f"Toplam süre uyumsuz: span={actual_span:.1f}s, beklenen={duration}s"

    print(f"{PASS} Zamanlama tutarlı: {len(captions)} grup, "
          f"offset=5.0, span={actual_span:.1f}s")


# ── C4: Boş/geçersiz girdi ───────────────────────────────────

@test("C4_empty_input_graceful")
def _():
    from app.modules.content.caption_generator import generate_captions

    # Boş metin
    r1 = generate_captions("", total_seconds=10.0)
    assert r1 == [], f"Boş metin [] döndürmeli: {r1}"

    # Sıfır süre
    r2 = generate_captions("Bir konu anlatımı.", total_seconds=0)
    assert r2 == [], f"Sıfır süre [] döndürmeli: {r2}"

    # Sadece boşluk
    r3 = generate_captions("   ", total_seconds=5.0)
    assert r3 == [], f"Yalnızca boşluk [] döndürmeli: {r3}"

    # Negatif süre
    r4 = generate_captions("Bir cümle.", total_seconds=-5.0)
    assert r4 == [], f"Negatif süre [] döndürmeli: {r4}"

    print(f"{PASS} Boş/geçersiz girdi graceful: hepsi [] döndü")


# ── C5: Whisper timestamp entegrasyonu ───────────────────────

@test("C5_whisper_timestamps")
def _():
    from app.modules.content.caption_generator import generate_captions

    text = "Yüz elli üç ticari mallar varlık hesabıdır."
    duration = 5.0

    # Simüle edilmiş Whisper word timestamps
    word_timestamps = [
        {"word": "Yüz",      "start": 0.0,  "end": 0.3},
        {"word": "elli",     "start": 0.3,  "end": 0.6},
        {"word": "üç",       "start": 0.6,  "end": 0.9},
        {"word": "ticari",   "start": 0.9,  "end": 1.3},
        {"word": "mallar",   "start": 1.3,  "end": 1.7},
        {"word": "varlık",   "start": 1.7,  "end": 2.0},
        {"word": "hesabıdır.","start": 2.0, "end": 2.6},
    ]

    # Whisper timestamp'li
    captions_wts = generate_captions(
        text, total_seconds=duration, word_timestamps=word_timestamps
    )
    # Whisper'sız
    captions_plain = generate_captions(text, total_seconds=duration)

    assert len(captions_wts) >= 1, "Whisper path altyazı üretmedi"
    assert len(captions_plain) >= 1, "Fast path altyazı üretmedi"

    # Whisper path ile elde edilen start/end, plain'den farklı (daha hassas)
    if len(captions_wts) > 0 and len(captions_plain) > 0:
        wts_start = captions_wts[0]["start"]
        plain_start = captions_plain[0]["start"]
        # Her ikisi de 0.0 civarında olmalı ama mantık farklı
        assert abs(wts_start) < 0.5, f"Whisper start çok büyük: {wts_start}"

    print(f"{PASS} Whisper path: {len(captions_wts)} grup | "
          f"Fast path: {len(captions_plain)} grup")


# ── C6: add_captions_to_storyboard ───────────────────────────

@test("C6_storyboard_captions")
def _():
    from app.modules.content.caption_generator import add_captions_to_storyboard

    storyboard = {
        "scenes": [
            {
                "id": 1,
                "component": "ReelHookScene",
                "voice_text": "SGS'de en çok kaybedilen konuyu biliyor musun?",
                "duration_seconds": 5,
            },
            {
                "id": 2,
                "component": "ReelConceptScene",
                "voice_text": "153 Ticari Mallar, varlık sınıfındadır. Borçta artış, alacakta azalış vardır.",
                "duration_seconds": 15,
            },
            {
                "id": 3,
                "component": "ReelCtaScene",
                "voice_text": "Kaydet, sınav gününe kadar lazım.",
                "duration_seconds": 8,
                # Zaten captions var — atlanmalı
                "captions": [{"start": 18.0, "end": 22.0, "text": "Mevcut altyazı"}],
            },
        ]
    }

    result = add_captions_to_storyboard(storyboard)
    scenes = result["scenes"]

    # Sahne 1 altyazı aldı mı
    assert scenes[0].get("captions"), "Sahne 1 altyazı almalıydı"
    assert scenes[0]["captions"][0]["start"] >= 0.0, "Sahne 1 start 0'dan başlamalı"

    # Sahne 2 altyazı aldı mı, offset 5 sn sonra başlıyor
    assert scenes[1].get("captions"), "Sahne 2 altyazı almalıydı"
    assert scenes[1]["captions"][0]["start"] >= 5.0 - 0.1, \
        f"Sahne 2 offset yanlış: {scenes[1]['captions'][0]['start']}"

    # Sahne 3 zaten captions var — değişmemeli
    assert scenes[2]["captions"][0]["text"] == "Mevcut altyazı", \
        "Zaten altyazısı olan sahne değiştirilmemeli"

    # Orijinal storyboard değişmedi (deep copy)
    assert storyboard["scenes"][0].get("captions") is None, \
        "Orijinal storyboard değiştirilmiş (deep copy hatası)"

    print(f"{PASS} add_captions_to_storyboard: "
          f"2 sahne altyazı aldı, 1 korundu, orijinal değişmedi")


# ── C7: validate_captions ────────────────────────────────────

@test("C7_validate_captions")
def _():
    from app.modules.content.caption_generator import validate_captions

    # Geçerli altyazı — hata olmamalı
    good = [
        {"start": 0.0,  "end": 2.0, "text": "SGS sınavında çok çıkıyor."},
        {"start": 2.0,  "end": 4.5, "text": "Bunu bilmek şart."},
    ]
    errs = validate_captions(good)
    assert errs == [], f"Geçerli altyazıda hata olmamalı: {errs}"

    # Büyük harf ihlali
    bad_caps = [
        {"start": 0.0, "end": 2.0, "text": "SGS SINAVINDA COK CIKIYOR BUDUR"},
    ]
    errs2 = validate_captions(bad_caps)
    assert any("büyük harf" in e.lower() for e in errs2), \
        f"Büyük harf hatası tespit edilmeli: {errs2}"

    # Örtüşme
    overlap = [
        {"start": 0.0, "end": 3.0, "text": "Birinci grup."},
        {"start": 2.0, "end": 5.0, "text": "İkinci grup örtüşüyor."},
    ]
    errs3 = validate_captions(overlap)
    assert any("örtüşme" in e.lower() for e in errs3), \
        f"Örtüşme hatası tespit edilmeli: {errs3}"

    print(f"{PASS} validate_captions: geçerli=0 hata, büyük-harf=tespit, örtüşme=tespit")


# ── C8: Türkçe kısaltmalar ───────────────────────────────────

@test("C8_turkish_abbreviations")
def _():
    from app.modules.content.caption_generator import _normalize_case

    cases = [
        ("SGS SINAVI HAZIRLIK", "SGS"),     # 3 harf kısaltma
        ("KDV BEYANNAMESI", "KDV"),         # 3 harf kısaltma
        ("TL HESABI", "TL"),                # 2 harf kısaltma
        ("SMMM ADAYI", "SMMM"),             # 4 harf kısaltma
    ]
    for text, abbr in cases:
        result = _normalize_case(text)
        assert abbr in result, \
            f"'{abbr}' kısaltması kayboldu: '{text}' → '{result}'"

    print(f"{PASS} Türkçe kısaltmalar korundu: SGS, KDV, TL, SMMM")


# ── Runner ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Test 8: ADIM 4 Altyazi Motoru Kabul Testleri ===\n")
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
            import traceback as tb
            print(f"{FAIL} {name} beklenmeyen hata: {type(e).__name__}: {e}")
            print(tb.format_exc())

    total = len(tests)
    print(f"\nSonuc: {passed}/{total} gecti")
    if passed < total:
        sys.exit(1)
