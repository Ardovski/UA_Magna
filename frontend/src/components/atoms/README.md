# `components/atoms/`

En küçük, tek sorumluluğa sahip, bağımsız UI birimleri. shadcn primitive'leri
(`components/ui/`) üstüne inşa edilir; **yalnızca** `components/ui/` ve `lib/`
kullanır.

- Hiçbir feature'ı import etmez.
- Hiçbir molecule/organism import etmez.
- Yalnız sunum: state yok, network yok, side-effect yok.

Kullanım: `SummaryCard`, `Badge`, `EmptyState` gibi parçaları bir molecule/organism
içinde birleştir.
