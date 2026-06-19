"use client";

import { useEffect, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { useFilterOptions } from "./useRecords";
import { useRecordsFilterStore } from "@/stores/filters";
import { useT } from "@/lib/i18n";

const SHIFT_VALUES = [1, 2, 3] as const;
const STATUS_VALUES = ["valid", "suspect", "rejected"] as const;
const STOCK_NAME_DEBOUNCE_MS = 300;

function toggle<T>(arr: T[], v: T): T[] {
  return arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
}

/** Slider'lar için local visual state + onCommit. Store yalnız bırakınca
 *  güncellenir → useRecords içindeki debounce penceresine girer. */
function OeeSlider({
  label,
  value,
  min,
  max,
  ariaLabel,
  onLocalChange,
  onCommit,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  ariaLabel: string;
  /** Sürüklerken çağrılır (controlled input için state update şart). */
  onLocalChange: (v: number) => void;
  /** Bırakınca (mouseup/touchend/keyup) çağrılır → store update. */
  onCommit: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground">
        {label}: <span className="font-mono text-foreground">{value}</span>
      </label>
      <Slider
        value={value}
        min={min}
        max={max}
        onChange={onLocalChange}
        onCommit={onCommit}
        ariaLabel={ariaLabel}
        className="mt-1"
      />
    </div>
  );
}

export function FilterPanel() {
  const t = useT();
  const filter = useRecordsFilterStore();
  const options = useFilterOptions();
  const toast = useToast();

  // Slider'lar için görsel state (sürüklerken anlık feedback). Store yalnız
  // onCommit'te güncellenir → slider sürükleme boyunca 0 API isteği.
  const [oeeMin, setOeeMin] = useState<number>(filter.oeeRange.min ?? 0);
  const [oeeMax, setOeeMax] = useState<number>(filter.oeeRange.max ?? 100);
  useEffect(() => {
    setOeeMin(filter.oeeRange.min ?? 0);
    setOeeMax(filter.oeeRange.max ?? 100);
  }, [filter.oeeRange.min, filter.oeeRange.max]);

  // Stock name: local state + 300ms debounce → store update. Tuş başına
  // istek yok; 300ms sessizlik sonrası 1 istek.
  const [stockInput, setStockInput] = useState<string>(filter.stockName ?? "");
  useEffect(() => {
    setStockInput(filter.stockName ?? "");
  }, [filter.stockName]);
  useEffect(() => {
    const id = setTimeout(() => {
      const next = stockInput.trim() === "" ? null : stockInput;
      if (next !== filter.stockName) filter.setStockName(next);
    }, STOCK_NAME_DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [stockInput, filter]);

  const onReset = () => {
    filter.reset();
    toast.push({ tone: "default", title: t("records.toast.filterReset") });
  };

  return (
    <aside className="space-y-4 rounded-lg border bg-card p-4 text-card-foreground">
      <h2 className="text-sm font-medium text-muted-foreground">
        {t("records.filterPanel.title")}
      </h2>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-muted-foreground">
            {t("records.filterPanel.startDate")}
          </label>
          <Input
            type="date"
            value={filter.dateRange.start ?? ""}
            onChange={(e) =>
              filter.setDateRange({ ...filter.dateRange, start: e.target.value || null })
            }
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted-foreground">
            {t("records.filterPanel.endDate")}
          </label>
          <Input
            type="date"
            value={filter.dateRange.end ?? ""}
            onChange={(e) =>
              filter.setDateRange({ ...filter.dateRange, end: e.target.value || null })
            }
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground">
          {t("records.filterPanel.shift")}
        </label>
        <div className="mt-1 flex gap-2">
          {SHIFT_VALUES.map((value) => (
            <Checkbox
              key={value}
              checked={filter.shifts.includes(value)}
              onChange={() => filter.setShifts(toggle(filter.shifts, value))}
              label={t(`shift.${value}`)}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground">
          {t("records.filterPanel.station")}
        </label>
        <Select
          multiple
          value={filter.stations}
          onChange={(e) =>
            filter.setStations(Array.from(e.target.selectedOptions).map((o) => o.value))
          }
          className="h-24"
        >
          {(options.data?.stations ?? []).map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground">
          {t("records.filterPanel.stockName")}
        </label>
        <Input
          type="text"
          value={stockInput}
          onChange={(e) => setStockInput(e.target.value)}
          placeholder={t("records.filterPanel.stockName")}
        />
        <p className="mt-1 text-[10px] text-muted-foreground">
          {STOCK_NAME_DEBOUNCE_MS}ms debounce
        </p>
      </div>

      <OeeSlider
        label={t("records.filterPanel.oeeMin", { n: oeeMin })}
        value={oeeMin}
        min={0}
        max={100}
        ariaLabel="OEE minimum"
        onLocalChange={setOeeMin}
        onCommit={(v) =>
          filter.setOeeRange({ ...filter.oeeRange, min: v === 0 ? null : v })
        }
      />
      <OeeSlider
        label={t("records.filterPanel.oeeMax", { n: oeeMax })}
        value={oeeMax}
        min={0}
        max={100}
        ariaLabel="OEE maximum"
        onLocalChange={setOeeMax}
        onCommit={(v) =>
          filter.setOeeRange({ ...filter.oeeRange, max: v === 100 ? null : v })
        }
      />

      <div>
        <label className="block text-xs font-medium text-muted-foreground">
          {t("records.filterPanel.validationStatus")}
        </label>
        <div className="mt-1 flex flex-wrap gap-2">
          {STATUS_VALUES.map((value) => (
            <Checkbox
              key={value}
              checked={filter.validationStatus.includes(value)}
              onChange={() =>
                filter.setValidationStatus(toggle(filter.validationStatus, value))
              }
              label={t(`status.${value}`)}
            />
          ))}
        </div>
      </div>

      <div>
        <Checkbox
          checked={filter.onlyProblematic}
          onChange={(v) => filter.setOnlyProblematic(v)}
          label={t("records.filterPanel.onlyProblematic")}
        />
      </div>

      <Button variant="outline" size="sm" onClick={onReset}>
        {t("records.filterPanel.reset")}
      </Button>
    </aside>
  );
}
