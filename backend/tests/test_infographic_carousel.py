from unittest.mock import patch

from app.modules.content.infographic_generator import generate_infographic_storyboard


def _carousel_payload() -> dict:
    return {
        "cover": {"title": "KDV'yi 5 Kartta Öğren", "subtitle": "Temelden örneğe", "cards": [{"title": "Ana fikir", "content": "Kısa açıklama"}]},
        "concepts": {"title": "Temel Kavramlar", "cards": [{"title": "Matrah", "content": "Verginin hesaplandığı tutar"}]},
        "comparison": {"title": "Kritik Ayrım", "left": {"title": "Dahil", "items": ["Vergi toplamda"]}, "right": {"title": "Hariç", "items": ["Vergi ayrıca"]}},
        "process": {"title": "Nasıl Uygulanır?", "steps": [{"number": 1, "title": "Matrah", "desc": "Tutarı belirle"}, {"number": 2, "title": "Oran", "desc": "Oranı uygula"}, {"number": 3, "title": "Sonuç", "desc": "Toplamı bul"}]},
        "finale": {"title": "Formül ve İpucu", "cards": [{"title": "KDV", "content": "Matrah × oran", "example": "1.000 × %20", "tip": "Dahil-hariç ayrımına dikkat"}]},
    }


def test_new_infographic_modes_create_five_slide_carousel() -> None:
    for mode in ("illustrated", "mind_map", "process", "accounting_solution", "comparison", "formula_example", "exam_tip"):
        with patch("app.modules.content.infographic_generator._rag_context", return_value="kaynak"), patch(
            "app.modules.content.infographic_generator.llm_json", return_value=_carousel_payload()
        ):
            storyboard = generate_infographic_storyboard("KDV", template=mode)

        assert storyboard["video_type"] == "gorsel_post"
        assert len(storyboard["scenes"]) == 5
        assert storyboard["scenes"][0]["component"] == "InfographicCardGridScene"
        assert storyboard["scenes"][2]["component"] == "InfographicComparisonScene"
        assert storyboard["scenes"][3]["component"] == "InfographicProcessScene"
