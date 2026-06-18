# Görev Log'u

> Format: `YYYY-MM-DD · ne yapıldı · sonuç/not`. En yeni en üstte.

- 2026-06-17 · Faz 6 — validation + records UI polish (19 component, 9 shadcn primitive, Zustand filters store, URL query senkron, sidebar layout) + `npx tsc --noEmit` 0 hata + `npx eslint` 0 hata · tamam
- 2026-06-17 · Faz 6 — README dolu içerik (43 kural 6 kategori tablosu, dürüst yapamadıklarım listesi, mimari kararlar) + CHECKLIST güncelleme (8/15 + bonus) + ai_usage envanter (7 satır) + 00_overall_summary · tamam
- 2026-06-17 · Faz 5 — sync feature (aggregator, client, retry policy, service, 4 endpoint) + sync_submissions error_message kolonu + SyncPage/HistoryTable (auto-refresh 3s) · tamam
- 2026-06-17 · Faz 4 — records feature (7-filtrli paginated list + CSV export streaming + UTF-8 BOM) + 4 endpoint · tamam
- 2026-06-17 · Faz 3 — analytics service (5 filtre-aware agregasyon: kpis, oee-trend, shift-comparison, station-ranking, quality-distribution) + Dashboard 4 grafik + KPI + 5 paralel TanStack Query hook · tamam
- 2026-06-17 · Faz 2.5 — DB şema/kod uyumsuzluk düzeltmesi (ProductionRecord.status, ValidationIssue.field_names, RecordEdit JSON audit, config 10 alan, NotFoundError) · tamam
- 2026-06-17 · Faz 2 — validation motoru (43 kural, 6 kategori, iki geçişli engine, report.py sistemik/tekil tespiti, 7 endpoint) · tamam
- 2026-06-17 · Faz 1 — ingestion feature (CSV parse + tarih/ondalık/yüzde normalize + file_hash + row_hash + ImportSummary + 2 endpoint + seed CLI) · tamam
- 2026-06-17 · Faz 0 — DB şema doğrulama + `init_db.py` iyileştirmesi (6 tablo, sıralı metadata.create_all) · tamam
- 2026-06-17 · Faz 0 — git init + remote git@github.com:Ardovski/UA_Magna.git + main push (temiz başlangıç) · tamam
- 2026-06-17 · ai_usage otomasyonu (şablon üretici `make ai-prompt` + transcript export `make ai-backup` + opt-in UserPromptSubmit log hook) + yapı (prompts/transcripts/screenshots) · tamam
- 2026-06-17 · ESLint yasakları (boundaries feature-izolasyonu + no-restricted-imports/syntax + no-cycle) + prohibitions/feature-architecture dokümanları + `.ai/memory` bellek sistemi · tamam
- 2026-06-17 · `.docs` yeniden yapılandırma (shared/api/web) + profesyonelleştirme + skill'ler (`.claude/skills`) + hook'lar (`.githooks`) · tamam
- 2026-06-17 · AI bağlam: `AGENTS.md` (MiniMax) + `CLAUDE.md` senkron; isimlendirme standartları + VS Code dosya yuvalama · tamam
- 2026-06-17 · Monorepo iskeleti + Makefile + `.docs` + `.roadmap`/CHECKLIST + backend/web scaffold + DB katmanı (5 tablo) · tamam
- 2026-06-17 · debug/test taraması (API 25 route + 5 sayfa 200, pytest 32 geçti, tsc/lint temiz) + routing bug fix: / ve /sync `(dashboard)` route group dışındaydı → navigasyon yoktu; route group'a taşındı + global responsive Header nav (NAV_ITEMS tek kaynak, Sidebar kaldırıldı, iç içe <main> giderildi) · tamam
- 2026-06-17 · bug fix turu: (1) RecordsPage sonsuz döngü (hydrate effect `filter` bağımlılığı + daima-true guard → mount-once ref guard + getState); (2) useRecords yanlış endpoint /api/v1/records → /api/v1/records/list; (3) oee_trend boş (today()'e sabitleniyordu, seed=Kasım 2025 → max(prod_date)'e sabitlendi). pytest 32 / tsc / eslint temiz · tamam
- 2026-06-17 · OEE hibrit semantik: avg_oee artık yalnız valid+fixed kayıtlardan (CASE ile kpis + shift_comparison; trend/station_ranking valid+fixed'e hizalandı), hacim/sayımlar tüm kayıtlarda kalır. _OEE_STATUSES sabiti. KPI %618→%91.5, shift ~%1200→~%91. KpiCard hint 'temiz veri'. pytest 32 / tsc / eslint temiz · tamam
- 2026-06-17 · OEE yeniden hesap (app/core/oee.py): MES'in garbage OEE/P kolonu yerine A=Çalışma/(Çalışma+Plansız), Q=(Üretim-Fire)/Üretim, P kolondan; hepsi [0,100] clamp; üretim=0→0, tamamen boş→None. oee_recomputed ingestion'da dolduruluyor. Analytics+sync oee_recomputed kullanıyor (basit ortalama, tüm kayıt). KPI OEE 91.55→71.48 (gerçekçi). +6 birim test (test_oee.py). pytest 38/tsc/eslint temiz · tamam
