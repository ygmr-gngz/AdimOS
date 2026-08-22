"""Görsel hesap kartları için doğrulanmış Tekdüzen Hesap Planı alt kümesi.

LLM hesap kodu/adı/niteliği uyduramaz. Katalog, kullanıcının onayladığı
"En Çok Sorulan Hesaplar" referansındaki kartların tek doğruluk kaynağıdır.
"""

ACCOUNT_CATALOG: dict[str, tuple[str, str]] = {
    "100": ("Kasa", "A"),
    "102": ("Bankalar", "A"),
    "120": ("Alıcılar", "A"),
    "153": ("Ticari Mallar", "A"),
    "191": ("İndirilecek KDV", "A"),
    "257": ("Birikmiş Amortismanlar", "P"),
    "320": ("Satıcılar", "P"),
    "360": ("Ödenecek Vergi ve Fonlar", "P"),
    "391": ("Hesaplanan KDV", "P"),
    "600": ("Yurt İçi Satışlar", "G"),
    "621": ("Satılan Ticari Mallar Maliyeti", "Gi"),
    "690": ("Dönem Kârı veya Zararı", "Gi"),
    "692": ("Dönem Net Kârı veya Zararı", "Gi"),
    "770": ("Genel Yönetim Giderleri", "Gi"),
}


def prompt_catalog() -> str:
    return "\n".join(
        f"- {code}: {name} ({nature})"
        for code, (name, nature) in ACCOUNT_CATALOG.items()
    )


def validate_account_identity(code: object, name: object, nature: object) -> None:
    code_text = str(code or "").strip()
    expected = ACCOUNT_CATALOG.get(code_text)
    if expected is None:
        raise RuntimeError(
            f"account_catalog_validation_failed: katalog dışı hesap kodu {code_text!r}"
        )
    actual_name = " ".join(str(name or "").split()).casefold()
    expected_name, expected_nature = expected
    if actual_name != expected_name.casefold() or str(nature or "").strip() != expected_nature:
        raise RuntimeError(
            "account_catalog_validation_failed: "
            f"{code_text} için beklenen=({expected_name!r},{expected_nature}) "
            f"üretilen=({name!r},{nature!r})"
        )
