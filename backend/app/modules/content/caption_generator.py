"""
Altyazı üretici — ses+metin → zamanlı altyazı grupları.

ADIM 4: Subtitle engine
Spec: BÖLÜM 5 (ÖNCELİK HATTI PROMPT'U v3 + v4 §17)
  - Anlam grubu bazlı, 3-7 kelime, maks. 2 satır
  - Tümü büyük harf yasak (uppercase_ratio ≤ %35)
  - Harf harf karaoke (word-level timing) yasak
  - Ses-altyazı farkı ≤ 150 ms
  - Kelime ortasında kaybolma yasak

İki zamanlama modu:
  1. fast_path:     kelime sayısı oranı — TTS süresi olmadan da çalışır
  2. whisper_path:  Whisper word timestamps — ≤ 150 ms hassasiyet için
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Türkçe konuşma hızı tahmini (0.98 hızda)
_TR_WORDS_PER_SECOND = 2.6
_MIN_GROUP_WORDS = 3
_MAX_GROUP_WORDS = 7
_MAX_CAPTION_CHARS = 38   # satır başına max karakter (2 satır × 19)
_UPPERCASE_RATIO_LIMIT = 0.35

# Whisper'ın SGS/mali müşavirlik alanı kısaltmalarını tanımasını artırmak için
# "prompt" parametresi — Whisper bunu sesli olarak duymaz, yalnızca kelime
# dağarcığı ipucu olarak kullanır (OpenAI docs). Bu olmadan "KDV" gibi kısa
# kısaltmalar "Kadeh"/"Kade ve" gibi alakasız kelimelere transkript ediliyordu
# — bu da _timing_from_whisper'ın eşleşme bulamayıp her sahnede fast path'e
# düşmesine yol açıyordu.
_WHISPER_DOMAIN_PROMPT = (
    "KDV, SGK, SMMM, SGS, TTK, VUK, yevmiye, amortisman, mizan, bilanço, "
    "tahakkuk, beyanname"
)


@dataclass
class CaptionEntry:
    start: float   # saniye
    end: float     # saniye
    text: str


def _uppercase_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def _normalize_case(text: str) -> str:
    """
    Büyük harf oranı %35'i aşıyorsa title-case'e çevirir.
    Türkçe büyük harf uyumunu korur (İ→i yerine str.lower kullanılmaz).
    """
    if _uppercase_ratio(text) > _UPPERCASE_RATIO_LIMIT:
        # Python str.title() İngilizce uyumlu; Türkçe için kelime bazlı ilk harf büyütme
        words = text.split()
        result = []
        for w in words:
            if len(w) > 0:
                # Tüm büyük kısaltmaları (SGS, KDV, TL) koru
                if w.isupper() and len(w) <= 4:
                    result.append(w)
                else:
                    result.append(w[0].upper() + w[1:].lower())
            else:
                result.append(w)
        return ' '.join(result)
    return text


def _split_semantic_groups(text: str) -> list[str]:
    """
    Metni noktalama işaretlerini anlam sınırı olarak kullanarak
    3-7 kelimelik gruplara böler.
    Kelime ortasında kesme yasak.
    """
    # Satır sonları ve çok boşlukları temizle
    text = re.sub(r'\s+', ' ', text.strip())

    # Noktalama sınırlarında doğal bölme noktaları tespit et
    # , ; — ' ile biten kelimelerden sonra yeni grup başlar
    tokens: list[tuple[str, bool]] = []   # (kelime, noktalama_sonrası_mı)
    for token in re.split(r'(\s+)', text):
        token = token.strip()
        if not token:
            continue
        is_boundary = bool(re.search(r'[,;—.!?–—]$', token))
        tokens.append((token, is_boundary))

    groups: list[str] = []
    current: list[str] = []

    for word, is_boundary in tokens:
        current.append(word)
        word_count = len(current)

        # Zorunlu bölme: max kelime sayısına ulaştık
        if word_count >= _MAX_GROUP_WORDS:
            groups.append(' '.join(current))
            current = []
            continue

        # Doğal bölme: noktalama sınırı + min kelime sayısı karşılandı
        if is_boundary and word_count >= _MIN_GROUP_WORDS:
            groups.append(' '.join(current))
            current = []

    # Kalan kelimeleri ekle
    if current:
        # Son grup çok kısaysa öncekiyle birleştir
        if len(current) < _MIN_GROUP_WORDS and groups:
            last = groups.pop()
            merged = last + ' ' + ' '.join(current)
            # Yeniden böl — hâlâ çok uzunsa zorla böl
            merged_words = merged.split()
            if len(merged_words) > _MAX_GROUP_WORDS:
                groups.append(' '.join(merged_words[:_MAX_GROUP_WORDS]))
                groups.append(' '.join(merged_words[_MAX_GROUP_WORDS:]))
            else:
                groups.append(merged)
        else:
            groups.append(' '.join(current))

    return [g for g in groups if g.strip()]


def _timing_from_wordcount(
    groups: list[str],
    total_seconds: float,
    start_offset: float = 0.0,
) -> list[CaptionEntry]:
    """
    Kelime sayısı oranıyla zamanlama üretir.
    Hassasiyet: ±200-400 ms (fast path).
    """
    total_words = sum(len(g.split()) for g in groups)
    if total_words == 0 or total_seconds <= 0:
        return []

    entries: list[CaptionEntry] = []
    cursor = start_offset
    for group in groups:
        word_count = len(group.split())
        duration = total_seconds * (word_count / total_words)
        entries.append(CaptionEntry(
            start=cursor,
            end=cursor + duration,
            text=_normalize_case(group),
        ))
        cursor += duration

    return entries


def _timing_from_whisper(
    groups: list[str],
    word_timestamps: list[dict],
    start_offset: float = 0.0,
) -> tuple[list[CaptionEntry], dict]:
    """
    Whisper word-level timestamp'leriyle hassas zamanlama.
    word_timestamps: [{"word": str, "start": float, "end": float}, ...]
    Hassasiyet: ≤ 150 ms (Whisper + tolerans).

    Döner: (entries, match_stats) — match_stats başarısızlık nedenini
    teşhis etmek için (kaç grup/kelime eşleşti, Whisper kaç kelime döndürdü).
    Önceden bu bilgi hiç loglanmıyordu ("eşleştirme başarısız" tek başına
    neden olduğunu göstermiyordu) — sessiz fallback sınırındaydı.
    """
    stats = {
        "groups_total": len(groups),
        "groups_matched": 0,
        "words_total": sum(len(g.split()) for g in groups),
        "words_matched": 0,
        "whisper_words_total": len(word_timestamps),
    }
    if not word_timestamps:
        stats["reason"] = "word_timestamps_empty"
        return [], stats

    # Kelime dizisini oluştur
    wt_idx = 0
    entries: list[CaptionEntry] = []

    for group in groups:
        words_in_group = group.split()
        group_start: Optional[float] = None
        group_end: Optional[float] = None

        for gword in words_in_group:
            # Whisper'ın ürettiği kelimeyle kaba eşleştirme (noktalama temizlenerek)
            gword_clean = re.sub(r'[^\w]', '', gword.lower())
            matched = False
            while wt_idx < len(word_timestamps):
                wt_word = re.sub(r'[^\w]', '', word_timestamps[wt_idx]['word'].lower())
                if wt_word == gword_clean or gword_clean in wt_word or wt_word in gword_clean:
                    if group_start is None:
                        group_start = word_timestamps[wt_idx]['start'] + start_offset
                    group_end = word_timestamps[wt_idx]['end'] + start_offset
                    wt_idx += 1
                    matched = True
                    break
                wt_idx += 1
            if matched:
                stats["words_matched"] += 1

        if group_start is not None and group_end is not None:
            entries.append(CaptionEntry(
                start=group_start,
                end=group_end,
                text=_normalize_case(group),
            ))
            stats["groups_matched"] += 1

    if not entries:
        stats["reason"] = (
            "no_groups_matched" if stats["words_matched"] == 0 else "partial_match_no_complete_group"
        )
        # Teşhis için ilk birkaç kelimeyi karşılaştırmalı göster.
        stats["sample_expected"] = groups[0].split()[:5] if groups else []
        stats["sample_whisper"] = [w.get("word") for w in word_timestamps[:5]]

    return entries, stats


def transcribe_word_timestamps(audio_bytes: bytes, scene_index: int | str = "?") -> Optional[list[dict]]:
    """
    TTS ses baytlarını Whisper'a geri gönderip kelime bazlı zaman damgası
    çıkarır. OpenAI TTS (audio.speech) zaman damgası döndürmez — bu yüzden
    üretilen ses ayrıca transkript edilir. Tahmin değil ölçüm: kelime
    zamanlaması sesin kendisinden çıkarılır.

    Başarısızlıkta None döner ve hatayı loglar (sessizce yutmaz) — çağıran
    bu durumda generate_captions'ı word_timestamps=None ile çağırır, ki bu
    da açıkça daha düşük hassasiyetli fast_path'e düşer (yine loglanır,
    bkz. generate_captions içindeki "fast path'e düşülüyor" uyarısı).
    """
    import io

    from openai import OpenAI

    from app.core.config import settings

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "scene.mp3"
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
            prompt=_WHISPER_DOMAIN_PROMPT,
        )
    except Exception as exc:
        logger.error(f"[caption] sahne {scene_index} whisper transkript hatası: {exc}")
        return None

    words = getattr(result, "words", None)
    if not words:
        logger.error(f"[caption] sahne {scene_index} whisper kelime zaman damgası döndürmedi")
        return None

    return [{"word": w.word, "start": w.start, "end": w.end} for w in words]


def generate_captions(
    voice_text: str,
    total_seconds: float,
    start_offset: float = 0.0,
    word_timestamps: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Ana giriş noktası. Storyboard sahnesine eklenecek captions listesini üretir.

    Args:
        voice_text:       TTS'e gönderilen ham metin (normalizasyon öncesi veya sonrası)
        total_seconds:    Bu sahnenin ses süresi
        start_offset:     Kompozisyon içindeki başlangıç zamanı (saniye, default 0)
        word_timestamps:  Whisper word-level timestamp'leri (varsa hassas zamanlama)

    Returns:
        [{"start": float, "end": float, "text": str}, ...]
    """
    if not voice_text or not voice_text.strip():
        return []

    if total_seconds <= 0:
        logger.warning("[caption] total_seconds ≤ 0 — altyazı üretilemiyor")
        return []

    groups = _split_semantic_groups(voice_text)
    if not groups:
        return []

    if word_timestamps:
        entries, match_stats = _timing_from_whisper(groups, word_timestamps, start_offset)
        if not entries:
            logger.warning(
                "[caption] Whisper eşleştirme başarısız — fast path'e düşülüyor "
                "(neden=%s gruplar=%d/%d kelimeler=%d/%d whisper_kelime=%d "
                "örnek_beklenen=%s örnek_whisper=%s)",
                match_stats.get("reason"),
                match_stats.get("groups_matched", 0), match_stats.get("groups_total", len(groups)),
                match_stats.get("words_matched", 0), match_stats.get("words_total", 0),
                match_stats.get("whisper_words_total", 0),
                match_stats.get("sample_expected"), match_stats.get("sample_whisper"),
            )
            entries = _timing_from_wordcount(groups, total_seconds, start_offset)
    else:
        entries = _timing_from_wordcount(groups, total_seconds, start_offset)

    return [{"start": e.start, "end": e.end, "text": e.text} for e in entries]


def validate_captions(captions: list[dict]) -> list[str]:
    """
    Üretilmiş altyazı listesini spec'e göre doğrular.
    Returns: hata mesajları listesi (boş → OK)
    """
    errors: list[str] = []
    if not captions:
        return errors

    for i, cap in enumerate(captions):
        text = cap.get("text", "")
        start = cap.get("start", 0.0)
        end = cap.get("end", 0.0)

        # Süre kontrolü
        if end <= start:
            errors.append(f"Altyazı {i+1}: end ({end}) ≤ start ({start})")

        if not text.strip():
            errors.append(f"Altyazı {i+1}: boş metin")
            continue

        # Büyük harf oranı
        ratio = _uppercase_ratio(text)
        if ratio > _UPPERCASE_RATIO_LIMIT:
            errors.append(
                f"Altyazı {i+1}: büyük harf oranı %{ratio*100:.0f} > %{_UPPERCASE_RATIO_LIMIT*100:.0f}"
                f" — '{text[:30]}'"
            )

        # Kelime sayısı
        wc = len(text.split())
        if wc > _MAX_GROUP_WORDS * 2:
            errors.append(
                f"Altyazı {i+1}: {wc} kelime çok uzun ({_MAX_GROUP_WORDS*2} max)"
                f" — '{text[:30]}'"
            )

        # Karakter uzunluğu (2 satır × maxCharsPerLine)
        if len(text) > _MAX_CAPTION_CHARS * 2:
            errors.append(
                f"Altyazı {i+1}: {len(text)} karakter ({_MAX_CAPTION_CHARS*2} max)"
            )

    # Zaman örtüşme kontrolü
    for i in range(len(captions) - 1):
        cur_end = captions[i].get("end", 0.0)
        nxt_start = captions[i+1].get("start", 0.0)
        gap = nxt_start - cur_end
        if gap < -0.05:    # 50ms tolerans
            errors.append(
                f"Altyazı {i+1}→{i+2}: örtüşme {abs(gap)*1000:.0f} ms"
            )

    return errors


def add_captions_to_storyboard(storyboard: dict) -> dict:
    """
    Storyboard'daki tüm sahnelere altyazı ekler.
    Zaten captions alanı olan sahneler atlanır.
    Offset: her sahnenin storyboard içindeki başlangıç zamanı.

    Returns: güncellemiş storyboard (in-place değil, kopya)
    """
    import copy
    result = copy.deepcopy(storyboard)
    scenes = result.get("scenes", [])

    cursor = 0.0
    for scene in scenes:
        duration = float(scene.get("duration_seconds") or 0)

        # Zaten altyazısı olan sahneyi atla
        if scene.get("captions"):
            cursor += duration
            continue

        voice_text = (scene.get("voice_text") or "").strip()
        if not voice_text or duration <= 0:
            cursor += duration
            continue

        # Whisper timestamp'leri varsa kullan
        word_ts = scene.get("whisper_word_timestamps")

        captions = generate_captions(
            voice_text=voice_text,
            total_seconds=duration,
            start_offset=cursor,
            word_timestamps=word_ts,
        )
        scene["captions"] = captions
        cursor += duration

    return result
