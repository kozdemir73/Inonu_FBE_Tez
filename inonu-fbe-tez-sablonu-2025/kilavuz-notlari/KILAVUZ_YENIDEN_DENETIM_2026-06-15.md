# Kılavuz Yeniden Denetimi

Denetim tarihi: 15.06.2026

Denetlenen yerel kaynaklar:

- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\İnönü Üniversitesi Lisansüstü Tez Yazım Kılavuzu.pdf`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\kilavuz.txt`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\Tez Yazım Kılavuzu öneriler_261225.docx`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\Ek-1-Yüksek Lisans Tez Kapağı.docx`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\Ek-2-Doktora Tez Kapağı.docx`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\Ek-3-APA7 kaynak gösterme.docx`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\Ek-4-İSNAD Atıf Sİistemi.docx`
- `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\İnönü Üniversitesi Fen Bilimleri Enstitüsü Tez Şablonu.docx`
- `D:\Developments\Yeni_Tez_LaTeX\İnönü Üniversitesi Fen Bilimleri Enstitüsü Tez Şablonu.docx`

## Bu Turda Düzeltilenler

1. Sistem sekmesindeki ikinci `Güncelle` düğmesi kaldırıldı. Üst sağdaki ana güncelleme düğmesi korunmuştur.
2. `Tez Bilgileri` içinde `ÜYZ Beyanı` için ayrı bir alt sekme eklendi. Beyan metni doğrudan bu sekmede düzenlenir, `etik-beyan.tex` dosyasına kaydedilir ve sağda önizlenir.
3. Sağdaki önizleme başlığı artık bağlama göre adlandırılır: `Dış Kapak Önizlemesi`, `İç Kapak Önizlemesi`, `Kabul-Onay Önizlemesi`, `ÜYZ Beyanı Önizlemesi`.
4. TeX dosyalarını tanıma penceresinde `Kısaltmalar dizini` ve `Simgeler dizini` ayrı satırlar olmaktan çıkarıldı; kılavuzdaki başlığa uygun olarak `Simgeler ve Kısaltmalar dizini` tek satır yapıldı.
5. Varsayılan `tez.tex`, `simgeler-ve-kisaltmalar.tex` adlı tek dosyayı kullanacak biçimde güncellendi. Eski `kisaltmalar.tex`, `sembol.tex`, `semboller.tex` dosyaları artık kullanılmadığı için kaldırıldı.
6. Dış kapak ve sırt kapak şerit rengi tez türüne bağlandı:
   - Yüksek lisans: turkuaz ton (`0D7C9F` referansına yakın).
   - Doktora: sarı ton (`FFC000` referansına yakın).
7. GUI kapak önizlemesinde de yüksek lisans/doktora şerit rengi ayrımı gösterilir hale getirildi.

## Kılavuzdan Doğrulanan Ana Noktalar

### Simgeler ve Kısaltmalar Dizini

Kılavuz 3.9 bölümü başlığı tekil olarak `SİMGELER VE KISALTMALAR DİZİNİ` biçiminde verir. Bu nedenle GUI'de ve yeni örnek giriş dosyasında tek dizin yaklaşımı doğru kabul edilmiştir.

Durum: LaTeX şablonu ve GUI bu turda uyumlu hale getirildi.

### Dış Kapak Tez Türü

Ana kılavuz dış kapakta şu bilgi grubunu ister:

- Tez konusu
- Yüksek Lisans / Doktora Tezi
- Doctoral Dissertation / Master's Thesis
- Öğrenci isim soyisim
- Şehir / yıl

Bu nedenle dış kapakta ana tez türü Türkçe ve tez türüne bağlı kalmalıdır; İngilizce alt satır ise kılavuz metninde ayrıca istendiği için tamamen kaldırılmamalıdır.

Durum: LaTeX şablonunda ana satır `YÜKSEK LİSANS TEZİ` veya `DOKTORA TEZİ`; alt satır tez türüne göre İngilizce olarak korunmuştur.

### Kapak Şerit Rengi

DOCX eklerinden çıkarılan renkler:

- `Ek-1-Yüksek Lisans Tez Kapağı.docx`: `0D7C9F`
- `Ek-2-Doktora Tez Kapağı.docx`: `FFC000`

Durum: LaTeX dış kapak ve sırt kapak şeridi tez türüne göre renklendirildi.

## Yerel Kılavuz Dosyaları Arasında Not Edilen Tutarsızlıklar

1. Ana kılavuz metni yüksek lisans dış kapak İngilizce alt satırı için `Master's Thesis` ifadesini verirken, `Ek-1-Yüksek Lisans Tez Kapağı.docx` dosyasında `MASTER OF SCIENCE DISSERTATION` ifadesi görülmektedir.

   Geçici karar: Kapak ek dosyası görsel/uygulama örneği olduğu için LaTeX şablonu şimdilik `MASTER OF SCIENCE DISSERTATION` ifadesini korur. Bu ifade Enstitü tarafından netleştirilmelidir.

2. Ana kılavuz metin çıkarımında `Doctoral Dıssertatıon` biçiminde noktasız harfli bir yazım görünüyor. Bu büyük olasılıkla PDF metin çıkarımı/OCR kaynaklıdır; Ek-2 kapak dosyası `DOCTORAL DISSERTATION` yazımını destekler.

   Geçici karar: LaTeX şablonu `DOCTORAL DISSERTATION` kullanır.

## Word Tez Şablonu İçin Ayrı Not

`İnönü Üniversitesi Fen Bilimleri Enstitüsü Tez Şablonu.docx` dosyası genel sayfa düzeni açısından yararlı bir referanstır; ancak kapak renkleri ve kapak örneği bakımından `Ek-1`/`Ek-2` kadar açık veri taşımamaktadır. DOCX içinden okunan renkler kapak şeridi ayrımını göstermemiştir.

Bu nedenle Word şablonu, kapak rengi ve dış kapak uygulaması için birincil kaynak kabul edilmemelidir. Bu alanlarda `Ek-1`, `Ek-2` ve ana kılavuz esas alınmalıdır.

## Performans Notu

GUI duman testinde sekme geçişleri ölçüldü:

- İlk açılış sonrası ilk ölçüm: `Teslim Kontrolü` yaklaşık 10 ms, `Sistem` yaklaşık 5 ms, `TeX ve Yazım` yaklaşık 2 ms.
- Başlangıç görevleri çalıştıktan sonra: `Teslim Kontrolü` yaklaşık 5 ms, `Sistem` yaklaşık 0.4 ms, `TeX ve Yazım` yaklaşık 0.6 ms.

Bu turda ana kaydırma alanının ölçüm/yenileme işi gecikmeli hale getirildi. Gerçek kullanımda kalan kasma olursa en olası kaynak sekme geçişi değil, arka plandaki dosya/TeX/PDF işlemleridir.

## İzlenecek Konular

- `MASTER OF SCIENCE DISSERTATION` ile `Master's Thesis` farkı Enstitü tarafından netleştirilmeli.
- Word şablonu ile LaTeX çıktısının nihai görsel karşılaştırması için Word dosyasından PDF alınarak kapak/iç kapak/onay/etik/dizinler sayfa sayfa karşılaştırılmalı.
- Kapak renklerinin kesin RGB/CMYK değerleri Enstitü kurumsal kimliğiyle ayrıca doğrulanırsa sınıftaki renkler birebir sabitlenebilir.
