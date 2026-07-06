from pypdf import PdfReader
import io
import logging

logger = logging.getLogger(__name__)


def load_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
            logger.info("[pdf_loader] Şifreli PDF boş şifreyle açıldı")
        except Exception as e:
            raise ValueError(f"PDF şifreli ve açılamıyor: {e}") from e
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            "PDF'den metin çıkarılamadı. Büyük olasılıkla taranmış (görüntü tabanlı) bir PDF. "
            "Lütfen OCR uygulanmış veya metin katmanlı PDF yükleyin."
        )
    return text
