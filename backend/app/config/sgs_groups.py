"""SGS ders grupları — tek kaynak, hem backend hem frontend kullanır."""

SGS_LESSON_GROUPS: dict[str, list[str]] = {
    "Genel Dersler": ["Türkçe", "Matematik", "Tarih - Genel Kültür", "İngilizce"],
    "Hukuk": ["Ticaret Hukuku", "Borçlar Hukuku", "Vergi Hukuku", "Meslek Hukuku", "İş ve Sosyal Güvenlik Hukuku"],
    "Muhasebe": ["Finansal Muhasebe", "Muhasebe Standartları", "Muhasebe Bilgi Sistemi", "Maliyet Muhasebesi", "Mali Tablolar Analizi", "Muhasebe Denetimi"],
    "Finans": ["Maliye", "İktisat"],
}


def get_group_for_lesson(lesson: str) -> str | None:
    for group, lessons in SGS_LESSON_GROUPS.items():
        if lesson in lessons:
            return group
    return None


def get_lessons_for_group(group: str) -> list[str]:
    return SGS_LESSON_GROUPS.get(group, [])
