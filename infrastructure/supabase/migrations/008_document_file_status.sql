-- Migration 008: Doküman kayıt durumu (GÖREV 6 — kayıp PDF kapanışı)
-- Tarih: 2026-07-04
-- Supabase SQL Editor'de çalıştır.

-- 1. Dosya durumu alanı
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS file_status TEXT DEFAULT 'mevcut'
    CHECK (file_status IN ('mevcut', 'kayip', 'yeniden_yuklendi')),
  ADD COLUMN IF NOT EXISTS page_count INTEGER,
  ADD COLUMN IF NOT EXISTS storage_verified_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS relinked_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS original_document_id UUID REFERENCES documents(id);

-- 2. Mevcut kayıtları işaretle
-- Dosyası olmayan (storage'da açılmayan) kayıtlar için:
-- Bu sorguyu çalıştırmadan önce hangi document_id'lerin kayıp olduğunu belirleyin.
-- Örnek: UPDATE documents SET file_status = 'kayip' WHERE id IN ('uuid1', 'uuid2');

-- 3. İndeks
CREATE INDEX IF NOT EXISTS idx_documents_file_status ON documents (file_status);

-- 4. Storage doğrulama trigger'ı için hazırlık
-- (Gerçek storage doğrulaması backend'de yapılır; bu alan sadece durumu saklar)
COMMENT ON COLUMN documents.file_status IS
  'mevcut: Dosya storage''da mevcut ve erişilebilir
   kayip: Dosya storage''dan silindi veya hiç yüklenmedi; chunk/soru verisi korunuyor
   yeniden_yuklendi: Kullanıcı dosyayı bulup yeniden bağladı';

COMMENT ON COLUMN documents.storage_verified_at IS
  'Backend''in storage''dan dosyayı başarıyla çektiğini doğruladığı son zaman';

COMMENT ON COLUMN documents.relinked_at IS
  'Kullanıcının kayıp dosyayı yeniden bağladığı zaman';
