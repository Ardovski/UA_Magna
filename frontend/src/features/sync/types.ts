export interface SyncGroupPreview {
  production_date: string;
  shift: number;
  machine_count: number;
  total_production_units: number;
  oe_value: number | null;
  idempotency_key: string;
  payload_hash: string;
  source_record_count: number;
  /** Hedef API constraint'lerine uygunluk (case §5.5): oe_value aralık, makine/üretim
   * limitleri, gelecek tarih. Uyumsuz gruplar gönderilmez; UI'da badge ile gösterilir. */
  target_valid: boolean;
  /** Uyumsuzluk varsa sebep(ler)i — açıklayıcı tooltip/metin için. */
  target_issues: string[];
}

export interface SyncPreview {
  groups: SyncGroupPreview[];
  total_groups: number;
  /** Hedef API'ye gönderilemeyecek (target_valid=false) grup sayısı — banner özeti. */
  not_target_compliant_count: number;
}

export interface SubmissionOut {
  id: number;
  prod_date: string;
  shift: number;
  idempotency_key: string;
  payload_hash: string;
  status: string;
  http_status: number | null;
  target_submission_id: number | null;
  /** Hedef API'nin başarılı yanıtından (case §5.5) yakalanan ek alanlar. */
  target_candidate_name: string | null;
  target_message: string | null;
  target_submitted_at: string | null;
  attempts: number;
  last_attempt_at: string | null;
  created_at: string | null;
  error_message: string | null;
  response_body: string | null;
}

/** UI'da seçilen tek bir (gün, vardiya) grubu — `SubmitRequest.targets` elemanı. */
export interface SubmitTarget {
  production_date: string;
  shift: number;
}

export interface SubmitRequest {
  production_date?: string | null;
  shift?: number | null;
  /** Çoklu seçim: doluysa yalnız bu grup(lar) gönderilir (boşsa eski tek/all davranışı). */
  targets?: SubmitTarget[];
  force?: boolean;
}

export interface SubmitResponse {
  accepted: string[];
  skipped_already_success: string[];
  /** Aynı idempotency_key + farklı payload_hash → güvenlik için reddedildi (force ile geçilebilir). */
  rejected_due_to_hash_conflict: string[];
  /** Hedef API constraint ihlali (oe_value/makine/üretim limiti, gelecek tarih) — payload
   * hiç oluşturulmaz. Veri düzeltilmeden gönderilemez. */
  rejected_target_constraints: string[];
  submission_ids: number[];
}
