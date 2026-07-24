"""
Kanal kalite profili — ADIM MÜŞAVİR kanalı için içerik standartları.
Section 12: channel_profile config.

Bu config pipeline boyunca kalite kararlarına referans olarak kullanılır.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ChannelProfile:
    # Kanal kimliği
    channel_id:        str
    channel_name:      str
    instagram_handle:  str
    youtube_handle:    str

    # Ses
    tts_voice:         str   # OpenAI TTS voice
    tts_speed:         float
    tts_model:         str
    min_volume_db:     float  # sessiz video eşiği

    # Video format
    default_format:    str   # "9:16" | "16:9"
    fps:               int
    reel_width:        int
    reel_height:       int

    # Süre toleransları (saniye)
    reel_target_sec:   int
    reel_tolerance_sec: int
    quiz_scene_sec:    int
    lesson_min_sec:    int

    # İçerik kalitesi
    min_reel_scenes:   int
    min_lesson_scenes: int
    dedup_threshold:   float  # cosine similarity eşiği

    # Marka renkleri
    primary_color:     str
    secondary_color:   str
    background_color:  str
    font_heading:      str
    font_body:         str

    # Yayın zamanlaması (opsiyonel)
    post_days:         tuple = field(default_factory=tuple)
    post_hours_utc3:   tuple = field(default_factory=tuple)


ADIM_MUSAVIR: ChannelProfile = ChannelProfile(
    channel_id        = "adim_musavir",
    channel_name      = "Adım Müşavir",
    instagram_handle  = "@adimmusavir",
    youtube_handle    = "@adimmusavir",

    # TTS ayarları
    tts_voice         = "nova",      # kadın öğretmen sesi
    tts_speed         = 0.93,
    tts_model         = "tts-1-hd",
    min_volume_db     = -45.0,

    # Format
    default_format    = "9:16",
    fps               = 30,
    reel_width        = 1080,
    reel_height       = 1920,

    # Süre toleransları
    reel_target_sec   = 120,
    reel_tolerance_sec = 15,
    quiz_scene_sec    = 55,
    lesson_min_sec    = 1080,  # 18 dakika minimum

    # Kalite
    min_reel_scenes   = 5,
    min_lesson_scenes = 8,
    dedup_threshold   = 0.82,

    # Marka
    primary_color     = "#0B2A4A",
    secondary_color   = "#C9A96E",
    background_color  = "#FAF7F0",
    font_heading      = "Playfair Display",
    font_body         = "Lato",

    # Yayın günleri/saatleri (TR +3)
    post_days        = (1, 3, 5),   # Pazartesi, Çarşamba, Cuma
    post_hours_utc3  = (9, 18, 20), # Sabah 9, Akşam 18, Gece 20
)


def get_channel_brand(profile: ChannelProfile | None = None) -> dict:
    """Profile'dan Remotion BrandConfig sözlüğü üretir."""
    p = profile or ADIM_MUSAVIR
    return {
        "primary_color":    p.primary_color,
        "secondary_color":  p.secondary_color,
        "background_color": p.background_color,
        "font_heading":     p.font_heading,
        "font_body":        p.font_body,
        "handle":           p.instagram_handle,
    }
