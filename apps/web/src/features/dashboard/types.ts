export interface KpiCards {
  avg_oee: number | null;
  total_production: number;
  total_scrap: number;
  total_down_time_minutes: number;
  record_count: number;
  valid_count: number;
  suspect_count: number;
  rejected_count: number;
}

export interface OeeTrendPoint {
  prod_date: string;
  avg_oee: number | null;
  total_production: number;
  record_count: number;
}

export interface ShiftComparisonRow {
  shift: number;
  avg_oee: number | null;
  total_production: number;
  total_scrap: number;
  record_count: number;
}

export interface StationRankingRow {
  station_name: string;
  avg_oee: number | null;
  total_production: number;
  record_count: number;
}

export interface QualityDistributionBucket {
  bucket_label: string;
  bucket_start: number;
  bucket_end: number;
  record_count: number;
  total_scrap: number;
}

export interface RecentRecordRow {
  id: number;
  prod_date: string | null;
  shift: number | null;
  station_name: string | null;
  stock_name: string | null;
  oee: number | null;
  produced_qty: number | null;
  scrap_qty: number | null;
  status: string;
  created_at: string | null;
}

export interface TopStationRow {
  station_name: string;
  avg_oee: number | null;
  total_production: number;
  total_scrap: number;
  record_count: number;
}

export interface ProblemShiftRow {
  prod_date: string | null;
  shift: number;
  station_name: string | null;
  avg_oee: number | null;
  rejected_count: number;
  total_production: number;
  record_count: number;
}
