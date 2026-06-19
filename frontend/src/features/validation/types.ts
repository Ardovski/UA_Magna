export interface ValidationIssue {
  id: number;
  record_id: number;
  rule_id: string;
  category: string;
  severity: string;
  fields: string | null;
  message: string;
  suggested_action: string;
  detected_at: string | null;
  fixed_at: string | null;
  status: string;
}

export interface ValidationSummary {
  total_records: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  by_rule: Record<string, number>;
}

export interface RecordEdit {
  id: number;
  field: string;
  old_value: string | null;
  new_value: string | null;
  reason: string | null;
  edited_by: string;
  edited_at: string | null;
}

/** Backend `RecordDetailOut` — diff editör için tek kaydın tüm alanları.
 *  Backend `RecordOut`'a karşılık gelir; ek olarak `issues` dizisi içerir. */
export interface RecordDetail {
  id: number;
  record_id_src: number | null;
  import_batch_id: number | null;
  prod_date: string | null;
  work_order_no: string | null;
  work_center_no: string | null;
  work_center_name: string | null;
  station_name: string | null;
  stock_name: string | null;
  shift: number | null;
  availability: number | null;
  performance: number | null;
  quality: number | null;
  oee: number | null;
  run_time: number | null;
  down_time: number | null;
  planned_down: number | null;
  unplanned_down: number | null;
  produced_qty: number | null;
  scrap_qty: number | null;
  oee_recomputed: number | null;
  validation_status: string;
  issue_count: number;
  created_at: string | null;
  updated_at: string | null;
  issues: Array<{
    id: number;
    rule_id: string;
    category: string;
    severity: string;
    fields: string | null;
    message: string;
    suggested_action: string;
    status: string;
    detected_at: string | null;
    fixed_at: string | null;
  }>;
}

export interface IssueFilter {
  category?: string;
  severity?: string;
  rule_id?: string;
  record_status?: string;
}
