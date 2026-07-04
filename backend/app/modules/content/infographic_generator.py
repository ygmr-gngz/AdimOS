"""İnfografik storyboard üreticisi — Bilgi Merkezi RAG + LLM (GÖREV 4)."""
import logging
from app.core.llm_client import chat_json as llm_json
from app.modules.knowledge.retriever import retrieve

logger = logging.getLogger(__name__)

_SYSTEM = """Sen bir eğitim içerik tasarımcısısın.
Adım Müşavirlik adına SGS/SMMM muhasebe eğitim infografikleri üretiyorsun.
Türkçe, net ve öğretici içerik üretirsin.
Yanıtın daima geçerli JSON olsun."""

_CARD_GRID_PROMPT = """Aşağıdaki kaynak metinden '{topic}' konusunda {card_count} kartlık infografik üret.

KAYNAK:
{context}

JSON:
{{
  "infographic_title": "Başlık (max 50 kar.)",
  "infographic_subtitle": "Alt başlık (max 80 kar.)",
  "cards": [
    {{
      "title": "Kart başlığı (max 30 kar.)",
      "category": "Aktif veya Pasif veya Gelir veya Gider",
      "content": "Açıklama (max 100 kar.)",
      "icon": "Tek emoji"
    }}
  ],
  "footer_note": "Kaynak notu (max 60 kar.)"
}}

Tam olarak {card_count} kart. Tüm metinler Türkçe."""

_COMPARISON_PROMPT = """Aşağıdaki kaynak metinden '{topic}' konusunda karşılaştırma infografiği üret.

KAYNAK:
{context}

JSON:
{{
  "infographic_title": "Başlık (max 50 kar.)",
  "infographic_subtitle": "Alt başlık (max 80 kar.)",
  "comparison_left": {{
    "title": "Sol başlık (max 30 kar.)",
    "items": ["madde 1", "madde 2", "madde 3", "madde 4", "madde 5"]
  }},
  "comparison_right": {{
    "title": "Sağ başlık (max 30 kar.)",
    "items": ["madde 1", "madde 2", "madde 3", "madde 4", "madde 5"]
  }},
  "footer_note": "Kaynak notu (max 60 kar.)"
}}

Tüm metinler Türkçe."""

_PROCESS_PROMPT = """Aşağıdaki kaynak metinden '{topic}' konusunda {step_count} adımlı süreç infografiği üret.

KAYNAK:
{context}

JSON:
{{
  "infographic_title": "Başlık (max 50 kar.)",
  "infographic_subtitle": "Alt başlık (max 80 kar.)",
  "process_steps": [
    {{
      "title": "Adım başlığı (max 40 kar.)",
      "description": "Açıklama (max 100 kar.)"
    }}
  ],
  "footer_note": "Kaynak notu (max 60 kar.)"
}}

Tam olarak {step_count} adım. Tüm metinler Türkçe."""

_BRAND = {
    "primary_color": "#0D1B3E",
    "secondary_color": "#2B7FE0",
    "background_color": "#08121E",
    "font_heading": "Playfair Display",
    "font_body": "Lato",
}

_TEMPLATE_TO_COMPONENT = {
    "card_grid":  "InfographicCardGridScene",
    "comparison": "InfographicComparisonScene",
    "process":    "InfographicProcessScene",
}


def _rag_context(topic: str, max_chars: int = 2500) -> str:
    chunks = retrieve(topic, match_count=8, match_threshold=0.25)
    if not chunks:
        return f"['{topic}' için önceden yüklenmiş belge bulunamadı — genel bilgi kullanılacak]"
    parts, total = [], 0
    for chunk in chunks:
        text = (chunk.get("content") or chunk.get("chunk_data", ""))[:600]
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n\n".join(parts)


def generate_infographic_storyboard(
    topic: str,
    template: str = "card_grid",
    card_count: int = 6,
    step_count: int = 5,
    format: str = "9:16",
) -> dict:
    """
    Bilgi Merkezi RAG + LLM ile infografik sahnesi üret.
    Remotion InfographicVideo storyboard JSON döndürür.
    template: card_grid | comparison | process
    """
    context = _rag_context(topic)
    component = _TEMPLATE_TO_COMPONENT.get(template, "InfographicCardGridScene")

    if template == "comparison":
        prompt = _COMPARISON_PROMPT.format(topic=topic, context=context)
    elif template == "process":
        prompt = _PROCESS_PROMPT.format(topic=topic, context=context, step_count=step_count)
    else:
        prompt = _CARD_GRID_PROMPT.format(topic=topic, context=context, card_count=card_count)

    scene_data = llm_json(
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        model="gpt-4o-mini",
        temperature=0.4,
        max_tokens=1600,
        caller="infographic_generator",
    )

    logger.info(
        f"[infographic] storyboard üretildi: '{scene_data.get('infographic_title')}' "
        f"template={template} format={format}"
    )

    return {
        "video_type": "lesson",
        "title": scene_data.get("infographic_title", topic),
        "format": format,
        "language": "tr",
        "brand": _BRAND,
        "scenes": [
            {
                "id": 1,
                "component": component,
                "duration_seconds": 15,
                **scene_data,
            }
        ],
    }
