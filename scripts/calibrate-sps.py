#!/usr/bin/env python3
"""
calibrate-sps.py — TR_SPS (Türkçe hece/saniye) sabitini gerçek TTS ölçümüyle
kalibre eder.

20 temsili Türkçe cümleyi backend'in kullandığı AYNI OpenAI TTS ayarlarıyla
(app.core.config.settings — model/ses/hız) seslendirir, ffprobe ile gerçek
süresini ölçer, hece sayısını sayar (backend/app/api/routes/video.py'deki
TR_VOWELS ile birebir aynı küme) ve gerçek hece/saniye oranını raporlar.

Tahmin değil ölçüm — shared/content-types.json'daki TR_SPS sabitinin hâlâ
doğru olup olmadığını periyodik olarak doğrulamak için kullanılır.

Gerektirir: OPENAI_API_KEY (gerçek TTS çağrısı yapar, küçük bir maliyeti var).
Kullanım: python scripts/calibrate-sps.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# backend/app/api/routes/video.py:TR_VOWELS ile birebir aynı — tek kaynak
# burada da elle kopyalanmak zorunda kaldı çünkü video.py'yi import etmek
# (Supabase client'ı vb. modül seviyesinde kurduğu için) ağır ve side-effect'li.
TR_VOWELS = frozenset("aeıioöuüAEIİOÖUÜ")

# SGS/mali müşavirlik alanında, çeşitli uzunlukta 20 temsili cümle —
# gerçek üretim promptlarına (educational_reel_storyboard.py few-shot
# örnekleri) yakın üslup ve konu.
SENTENCES = [
    "Özel güvenlik kimlik kartının geçerlilik süresi beş yıldır.",
    "Süresi dolan kartla görev yapmak kanuna aykırıdır.",
    "SGS sınavına girenlerin çoğu bu soruyu yanlış yapıyor.",
    "Kanunun ilgili maddesi net bir süre ve şart tanımlıyor.",
    "Bu süre dolmadan gerekli işlemi yapmazsan yetki belgen geçersiz sayılır.",
    "Örneğin bir aday süresini kaçırdığında yeniden başvuru sürecine girer.",
    "Bu hem zaman hem de ek belge kaybı anlamına gelir, dikkatli olmak gerekir.",
    "Adayların çoğu süre dolsa da görevime devam ederim sanıyor.",
    "Bu tamamen yanlış, geçersiz belgeyle çalışmak kanuna aykırıdır.",
    "Soru kökünde süreyle ilgili bir ifade görürsen önce ilgili maddeyi hatırla.",
    "Sonra şıklardaki sayılara değil kurala odaklanarak cevap ver.",
    "Özetle süreyi takip et, belgeni zamanında yenile.",
    "153 Ticari Mallar hesabını bugün birlikte öğreniyoruz.",
    "Kaydet, sınav sırasında mutlaka lazım olacak.",
    "Bu konu her dönem sınavda karşına çıkıyor ve çoğu aday puan kaybediyor.",
    "Teorik bilgiyle pratik uygulamayı birbirine karıştırdığı için hata yapılıyor.",
    "Mali müşavirlik mesleğinde bilgilendirici ton her zaman önceliklidir.",
    "Danışmanlık sürecinde net ve anlaşılır bir dil kullanmak önemlidir.",
    "Vergi mevzuatındaki değişiklikleri düzenli olarak takip etmek gerekir.",
    "Bir sonraki videoda bu konunun devamını ele alacağız, takipte kal.",
]


def _syllable_count(text: str) -> int:
    return sum(1 for ch in text if ch in TR_VOWELS)


def _ffprobe_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=20,
    )
    return float(result.stdout.strip())


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("HATA: OPENAI_API_KEY ayarlı değil — gerçek TTS çağrısı için gerekli.", file=sys.stderr)
        sys.exit(1)

    from openai import OpenAI
    try:
        from app.core.config import settings
        voice, model, speed = settings.TTS_VOICE_ID, settings.TTS_MODEL, settings.TTS_SPEED
    except Exception as exc:
        print(f"UYARI: backend ayarları okunamadı ({exc}) — varsayılanlar kullanılıyor.", file=sys.stderr)
        voice, model, speed = "nova", "tts-1-hd", 1.0

    client = OpenAI()
    print(f"[calibrate-sps] model={model} voice={voice} speed={speed}")
    print(f"[calibrate-sps] {len(SENTENCES)} cümle seslendirilecek...\n")

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, sentence in enumerate(SENTENCES, 1):
            syl = _syllable_count(sentence)
            resp = client.audio.speech.create(model=model, voice=voice, input=sentence, speed=speed)
            audio_path = os.path.join(tmpdir, f"s{i}.mp3")
            with open(audio_path, "wb") as f:
                f.write(resp.content)
            dur = _ffprobe_duration(audio_path)
            sps = syl / dur if dur > 0 else 0.0
            results.append({"sentence": sentence, "syllables": syl, "duration": dur, "sps": sps})
            print(f"  [{i:2d}/20] hece={syl:3d} süre={dur:5.2f}s sps={sps:.3f}  \"{sentence[:40]}...\"")

    sps_values = [r["sps"] for r in results]
    total_syl = sum(r["syllables"] for r in results)
    total_dur = sum(r["duration"] for r in results)
    aggregate_sps = total_syl / total_dur if total_dur > 0 else 0.0

    print()
    print("=== SONUÇ ===")
    print(f"  ortalama (cümle-bazlı)  : {mean(sps_values):.3f}")
    print(f"  std sapma               : {pstdev(sps_values):.3f}")
    print(f"  min / max               : {min(sps_values):.3f} / {max(sps_values):.3f}")
    print(f"  toplam hece / toplam sn : {total_syl} / {total_dur:.2f}s")
    print(f"  agregat SPS (toplam/toplam) : {aggregate_sps:.3f}")

    try:
        current = None
        import json
        shared_json = ROOT / "shared" / "content-types.json"
        if shared_json.exists():
            current = json.loads(shared_json.read_text(encoding="utf-8")).get("constants", {}).get("TR_SPS")
    except Exception:
        current = None

    print()
    if current is not None:
        drift_pct = abs(aggregate_sps - current) / current * 100
        print(f"  şu anki TR_SPS (shared/content-types.json) : {current}")
        print(f"  sapma: %{drift_pct:.1f}")
        if drift_pct > 10:
            print(
                f"  ÖNERİ: sapma %10'u aşıyor — shared/content-types.json içindeki "
                f"TR_SPS'i {aggregate_sps:.2f}'ye güncelleyip "
                f"backend/scripts/generate_content_constants.py çalıştırmayı düşün."
            )
        else:
            print("  Mevcut TR_SPS makul aralıkta — güncelleme gerekmiyor gibi görünüyor.")
    else:
        print("  (shared/content-types.json okunamadı — karşılaştırma atlandı)")


if __name__ == "__main__":
    main()
