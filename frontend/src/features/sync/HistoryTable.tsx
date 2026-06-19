"use client";

import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";

import { useRetryAll, useRetrySync, useSyncHistory } from "./useSync";

function fmtDate(s: string | null): string {
  if (!s) return "—";
  return s.replace("T", " ").slice(0, 19);
}

function statusClass(status: string): string {
  switch (status) {
    case "success":
      return "bg-success text-success-foreground";
    case "failed":
      return "bg-destructive text-destructive-foreground";
    case "retrying":
      return "bg-warning text-warning-foreground";
    default:
      return "bg-muted text-muted-foreground";
  }
}

export function HistoryTable() {
  const t = useT();
  const toast = useToast();
  const history = useSyncHistory();
  const retry = useRetrySync();
  const retryAll = useRetryAll();
  const rows = history.data ?? [];
  // Yeniden denenebilir = başarısız + yeniden deniyor olan gönderimler.
  const retriableCount = rows.filter((s) => s.status === "failed" || s.status === "retrying").length;

  return (
    <section className="overflow-hidden rounded-lg border bg-card text-card-foreground">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b bg-muted/30 p-3">
        <div>
          <h2 className="text-sm font-semibold">{t("sync.historyTable.title")}</h2>
          <p className="text-xs text-muted-foreground">{t("sync.historyTable.autoRefresh")}</p>
        </div>
        <button
          type="button"
          disabled={retriableCount === 0 || retryAll.isPending}
          onClick={() =>
            retryAll.mutate(undefined, {
              onSuccess: (data) =>
                toast.push({
                  tone: "success",
                  title: t("sync.syncPage.retryAllSuccess"),
                  description: t("sync.syncPage.retryAllSuccessDesc", { n: data.queued }),
                }),
              onError: () =>
                toast.push({
                  tone: "destructive",
                  title: t("sync.syncPage.retryAllFailed"),
                }),
            })
          }
          className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50"
        >
          {retryAll.isPending
            ? t("sync.historyTable.retryingAll")
            : t("sync.historyTable.retryAll", { n: retriableCount })}
        </button>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
            <th className="p-2">#</th>
            <th className="p-2">{t("sync.historyTable.colDate")}</th>
            <th className="p-2">{t("sync.historyTable.colShift")}</th>
            <th className="p-2">{t("sync.historyTable.colStatus")}</th>
            <th className="p-2 text-right">HTTP</th>
            <th className="p-2 text-right">{t("sync.historyTable.colAttempts")}</th>
            <th className="p-2">{t("sync.historyTable.colLastAttempt")}</th>
            <th className="p-2">{t("sync.historyTable.colTargetId")}</th>
            <th className="p-2">{t("sync.historyTable.colResponse")}</th>
            <th className="p-2"></th>
          </tr>
        </thead>
        <tbody>
          {history.isLoading ? (
            <tr>
              <td colSpan={10} className="p-4 text-center text-muted-foreground">
                {t("common.loading")}
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={10} className="p-4 text-center text-muted-foreground">
                {t("sync.historyTable.empty")}
              </td>
            </tr>
          ) : (
            rows.map((s) => (
              <tr key={s.id} className="border-b transition-colors hover:bg-muted/50">
                <td className="p-2 font-mono">{s.id}</td>
                <td className="p-2 font-mono">{s.prod_date}</td>
                <td className="p-2">{t(`shift.${s.shift}`)}</td>
                <td className="p-2">
                  <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${statusClass(s.status)}`}>
                    {t(`status.${s.status}`)}
                  </span>
                </td>
                <td className="p-2 text-right tabular-nums">{s.http_status ?? "—"}</td>
                <td className="p-2 text-right tabular-nums">{s.attempts}</td>
                <td className="p-2 font-mono text-xs">{fmtDate(s.last_attempt_at)}</td>
                <td className="p-2 font-mono">{s.target_submission_id ?? "—"}</td>
                <td className="p-2 text-xs text-muted-foreground" title={s.target_message ?? undefined}>
                  {s.target_candidate_name ?? (s.target_message ? "…" : "—")}
                </td>
                <td className="p-2">
                  {s.status === "failed" || s.status === "retrying" ? (
                    (() => {
                      // Pending state'i yalnız tıklanan satıra bağla — aksi halde
                      // tek retry tüm satırların butonunu "…" yapardı.
                      const isThisRetrying = retry.isPending && retry.variables === s.id;
                      return (
                        <button
                          type="button"
                          className="rounded-md border bg-background px-2 py-1 text-xs text-foreground hover:bg-muted disabled:opacity-50"
                          disabled={isThisRetrying}
                          onClick={() =>
                            retry.mutate(s.id, {
                              onSuccess: () =>
                                toast.push({
                                  tone: "success",
                                  title: t("sync.syncPage.retrySuccess"),
                                  description: t("sync.syncPage.retrySuccessDesc", { id: s.id }),
                                }),
                              onError: () =>
                                toast.push({
                                  tone: "destructive",
                                  title: t("sync.syncPage.retryFailed"),
                                }),
                            })
                          }
                        >
                          {isThisRetrying ? "…" : t("common.retry")}
                        </button>
                      );
                    })()
                  ) : null}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
