"""
Test 9 — ADIM 6+7: İçerik bankası + visual library kabul testleri

Kontrol eder:
  B1 — Motivasyon konu bankası: ogrenci/danisan, deterministik seçim
  B2 — Hook formula bankası: track filtresi, yasak açılış engeli
  B3 — CTA bankası: tek eylem, track'e göre seçim
  B4 — Hook compliance: yasak açılışlar reddedilir
  B5 — Visual library manifest: tema dizinleri ve json geçerli
  B6 — Theme for scene: component'e göre tema tahmini
  B7 — Deterministik seçim: aynı job_id → aynı içerik

Çalıştır: python -X utf8 scripts/test_09_content_bank.py
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


@test("B1_motivation_topic_bank")
def _():
    from app.modules.content.content_bank import (
        pick_motivation_topic, MOTIVATION_TOPICS_OGRENCI, DANISAN_TOPICS
    )

    assert len(MOTIVATION_TOPICS_OGRENCI) >= 8, \
        f"Ogrenci banka en az 8 konu olmalı: {len(MOTIVATION_TOPICS_OGRENCI)}"
    assert len(DANISAN_TOPICS) >= 5, \
        f"Danisan banka en az 5 konu olmalı: {len(DANISAN_TOPICS)}"

    t_ogr = pick_motivation_topic("job-001", "ogrenci")
    t_dan = pick_motivation_topic("job-001", "danisan")

    assert t_ogr is not None and t_ogr.content_track == "ogrenci"
    assert t_dan is not None and t_dan.content_track == "danisan"
    assert t_ogr.id != t_dan.id, "Farklı track'ler aynı konuyu vermemeli"

    print(f"{PASS} Konu bankası: {len(MOTIVATION_TOPICS_OGRENCI)} ogrenci, "
          f"{len(DANISAN_TOPICS)} danisan")
    print(f"  ogrenci seçim: {t_ogr.id} — {t_ogr.topic[:40]}")
    print(f"  danisan seçim: {t_dan.id} — {t_dan.topic[:40]}")


@test("B2_hook_formula_bank")
def _():
    from app.modules.content.content_bank import pick_hook_formula, HOOK_FORMULAS

    assert len(HOOK_FORMULAS) >= 6, f"En az 6 hook formülü olmalı: {len(HOOK_FORMULAS)}"

    h_ogr = pick_hook_formula("job-002", "ogrenci")
    h_dan = pick_hook_formula("job-002", "danisan")

    assert h_ogr is not None
    assert h_dan is not None
    assert h_ogr.content_track in ("ogrenci", "her_ikisi")
    assert h_dan.content_track in ("danisan", "her_ikisi")

    # Hook şablonu belirtilmiş
    assert h_ogr.example, "Hook example boş olmamalı"
    assert len(h_ogr.example.split()) <= 14, \
        f"Hook örneği 14 kelimeden uzun: {h_ogr.example}"

    print(f"{PASS} Hook bankası: {len(HOOK_FORMULAS)} formül")
    print(f"  ogrenci: [{h_ogr.formula_type}] {h_ogr.example[:60]}")
    print(f"  danisan: [{h_dan.formula_type}] {h_dan.example[:60]}")


@test("B3_cta_bank")
def _():
    from app.modules.content.content_bank import pick_cta, CTA_BANK

    assert len(CTA_BANK) >= 4, f"En az 4 CTA olmalı: {len(CTA_BANK)}"

    c_ogr = pick_cta("job-003", "ogrenci")
    c_dan = pick_cta("job-003", "danisan")

    assert c_ogr is not None and c_ogr.content_track == "ogrenci"
    assert c_dan is not None and c_dan.content_track == "danisan"
    assert c_ogr.primary, "CTA primary boş olmamalı"
    assert c_ogr.pinned_comment, "CTA pinned_comment boş olmamalı"

    # Tek eylem kuralı: 've [fiil]' içermemeli
    primary = c_ogr.primary.lower()
    risky_conjunctions = [" ve takip", " ve yorum", " ve beğen"]
    for conj in risky_conjunctions:
        assert conj not in primary, \
            f"CTA iki eylem içeriyor: '{c_ogr.primary}'"

    print(f"{PASS} CTA bankası: {len(CTA_BANK)} giriş")
    print(f"  ogrenci: '{c_ogr.primary}'")
    print(f"  danisan: '{c_dan.primary}'")


@test("B4_hook_compliance")
def _():
    from app.modules.content.content_bank import check_hook_compliance

    # Yasak açılışlar
    bad_hooks = [
        "Merhaba arkadaşlar, bugün 153 hesabını anlatacağım.",
        "Herkese merhaba, SGS sınavı için önemli bir konu.",
        "İyi günler arkadaşlar.",
        "Bu videoda KDV'yi anlatacağım.",
    ]
    for bh in bad_hooks:
        errs = check_hook_compliance(bh)
        assert len(errs) > 0, f"Yasak hook geçmemeli: '{bh}'"

    # Geçerli hooklar
    good_hooks = [
        "Üç gündür kitabı açmadın, biliyorum.",
        "SGS'de en çok kaybedilen 8 net, hep aynı yerden gider.",
        "e-Fatura'ya geçmezseniz bu cezayı yiyebilirsiniz.",
    ]
    for gh in good_hooks:
        errs = check_hook_compliance(gh)
        assert len(errs) == 0, f"Geçerli hook reddedildi: '{gh}' → {errs}"

    print(f"{PASS} Hook compliance: {len(bad_hooks)} yasak engellendi, "
          f"{len(good_hooks)} geçerli kabul edildi")


@test("B5_visual_library_manifest")
def _():
    import json, pathlib
    manifest_path = pathlib.Path(__file__).parents[2] / "assets" / "library" / "manifest.json"

    assert manifest_path.exists(), f"manifest.json bulunamadı: {manifest_path}"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    themes = manifest.get("themes", {})

    assert len(themes) >= 8, f"En az 8 tema olmalı: {len(themes)}"

    # Zorunlu alanlar
    required_fields = {"dir", "label", "content_tracks", "target_variants",
                       "tags", "subject_prompt"}
    for theme_key, cfg in themes.items():
        missing = required_fields - set(cfg.keys())
        assert not missing, f"Tema '{theme_key}' eksik alanlar: {missing}"
        assert cfg["target_variants"] >= 10, \
            f"Tema '{theme_key}' hedef varyant çok düşük: {cfg['target_variants']}"
        assert len(cfg["tags"]) >= 3, \
            f"Tema '{theme_key}' en az 3 tag olmalı"

    # Danisan temaları var mı
    danisan_themes = [k for k, v in themes.items()
                      if "danisan" in v.get("content_tracks", [])]
    assert len(danisan_themes) >= 2, \
        f"En az 2 danisan teması olmalı: {danisan_themes}"

    # Style contract
    sc = manifest.get("style_contract", {})
    assert sc.get("positive"), "style_contract.positive boş"
    assert sc.get("negative"), "style_contract.negative boş"
    assert "no text" in sc.get("positive", "").lower() or \
           "no text" in sc.get("negative", "").lower(), \
        "Style contract görsel-metin yasağı içermeli"

    print(f"{PASS} Manifest geçerli: {len(themes)} tema, "
          f"{len(danisan_themes)} danisan, style_contract OK")


@test("B6_theme_for_scene")
def _():
    from app.modules.content.visual_library import theme_for_scene

    # text_only sahne → None (görsel gerekmez)
    hook_scene = {"component": "ReelHookScene", "visual_source": "text_only"}
    assert theme_for_scene(hook_scene) is None, \
        "text_only sahne görsel istemeli değil"

    # Motivasyon sahnesi → ogrenci'de calisma_masasi veya benzeri
    mot_scene = {"component": "MotivationHookScene", "segment_type": "hook"}
    t = theme_for_scene(mot_scene, content_track="ogrenci")
    assert t is not None, "Motivasyon sahnesi tema almalı"
    assert t in (
        "calisma_masasi", "ogrenci_calisir", "yeniden_baslama", "sabah_isik",
        "mola", "kitap_defter", "takvim_plan", "ilerleme", "ofis_muhasebe"
    ), f"Geçersiz tema: {t}"

    # Danişan motivasyon → ofis_muhasebe
    mot_dan = {"component": "MotivationHookScene", "segment_type": "hook"}
    td = theme_for_scene(mot_dan, content_track="danisan")
    assert td == "ofis_muhasebe", f"Danisan için ofis_muhasebe beklendi: {td}"

    # LLM visual_theme alanı varsa öncelikli kullanılır
    scene_with_theme = {"component": "MotivationStepScene",
                        "visual_theme": "ilerleme"}
    assert theme_for_scene(scene_with_theme) == "ilerleme", \
        "LLM visual_theme alanı öncelikli olmalı"

    print(f"{PASS} theme_for_scene: text_only→None, motivasyon→{t}, danisan→{td}, LLM→ilerleme")


@test("B7_deterministic_selection")
def _():
    from app.modules.content.content_bank import (
        pick_motivation_topic, pick_hook_formula, pick_cta
    )

    job_id = "test-job-determinism-xyz"

    # Aynı job_id → aynı seçim
    t1 = pick_motivation_topic(job_id, "ogrenci")
    t2 = pick_motivation_topic(job_id, "ogrenci")
    assert t1.id == t2.id, f"Deterministik değil: {t1.id} vs {t2.id}"

    h1 = pick_hook_formula(job_id, "ogrenci")
    h2 = pick_hook_formula(job_id, "ogrenci")
    assert h1.id == h2.id, f"Hook deterministik değil: {h1.id} vs {h2.id}"

    c1 = pick_cta(job_id, "ogrenci")
    c2 = pick_cta(job_id, "ogrenci")
    assert c1.id == c2.id, f"CTA deterministik değil: {c1.id} vs {c2.id}"

    # Farklı job_id farklı seçim yapabilir (zorunlu değil, ama beklenen)
    t_other = pick_motivation_topic("completely-different-job-id", "ogrenci")
    # Aynı çıkarsa sorun değil (hash çakışması), ama genellikle farklı
    print(f"{PASS} Deterministik seçim: topic={t1.id}, hook={h1.id}, cta={c1.id}")


# ── Runner ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Test 9: Icerik Bankasi + Visual Library Kabul Testleri ===\n")
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
            print(f"{FAIL} {name}: {type(e).__name__}: {e}")
            print(tb.format_exc())

    total = len(tests)
    print(f"\nSonuc: {passed}/{total} gecti")
    if passed < total:
        sys.exit(1)
