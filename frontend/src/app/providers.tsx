"use client";

import {
  QueryCache,
  QueryClient,
  QueryClientProvider,
  MutationCache,
  type QueryClientConfig,
} from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useEffect, useState } from "react";
import { ToastProvider, Toaster, useToast, type Toast } from "@/components/ui/toast";
import { LocaleProvider, useT } from "@/lib/i18n";
import { ApiError } from "@/lib/api";

/**
 * Provider sıralaması (dıştan içe):
 *   ThemeProvider → LocaleProvider → QueryClientProvider → ToastProvider → Toaster
 *
 * Theme/Locale en dışta çünkü SSR'da değişmezler; Query + Toast içeride.
 * ToastProvider QueryClientProvider'ın İÇİNDE — global error bridge'in
 * useToast() çağırabilmesi için.
 */

type ToastSink = (t: Omit<Toast, "id">) => void;

let toastSink: ToastSink | null = null;
function setToastSink(fn: ToastSink | null) {
  toastSink = fn;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <LocaleProvider>
        <QueryProvider>{children}</QueryProvider>
      </LocaleProvider>
    </ThemeProvider>
  );
}

function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState<QueryClient>(() => buildQueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ToastBridge>{children}</ToastBridge>
      </ToastProvider>
    </QueryClientProvider>
  );
}

/** QueryClient. staleTime 60s + gcTime 5dk ile scroll/refocus refetch'i minimuma
 *  iner; refetchOnWindowFocus false (tab değiştirince patlamaz); global hata
 *  yakalayıcılar Query/Mutation cache üzerinde. */
function buildQueryClient(): QueryClient {
  const cfg: QueryClientConfig = {
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        gcTime: 5 * 60_000,
        retry: 1,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: { retry: 0 },
    },
    queryCache: new QueryCache({
      onError: (err) => emitGlobalError(err, "query"),
    }),
    mutationCache: new MutationCache({
      onError: (err) => emitGlobalError(err, "mutation"),
    }),
  };
  return new QueryClient(cfg);
}

function emitGlobalError(err: unknown, _kind: "query" | "mutation") {
  if (!toastSink) return; // bridge henüz mount olmadı (SSR) — sessizce atla
  toastSink({
    tone: "destructive",
    title: friendlyTitle(),
    description: friendlyMessage(err),
  });
}

function friendlyTitle(): string {
  return "Hata";
}

function friendlyMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return "Ağ hatası — backend'e ulaşılamıyor.";
    if (err.status === 401) return "Yetkisiz (401).";
    if (err.status === 403) return "Erişim reddedildi (403).";
    if (err.status === 404) return "Bulunamadı (404).";
    if (err.status === 422) return err.message || "Geçersiz istek (422).";
    if (err.status === 429) return "Çok fazla istek (429) — biraz bekleyin.";
    if (err.status >= 500) return `Sunucu hatası (${err.status}).`;
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Beklenmeyen hata.";
}

/** ToastProvider içinde Toaster'ı mount eder ve QueryClient error handler'larını
 *  bu provider'ın toast sink'ine bağlar. Hook'lar güvenli context'te çalışır. */
function ToastBridge({ children }: { children: React.ReactNode }) {
  const toast = useToast();
  const t = useT();
  useEffect(() => {
    setToastSink((toastOpts) =>
      toast.push({
        ...toastOpts,
        title: toastOpts.title ?? t("toast.errorTitle"),
      }),
    );
    return () => setToastSink(null);
  }, [toast, t]);
  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
