"use client";

import { BookOpen, Calculator, Database, Github, Globe, ListChecks, Send, TriangleAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/lib/i18n";

/**
 * Tanımlar / Definitions — statik referans sayfası.
 * İçerik kaynağı: MAGNA case study PDF (Veri Sözlüğü, OEE formülü, hedef API alanları,
 * hata kodları) + proje içi sözlük. Çift dilli (TR/EN); locale'e göre seçilir.
 */
type Bi = { tr: string; en: string };
const bi = (tr: string, en: string): Bi => ({ tr, en });

interface DictRow {
  n: number;
  csv: string;
  id: string;
  type: string;
  desc: Bi;
  rule: Bi;
}

const DICT: DictRow[] = [
  { n: 1, csv: "record_id", id: "record_id_src", type: "int", desc: bi("Kayıt tekil numarası", "Unique record id"), rule: bi("benzersiz, boş değil", "unique, not empty") },
  { n: 2, csv: "Tarih", id: "prod_date", type: "date", desc: bi("Üretim günü", "Production day"), rule: bi("geçerli tarih, gelecekte değil", "valid date, not in the future") },
  { n: 3, csv: "İş Emri No", id: "work_order_no", type: "string", desc: bi("İş emri (302 ile başlayan 10 haneli)", "Work order (10 digits starting with 302)"), rule: bi("^302\\d{7}$ · örn. 3025678325", "^302\\d{7}$ · e.g. 3025678325") },
  { n: 4, csv: "İş Merkezi No", id: "work_center_no", type: "string", desc: bi("İş merkezi kodu", "Work center code"), rule: bi("boş değil", "not empty") },
  { n: 5, csv: "İşmerkezi Adı", id: "work_center_name", type: "string", desc: bi("İş merkezi tanımı", "Work center name"), rule: bi("—", "—") },
  { n: 6, csv: "İş İstasyon Adı", id: "station_name", type: "string", desc: bi("Makine kodu (örn. IMM-2700-3)", "Machine code (e.g. IMM-2700-3)"), rule: bi("^IMM-\\d+-\\d+$ (gevşek)", "^IMM-\\d+-\\d+$ (loose)") },
  { n: 7, csv: "Stok Adı", id: "stock_name", type: "string", desc: bi("Üretilen parça/ürün", "Produced part/product"), rule: bi("boş değil", "not empty") },
  { n: 8, csv: "Vardiya", id: "shift", type: "int", desc: bi("Vardiya numarası", "Shift number"), rule: bi("∈ {1, 2, 3}", "∈ {1, 2, 3}") },
  { n: 9, csv: "A (Kullanılırlık)", id: "availability", type: "float", desc: bi("Availability — yüzde", "Availability — percent"), rule: bi("0–100", "0–100") },
  { n: 10, csv: "P (Performans)", id: "performance", type: "float", desc: bi("Performance — yüzde", "Performance — percent"), rule: bi("0–~100 (>100 şüpheli)", "0–~100 (>100 suspect)") },
  { n: 11, csv: "Q (Kalite)", id: "quality", type: "float", desc: bi("Quality — yüzde", "Quality — percent"), rule: bi("0–100", "0–100") },
  { n: 12, csv: "OEE", id: "oee", type: "float", desc: bi("Overall Equipment Effectiveness — yüzde", "Overall Equipment Effectiveness — percent"), rule: bi("0–100, = A·P·Q/10000", "0–100, = A·P·Q/10000") },
  { n: 13, csv: "Çalışma Süresi", id: "run_time", type: "float", desc: bi("Makine çalışma dakikası", "Machine run minutes"), rule: bi("≥ 0", "≥ 0") },
  { n: 14, csv: "Duruş Süresi", id: "down_time", type: "float", desc: bi("Toplam duruş dakikası", "Total downtime minutes"), rule: bi("≥ 0, = planlı+plansız", "≥ 0, = planned+unplanned") },
  { n: 15, csv: "Planlı Duruş Süresi", id: "planned_down", type: "float", desc: bi("Planlı duruş dakikası", "Planned downtime minutes"), rule: bi("≥ 0", "≥ 0") },
  { n: 16, csv: "Plansız Duruş Süresi", id: "unplanned_down", type: "float", desc: bi("Plansız duruş dakikası", "Unplanned downtime minutes"), rule: bi("≥ 0", "≥ 0") },
  { n: 17, csv: "Üretilen Miktar", id: "produced_qty", type: "int", desc: bi("Toplam üretim adedi", "Total produced units"), rule: bi("≥ 0", "≥ 0") },
  { n: 18, csv: "Hatalı Üretilen Miktar", id: "scrap_qty", type: "int", desc: bi("Fire/scrap adedi", "Scrap units"), rule: bi("≥ 0, ≤ Üretilen", "≥ 0, ≤ produced") },
];

interface ApiField {
  field: string;
  type: string;
  desc: Bi;
}
const API_FIELDS: ApiField[] = [
  { field: "production_date", type: "string", desc: bi("Üretim tarihi — YYYY-MM-DD; gelecek tarih kabul edilmez", "Production date — YYYY-MM-DD; future dates rejected") },
  { field: "shift", type: "integer", desc: bi("Vardiya: 1 (Sabah), 2 (Öğle), 3 (Gece)", "Shift: 1 (Morning), 2 (Afternoon), 3 (Night)") },
  { field: "machine_count", type: "integer", desc: bi("Vardiyada aktif makine sayısı — 1–1000", "Active machine count in shift — 1–1000") },
  { field: "total_production_units", type: "integer", desc: bi("Toplam üretim adedi — 1–1.000.000", "Total produced units — 1–1,000,000") },
  { field: "oe_value", type: "float", desc: bi("Ekipman verimliliği (OEE) — yüzde, 0.0–100.0", "Equipment effectiveness (OEE) — percent, 0.0–100.0") },
];

interface ErrRow {
  code: string;
  meaning: Bi;
}
const ERRORS: ErrRow[] = [
  { code: "401", meaning: bi("Eksik veya geçersiz API key", "Missing or invalid API key") },
  { code: "413", meaning: bi("İstek gövdesi 10 KB sınırını aştı", "Request body exceeded the 10 KB limit") },
  { code: "422", meaning: bi("Validasyon hatası — yanıttaki detail alanını inceleyin", "Validation error — inspect the response detail field") },
  { code: "429", meaning: bi("Rate limit aşıldı — 1 dakika bekleyin", "Rate limit exceeded — wait 1 minute") },
];

interface GlossRow {
  term: string;
  def: Bi;
}
const GLOSSARY: GlossRow[] = [
  { term: "MES", def: bi("Manufacturing Execution System — her vardiya sonunda .csv üretim raporu üreten saha sistemi.", "Manufacturing Execution System — shop-floor system that emits a .csv production report per shift.") },
  { term: "OEE", def: bi("Overall Equipment Effectiveness — A×P×Q/10000. Bantlar: ≥85 iyi, 60–85 orta, <60 düşük.", "Overall Equipment Effectiveness — A×P×Q/10000. Bands: ≥85 good, 60–85 mid, <60 low.") },
  { term: "Availability (A)", def: bi("Kullanılırlık = Çalışma / (Çalışma + Plansız Duruş).", "Availability = Run / (Run + Unplanned downtime).") },
  { term: "Performance (P)", def: bi("Performans = ideal hıza karşı gerçekleşen hız.", "Performance = actual speed vs. ideal speed.") },
  { term: "Quality (Q)", def: bi("Kalite = (Üretilen − Hatalı) / Üretilen.", "Quality = (Produced − Scrap) / Produced.") },
  { term: "Scrap / Fire", def: bi("Hatalı üretilen adet (scrap_qty); üretimden büyük olamaz.", "Defective produced units (scrap_qty); cannot exceed production.") },
  { term: "Downtime / Duruş", def: bi("Toplam duruş = planlı + plansız duruş dakikaları.", "Total downtime = planned + unplanned downtime minutes.") },
  { term: "Import batch", def: bi("Bir CSV yüklemesi (import_batches). Kayıtlar import_batch_id ile batch'e bağlanır.", "One CSV upload (import_batches). Records link to it via import_batch_id.") },
  { term: "file_hash", def: bi("Yüklenen dosyanın SHA-256'sı → aynı dosya tekrar yüklemesini tespit eder.", "SHA-256 of the uploaded file → detects re-uploading the same file.") },
  { term: "row_hash", def: bi("Satırın hash'i → birebir tekrarlanan satırları (V-D01) eler.", "Hash of a row → de-dupes byte-identical rows (V-D01).") },
  { term: "idempotency_key", def: bi('"{YYYY-MM-DD}:{shift}" (örn. 2025-11-05:1) — aynı (gün, vardiya) hedefe iki kez gitmez.', '"{YYYY-MM-DD}:{shift}" (e.g. 2025-11-05:1) — a (day, shift) is not sent twice.') },
  { term: "payload_hash", def: bi("Gönderilecek payload'ın SHA-256'sı — içerik değişti mi anlamak için (force gerekir).", "SHA-256 of the outgoing payload — detects content change (requires force).") },
  { term: "Severity", def: bi("Issue ağırlığı: error → rejected, warning → suspect, info tek başına statü değiştirmez.", "Issue weight: error → rejected, warning → suspect, info alone does not change status.") },
  { term: "Önerilen aksiyon / Suggested action", def: bi("reject (yüksek güven) · warn (sezgisel) · fix (otomatik düzeltilebilir).", "reject (high confidence) · warn (heuristic) · fix (auto-correctable).") },
  { term: "Sistemik vs tekil / Systemic vs unique", def: bi("Bir kural kayıtların ≥%20'sinde görülürse 'sistemik', aksi halde 'tekil' sayılır.", "A rule seen in ≥20% of records is 'systemic', otherwise 'unique'.") },
];

export function DefinitionsPage() {
  const { locale } = useLocale();
  const tx = (b: Bi): string => (locale === "en" ? b.en : b.tr);
  const T = (tr: string, en: string): string => (locale === "en" ? en : tr);

  return (
    <main className="container mx-auto max-w-5xl space-y-6 py-8">
      <header>
        <p className="font-mono text-sm text-muted-foreground">MAGNA · {T("Referans", "Reference")}</p>
        <h1 className="mt-1 flex items-center gap-2 text-3xl font-bold tracking-tight">
          <BookOpen className="h-7 w-7" /> {T("Tanımlar", "Definitions")}
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          {T(
            "Veri sözlüğü, OEE formülü, hedef API alanları ve proje terimleri. Kaynak: MAGNA case study dokümanı + proje içi tanımlar.",
            "Data dictionary, OEE formula, target-API fields and project terms. Source: the MAGNA case-study document + in-project definitions.",
          )}
        </p>
      </header>

      {/* Veri Sözlüğü */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" /> {T("Veri Sözlüğü — production_data.csv", "Data Dictionary — production_data.csv")}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {T("2.117 satır · 18 kolon · 5–25 Kasım 2025", "2,117 rows · 18 columns · 5–25 Nov 2025")}
          </p>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-y bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <th className="p-2">#</th>
                <th className="p-2">{T("Kolon (CSV)", "Column (CSV)")}</th>
                <th className="p-2">{T("İç alan", "Internal field")}</th>
                <th className="p-2">{T("Tip", "Type")}</th>
                <th className="p-2">{T("Açıklama", "Description")}</th>
                <th className="p-2">{T("Kısıt", "Constraint")}</th>
              </tr>
            </thead>
            <tbody>
              {DICT.map((r) => (
                <tr key={r.n} className="border-b transition-colors hover:bg-muted/40">
                  <td className="p-2 tabular-nums text-muted-foreground">{r.n}</td>
                  <td className="p-2 font-medium">{r.csv}</td>
                  <td className="p-2 font-mono text-xs text-muted-foreground">{r.id}</td>
                  <td className="p-2 font-mono text-xs">{r.type}</td>
                  <td className="p-2">{tx(r.desc)}</td>
                  <td className="p-2 font-mono text-xs text-muted-foreground">{tx(r.rule)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* OEE Formülü */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" /> {T("OEE Formülü (referans)", "OEE Formula (reference)")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-md border bg-muted/40 p-3 text-center font-mono text-base font-semibold">
              OEE = A × P × Q / 10000
            </div>
            <ul className="space-y-1.5">
              <li>
                <span className="font-semibold text-oee-good">A</span> {T("(Kullanılırlık)", "(Availability)")} ={" "}
                {T("Çalışma / (Çalışma + Plansız Duruş)", "Run / (Run + Unplanned downtime)")}
              </li>
              <li>
                <span className="font-semibold text-oee-mid">P</span> {T("(Performans)", "(Performance)")} ={" "}
                {T("ideal hıza karşı gerçekleşen hız", "actual speed vs. ideal speed")}
              </li>
              <li>
                <span className="font-semibold text-oee-low">Q</span> {T("(Kalite)", "(Quality)")} ={" "}
                {T("(Üretilen − Hatalı) / Üretilen", "(Produced − Scrap) / Produced")}
              </li>
            </ul>
            <p className="text-xs text-muted-foreground">
              {T(
                "Uygulama OEE'yi bileşenlerden yeniden hesaplar (oee_recomputed) ve [0,100]'e clamp'ler. Bantlar: ",
                "The app recomputes OEE from components (oee_recomputed), clamped to [0,100]. Bands: ",
              )}
              <span className="text-oee-good">≥85</span> · <span className="text-oee-mid">60–85</span> ·{" "}
              <span className="text-oee-low">&lt;60</span>.
            </p>
          </CardContent>
        </Card>

        {/* Vardiya + Statü + Severity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-5 w-5" /> {T("Vardiya, Statü & Severity", "Shift, Status & Severity")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="font-medium">{T("Vardiya kodları", "Shift codes")}</p>
              <p className="text-muted-foreground">
                1 = {T("Sabah", "Morning")} · 2 = {T("Öğle", "Afternoon")} · 3 = {T("Gece", "Night")}
              </p>
            </div>
            <div>
              <p className="font-medium">{T("Kayıt statüsü (severity'den türetilir)", "Record status (derived from severity)")}</p>
              <ul className="text-muted-foreground">
                <li>
                  <span className="text-oee-low">rejected</span> — {T("en az bir", "at least one")} <code>error</code>
                </li>
                <li>
                  <span className="text-oee-mid">suspect</span> — {T("error yok, en az bir", "no error, at least one")} <code>warning</code>
                </li>
                <li>
                  <span className="text-oee-good">valid</span> — {T("error/warning yok", "no error/warning")}
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium">{T("Önerilen aksiyon", "Suggested action")}</p>
              <p className="text-muted-foreground">
                reject ({T("yüksek güven", "high confidence")}) · warn ({T("sezgisel", "heuristic")}) · fix ({T("otomatik", "auto")})
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Hedef API alanları */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5" /> {T("Hedef API — Gönderim Alanları", "Target API — Submission Fields")}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {T("(gün, vardiya) bazında agrege JSON gövdesi", "Aggregated JSON body per (day, shift)")}
            </p>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-y bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                  <th className="p-2">{T("Alan", "Field")}</th>
                  <th className="p-2">{T("Tip", "Type")}</th>
                  <th className="p-2">{T("Açıklama", "Description")}</th>
                </tr>
              </thead>
              <tbody>
                {API_FIELDS.map((f) => (
                  <tr key={f.field} className="border-b hover:bg-muted/40">
                    <td className="p-2 font-mono text-xs">{f.field}</td>
                    <td className="p-2 font-mono text-xs text-muted-foreground">{f.type}</td>
                    <td className="p-2">{tx(f.desc)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Hata kodları */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TriangleAlert className="h-5 w-5" /> {T("Hedef API — Hata Kodları", "Target API — Error Codes")}
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-y bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                  <th className="p-2">HTTP</th>
                  <th className="p-2">{T("Anlam", "Meaning")}</th>
                </tr>
              </thead>
              <tbody>
                {ERRORS.map((e) => (
                  <tr key={e.code} className="border-b hover:bg-muted/40">
                    <td className="p-2 font-mono font-semibold">{e.code}</td>
                    <td className="p-2">{tx(e.meaning)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="p-3 text-xs text-muted-foreground">
              {T(
                "Retry yalnız 429 (60s cooldown) + 5xx + ağ/timeout için; 401/422/413 kalıcı hatadır.",
                "Retry only for 429 (60s cooldown) + 5xx + network/timeout; 401/422/413 are permanent.",
              )}
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Proje sözlüğü */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" /> {T("Proje Sözlüğü", "Project Glossary")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2">
            {GLOSSARY.map((g) => (
              <div key={g.term} className="border-b pb-2">
                <dt className="font-mono text-sm font-semibold">{g.term}</dt>
                <dd className="text-sm text-muted-foreground">{tx(g.def)}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      {/* Geliştirici / Developer */}
      <footer className="mt-2 flex flex-col items-center gap-2 border-t pt-6 text-center text-sm text-muted-foreground">
        <p>
          {T("Geliştirici", "Developer")}: <span className="font-semibold text-foreground">Umut Arda Özdeş</span>
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="https://github.com/Ardovski"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-foreground hover:underline"
          >
            <Github className="h-4 w-4" /> github.com/Ardovski
          </a>
          <a
            href="https://umutardaozdes.com.tr"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-foreground hover:underline"
          >
            <Globe className="h-4 w-4" /> umutardaozdes.com.tr
          </a>
        </div>
      </footer>
    </main>
  );
}
