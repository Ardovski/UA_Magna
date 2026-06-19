# `components/organisms/`

Bir sayfanın bağımsız parçası olan, atom+molecule birleşiminden oluşan tam
bileşenler. Genellikle uygulama kabuğu, başlık, tablo kabuğu gibi **kendi başına
anlamlı** birimlerdir.

- `components/atoms/` + `components/molecules/` + `components/ui/` + `lib/`
  + `hooks/` + `stores/` import edebilir.
- Feature'ları import etmez (ters yön).
- Network çağrısı yapan organism'ler hook kullanır (`useActiveBatch` vb.); doğrudan
  fetch yapmaz.
