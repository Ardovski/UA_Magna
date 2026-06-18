"use client";

import { useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { Inbox } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { oeeColorClass } from "@/lib/utils";
import { useTopStations } from "./useDashboardData";
import type { TopStationRow } from "./types";

const fmtNum = (n: number | null | undefined): string =>
  n === null || n === undefined ? "—" : n.toLocaleString("tr-TR");

export interface TopStationsTableProps {
  batchId: number | null;
}

export function TopStationsTable({ batchId }: TopStationsTableProps) {
  const q = useTopStations(batchId, 10);
  const [sorting, setSorting] = useState<SortingState>([]);
  const data = q.data ?? [];

  const columns = useMemo<ColumnDef<TopStationRow>[]>(
    () => [
      {
        accessorKey: "station_name",
        header: "İstasyon",
        cell: (info) => (
          <span className="font-medium">{info.getValue<string>()}</span>
        ),
      },
      {
        accessorKey: "avg_oee",
        header: "OEE",
        cell: (info) => {
          const v = info.getValue<number | null>();
          return v === null ? (
            "—"
          ) : (
            <span className={`tabular-nums ${oeeColorClass(v)}`}>{v.toFixed(1)}%</span>
          );
        },
      },
      {
        accessorKey: "total_production",
        header: "Üretim",
        cell: (info) => (
          <span className="tabular-nums">{fmtNum(info.getValue<number>())}</span>
        ),
      },
      {
        accessorKey: "total_scrap",
        header: "Fire",
        cell: (info) => {
          const v = info.getValue<number>();
          return (
            <span className={`tabular-nums ${v > 0 ? "text-oee-low" : ""}`}>
              {fmtNum(v)}
            </span>
          );
        },
      },
      {
        accessorKey: "record_count",
        header: "Kayıt",
        cell: (info) => (
          <span className="tabular-nums text-muted-foreground">
            {fmtNum(info.getValue<number>())}
          </span>
        ),
      },
    ],
    [],
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="overflow-hidden rounded-lg border bg-card text-card-foreground">
      <table className="w-full text-sm">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr
              key={hg.id}
              className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground"
            >
              {hg.headers.map((h) => (
                <th
                  key={h.id}
                  className="cursor-pointer select-none p-2"
                  onClick={h.column.getToggleSortingHandler()}
                >
                  {flexRender(h.column.columnDef.header, h.getContext())}
                  {h.column.getIsSorted() === "asc"
                    ? " ▲"
                    : h.column.getIsSorted() === "desc"
                      ? " ▼"
                      : ""}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {q.isLoading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <tr key={`s_${i}`} className="border-b">
                <td colSpan={columns.length} className="p-2">
                  <Skeleton className="h-6 w-full" />
                </td>
              </tr>
            ))
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="p-8">
                <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
                  <Inbox className="h-8 w-8 opacity-60" />
                  <p>Veri yok</p>
                </div>
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b transition-colors hover:bg-muted/40">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="p-2 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
