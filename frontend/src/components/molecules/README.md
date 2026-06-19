# `components/molecules/`

2+ atom veya shadcn primitive'inden oluşan, **tek bir UI işi** yapan küçük
birimler. Domain bağımsız (örn. `SummaryCard` OEE'ye özel değil; KPI/istatistik
gösterimi için jenerik). `components/atoms/` ve `components/ui/` üstüne kurulur.

- Hiçbir feature'ı import etmez.
- Hiçbir organism import etmez.
- Network çağrısı yapmaz; sunum + minimal yerel state (örn. controlled input).

Kullanım: organism'ler veya feature sayfaları tarafından birleştirilir.
