# Yol Haritası

## Faz Planı

| Faz | Kapsam | Durum |
|-----|--------|:-----:|
| 1 | Bilgi tabanı, Asistan (Chat + Ses), Dashboard | ✅ Aktif |
| 2 | CRM, Follow-up Agent | 🔧 Hazırlanıyor |
| 3 | SGS Akademi | 🔧 Hazırlanıyor |
| 4 | İçerik Otomasyonu (YouTube / Instagram) | ✅ Aktif |
| 4b | Web Sitesi Chatbotu (embed widget) | ✅ Aktif |
| 5 | Raporlar ve analitik | 🔧 Hazırlanıyor |
| 6 | Çoklu kullanıcı, white-label | 📋 Planlandı |

## Faz 1 — Bilgi Tabanı + Asistan

- [x] Frontend arayüzü (Next.js 15)
- [x] Sidebar, Header, AppShell
- [x] Asistan Widget (chat + ses birleşik)
- [x] Doküman yükleme UI
- [ ] PDF → chunk → embedding pipeline (backend)
- [ ] RAG soru-cevap endpoint (backend)
- [ ] Sesli asistan STT + TTS (backend)
- [ ] Dashboard istatistikleri (backend)

## Faz 2 — CRM

- [x] Lead listesi UI
- [ ] Lead ekleme / güncelleme (backend)
- [ ] Lead skorlama (CRM Agent)
- [ ] Otomatik follow-up mesajları (Follow-up Agent)

## Faz 3 — SGS Akademi

- [x] Öğrenci listesi UI
- [ ] Öğrenci ekleme / güncelleme (backend)
- [ ] Sınav denemesi kayıt (backend)
- [ ] AI öğrenme planı (Learning Agent)

## Faz 4 — İçerik Otomasyonu

- [x] İçerik üretme UI (platform, ton, hedef kitle)
- [x] Onay akışı UI
- [ ] AI içerik üretimi (Automation Agent)
- [ ] YouTube yayınlama (Google API)
- [ ] Instagram yayınlama (Meta Graph API)

## Faz 4b — Web Sitesi Chatbotu

- [x] /widget sayfası (iframe embed)
- [x] public/embed.js (script embed)
- [x] /website konuşma raporu (dashboard)
- [ ] /website/chat endpoint (backend)
- [ ] /website/voice endpoint (backend)
- [ ] /website/conversations endpoint (backend)

## Faz 5 — Raporlar

- [x] Raporlar iskelet sayfası
- [ ] Doküman analizi grafikleri
- [ ] Agent performans istatistikleri
- [ ] Müşteri dönüşüm raporu

## Faz 6 — Çoklu Kullanıcı

- [ ] Rol yönetimi (admin / çalışan)
- [ ] White-label (farklı şirketlere satış)
- [ ] Kullanım bazlı faturalandırma
