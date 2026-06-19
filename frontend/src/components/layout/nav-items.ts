/** Uygulama navigasyonu — tek kaynak (Header kullanır). */

export interface NavItem {
  href: string;
  /** i18n anahtarları (messages.ts: `nav.*`). Etiket Header'da `t(labelKey)` ile çözülür. */
  labelKey: string;
  descKey: string;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", labelKey: "nav.import", descKey: "nav.import.desc" },
  { href: "/dashboard", labelKey: "nav.dashboard", descKey: "nav.dashboard.desc" },
  { href: "/validation", labelKey: "nav.validation", descKey: "nav.validation.desc" },
  { href: "/records", labelKey: "nav.records", descKey: "nav.records.desc" },
  { href: "/sync", labelKey: "nav.sync", descKey: "nav.sync.desc" },
  { href: "/definitions", labelKey: "nav.definitions", descKey: "nav.definitions.desc" },
];

/** Aktif route eşleşmesi — "/" sadece tam eşleşir, diğerleri prefix. */
export function isActivePath(href: string, pathname: string | null): boolean {
  if (!pathname) return false;
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
