"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useActiveBatch } from "@/hooks/useActiveBatch";
import { DashboardHeader } from "./DashboardHeader";
import { KpiCardGrid } from "./KpiCardGrid";
import { OeeTrendChart } from "./OeeTrendChart";
import { ProblemShiftsTable } from "./ProblemShiftsTable";
import { QualityDistributionChart } from "./QualityDistributionChart";
import { RecentRecordsTable } from "./RecentRecordsTable";
import { ShiftComparisonChart } from "./ShiftComparisonChart";
import { StationRankingChart } from "./StationRankingChart";
import { TopStationsTable } from "./TopStationsTable";

export function DashboardPage() {
  const active = useActiveBatch();
  const batchId: number | null = active.data?.id ?? null;
  const [tab, setTab] = useState("recent");

  return (
    <main className="container mx-auto space-y-6 py-8">
      <DashboardHeader />

      <KpiCardGrid />

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <OeeTrendChart />
        <ShiftComparisonChart />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <StationRankingChart />
        <QualityDistributionChart />
      </section>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="recent">Son Kayıtlar</TabsTrigger>
          <TabsTrigger value="top">Top İstasyonlar</TabsTrigger>
          <TabsTrigger value="problems">Sorunlu Vardiyalar</TabsTrigger>
        </TabsList>
        <TabsContent value="recent">
          <RecentRecordsTable batchId={batchId} />
        </TabsContent>
        <TabsContent value="top">
          <TopStationsTable batchId={batchId} />
        </TabsContent>
        <TabsContent value="problems">
          <ProblemShiftsTable batchId={batchId} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
