# Yapılan güncellemeler

- Dış kapak Word şablonundaki sıraya yaklaştırıldı: logo/T.C./üniversite/enstitü, 3 satırlı tez başlığı, öğrenci adı, ana bilim dalı, tez türü ve altta renkli şerit.
- Şerit içindeki `MALATYA, 2025` metni dikey olarak ortalandı.
- İç kapak Word şablonundaki içerik ve sıralamaya göre düzenlendi.
- `Eş Danışman` yerine `İkinci Tez Danışmanı` terminolojisi eklendi. Eski `\esdanismani` komutları geriye dönük uyumluluk için korunurken yeni `\ikincitezdanismani` komutları eklendi.
- Program alanı boşsa veya Ana Bilim Dalı ile aynı kabul ediliyorsa PDF'de gösterilmemesi için GUI tarafına karşılaştırma mantığı eklendi.
- Kabul-Onay sayfası Word/kabul-onay düzenine yaklaştırıldı; doktora için 5, yüksek lisans için 3 jüri satırı basılır.
- Etik ve Yapay Zekâ Kullanım Beyanı sayfası Word şablonundaki metne göre yeniden üretildi.
- GUI'de Yapay Zekâ kullanımı için `Kullanılmadı` / `Kullanıldı - tablo doldur` seçimi ve tablo alanları eklendi.

Not: LaTeX sınıfı bir test dosyası ile xelatex altında derleme kontrolünden geçirildi. Test ortamında orijinal şablondaki `includex.sty` paketi bulunmadığı için derleme testinde dummy paket kullanıldı; sizin mevcut proje klasörünüzde bu dosya zaten varsa ayrıca işlem gerekmez.
