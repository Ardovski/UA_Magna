/** Uygulama navigasyonu — tek kaynak (Header kullanır). */

export interface NavItem {
  href: string;
  label: string;
  description: string;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Import", description: "CSV yükle" },
  { href: "/dashboard", label: "Dashboard", description: "KPI + grafikler" },
  { href: "/validation", label: "Validation", description: "Issue yönetimi" },
  { href: "/records", label: "Records", description: "Filtreli tablo" },
  { href: "/sync", label: "Sync", description: "Hedef API" },
];

/** Aktif route eşleşmesi — "/" sadece tam eşleşir, diğerleri prefix. */
export function isActivePath(href: string, pathname: string | null): boolean {
  if (!pathname) return false;
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
