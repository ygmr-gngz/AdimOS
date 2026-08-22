"""İnfografik storyboard üreticisi — Bilgi Merkezi RAG + LLM (GÖREV 4)."""
import logging
from app.core.llm_client import chat_json as llm_json
from app.core.account_catalog import prompt_catalog, validate_account_identity
from app.modules.knowledge.retriever import retrieve

logger = logging.getLogger(__name__)

_SYSTEM = """Sen bir eğitim içerik tasarımcısısın.
Adım Müşavirlik adına SGS/SMMM muhasebe eğitim infografikleri üretiyorsun.
Türkçe, net ve öğretici içerik üretirsin.
Yanıtın daima geçerli JSON olsun."""

_CARD_GRID_PROMPT = """Aşağıdaki kaynak metinden '{topic}' konusunda {card_count} adet muhasebe hesap kartı üret.

KAYNAK:
{context}

İZİNLİ HESAPLAR (kod, ad ve nitelik AYNEN korunacak):
{account_catalog}

JSON:
{{
  "cards": [
    {{
      "accountCode": "191",
      "accountName": "İndirilecek KDV",
      "nature": "A veya P veya G veya Gi",
      "purpose": "12-25 kelimelik amaç açıklaması",
      "journalEntry": [
        {{"code":"153", "name":"TİCARİ MALLAR", "side":"debit", "amount":"10.000"}},
        {{"code":"191", "name":"İNDİRİLECEK KDV", "side":"debit", "amount":"2.000"}},
        {{"code":"320", "name":"SATICILAR", "side":"credit", "amount":"12.000"}}
      ],
      "entryCaption": "En fazla 6 kelime",
      "tip": "10-22 kelimelik püf noktası"
    }}
  ]
}}

Kurallar:
- Tam olarak {card_count} kart ve her kart farklı bir hesap; yalnızca İZİNLİ HESAPLAR listesinden seç.
- accountName katalogdaki adla birebir aynı ve en fazla 4 kelime olacak.
- XXX/YYY placeholder yasak; gerçek, yuvarlak Türkçe tutarlar kullan.
- Her kartta borç toplamı alacak toplamına eşit olacak.
- Nature muhasebe niteliğine göre doğru seçilecek: A=Aktif, P=Pasif, G=Gelir, Gi=Gider.
- Emoji, logo veya serbest görsel istemi üretme.
- Tüm metinler Türkçe."""

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
        prompt = _CARD_GRID_PROMPT.format(
            topic=topic,
            context=context,
            card_count=card_count,
            account_catalog=prompt_catalog(),
        )

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

    if template == "card_grid":
        cards = scene_data.get("cards") or []
        scenes = [
            {
                "id": i,
                "component": "AccountCardScene",
                "duration_seconds": 8,
                **card,
            }
            for i, card in enumerate(cards, 1)
        ]
        storyboard = {
            "video_type": "gorsel_post",
            "title": topic,
            "format": format,
            "language": "tr",
            "brand": _BRAND,
            "scenes": scenes,
        }
        validate_account_card_storyboard(storyboard, expected_count=card_count)
        return storyboard

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


def _amount_value(raw) -> float:
    """10.000,50 biçimini deterministik sayıya çevirir; bilinmeyeni kabul etmez."""
    text = str(raw or "").strip().replace("₺", "").replace(" ", "")
    if not text or any(token in text.upper() for token in ("XXX", "YYY")):
        raise RuntimeError(f"math_validation_failed: geçersiz tutar {raw!r}")
    try:
        return float(text.replace(".", "").replace(",", "."))
    except ValueError as exc:
        raise RuntimeError(f"math_validation_failed: geçersiz tutar {raw!r}") from exc


def validate_account_card_storyboard(storyboard: dict, expected_count: int = 3) -> None:
    """LLM üretimi ve dışarıdan gelen pre_storyboard için aynı kalite kapısı."""
    scenes = storyboard.get("scenes") or []
    if len(scenes) != expected_count:
        raise RuntimeError(
            f"Hesap kartı sayısı hatalı: hedef={expected_count}, üretilen={len(scenes)}"
        )

    seen_codes: set[str] = set()
    for i, card in enumerate(scenes, 1):
        if card.get("component") != "AccountCardScene":
            raise RuntimeError(
                f"account_catalog_validation_failed: kart={i} bileşen={card.get('component')!r}"
            )
        code = str(card.get("accountCode") or "").strip()
        validate_account_identity(code, card.get("accountName"), card.get("nature"))
        if code in seen_codes:
            raise RuntimeError(f"account_catalog_validation_failed: mükerrer hesap kodu {code}")
        seen_codes.add(code)

        entries = card.get("journalEntry") or []
        sides = {entry.get("side") for entry in entries}
        if not entries or not sides.issubset({"debit", "credit"}) or sides != {"debit", "credit"}:
            raise RuntimeError(f"math_validation_failed: kart={i} borç/alacak satırları eksik")
        debit = sum(_amount_value(e.get("amount")) for e in entries if e.get("side") == "debit")
        credit = sum(_amount_value(e.get("amount")) for e in entries if e.get("side") == "credit")
        if abs(debit - credit) > 0.005:
            raise RuntimeError(
                f"math_validation_failed: kart={i} borç={debit:g} alacak={credit:g}"
            )
