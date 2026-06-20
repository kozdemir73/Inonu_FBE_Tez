# Word Şablonu ile LaTeX Şablonu İlk Uyumluluk Karşılaştırması

Karşılaştırma tarihi: 12.06.2026

Karşılaştırılan dosyalar:

- Word şablonu: `D:\Developments\Yeni_Tez_LaTeX\İnönü Üniversitesi Fen Bilimleri Enstitüsü Tez Şablonu.docx`
- LaTeX şablonu: `D:\Developments\Yeni_Tez_LaTeX\Inonu_FBE_Tez\inonu-fbe-tez-sablonu-2025`
- LaTeX çıktısı: `tez.pdf`

Bu ilk karşılaştırma DOCX dosyasının XML içeriği, stil tanımları ve LaTeX PDF çıktısı üzerinden yapılmıştır. Nihai görsel eşleşme için Word şablonundan PDF çıktısı alınarak sayfa sayfa görsel karşılaştırma yapılması ayrıca önerilir.

## Word Şablonundan Okunan Temel Sayfa Ayarları

DOCX bölüm ayarları:

- Sayfa genişliği: 21,003 cm
- Sayfa yüksekliği: 29,704 cm
- Üst boşluk: 2,501 cm
- Sağ boşluk: 2,501 cm
- Alt boşluk: 2,501 cm
- Sol boşluk: 2,501 cm
- Üstbilgi: 1,251 cm
- Altbilgi: 1,251 cm
- Cilt payı: 0 cm

LaTeX şablonu güncel durumda A4 ve 2,5 cm metin alanı kuralıyla uyumludur. `pdftotext -bbox-layout` ölçümünde metin alanı için 2,5 cm sınırını aşan sayfa kalmamıştır.

## Güçlü Uyum Alanları

- Her iki şablonda A4 sayfa düzeni ve 2,5 cm kenar boşlukları hedefleniyor.
- Kapak, iç kapak, kabul-onay, etik beyan, içindekiler, özet/abstract, dizinler, kaynaklar ve ekler gibi ana bloklar iki şablonda da var.
- Word şablonunda ana başlık stili 14 punto kalın ve ortalı; LaTeX şablonunda ana başlıklar 14 punto kalın ve ortalı basılıyor.
- Word şablonunda gövde stilleri genel olarak 1,5 satır aralığına karşılık gelen `360` line değeri taşıyor; LaTeX şablonu ana metinde 1,5 satır aralığı kullanıyor.
- Word şablonu şekil/tablo/dizin otomatik alan mantığını vurguluyor; LaTeX şablonu bunu otomatik `\caption`, `\listoffigures`, `\listoftables` ile sağlıyor.
- LaTeX şablonunda 2025 kılavuzuna uygun olarak `SİMGELER VE KISALTMALAR DİZİNİ` birleşik başlık halinde üretiliyor.

## Farklar ve Notlar

### 1. Kaynak/atıf stili

Word şablonunda APA vurgusu var; ayrıca örnek metinde numaralı atıf örnekleri de bulunuyor. LaTeX şablonunda Matematik alanı için `num` stili korunmuştur.

Bu konu kullanıcı kararı gereği değiştirilmemiştir; Enstitü Yönetim Kurulu değerlendirmesine bırakılan istisna olarak izlenmelidir.

### 2. Dış kapak başlık puntosu

Word/kılavuz çizgisi dış kapakta yüksek puntoları işaret ediyor; LaTeX şablonunda uzun başlıklarda taşma riskini azaltmak için başlık/tez türü puntoları bilinçli olarak daha esnek tutulmuştur.

Bu konu kullanıcı kararı gereği değiştirilmemiştir; Enstitü Yönetim Kurulu değerlendirmesine bırakılan istisna olarak izlenmelidir.

### 3. Etik beyan başlığı

Word şablonunda `ETİK VE YAPAY ZEKÂ KULLANIM BEYANI` ifadesi görülüyor. 2025 kılavuzunda ise başlık `Etik ve Üretken Yapay Zekâ Beyanı` biçimindedir. LaTeX şablonu `ETİK VE ÜRETKEN YAPAY ZEKÂ BEYANI` kullandığı için güncel kılavuza daha yakındır.

Durum: LaTeX tercih edilmeli.

### 4. Tablo / Çizelge dili

Word şablonunda bazı yerlerde `Çizelge` kullanımı ve `Çizelge A.1` gibi örnekler bulunuyor. 2025 kılavuzu şekil dışındaki tablo düzenini `Tablo` başlığıyla açıklıyor ve örnekleri `Tablo` olarak veriyor. LaTeX şablonu `Tablo` kullanıyor.

Durum: LaTeX güncel kılavuza daha yakın.

### 5. Eklerin içindekilerde gösterimi

Word şablonunda `Ek alt bölümlerinin isimleri EKLER ana başlığında listelenir. Fakat tezin başındaki içindekiler listesinde yazılmaz.` anlamında bir not bulunuyor. 2025 kılavuzu ise eklerin içindekiler sayfasında sayfa numaralarıyla yazılmasını ister.

LaTeX şablonu güncel kılavuzu izleyerek `EKLER`, `EK-1`, `EK-2`, `EK-3` satırlarını içindekilere alıyor.

Durum: LaTeX güncel kılavuza daha yakın.

### 6. Ek başlığı yerleşimi

Word şablonu ekler bölümünde sol üst yerleşimi tarif ediyor. LaTeX şablonu bu turda güncellendi: ek başlıkları artık merkezli bölüm başlığı gibi değil, sayfa başında sol üstte `EK-1 ...` biçiminde basılıyor.

Durum: Uyumlu hale getirildi.

### 7. Dördüncü düzey başlıklar

Word şablonunda `toc 4` stili mevcut olsa da 2025 kılavuzu üçüncü dereceden ileri başlıkların içindekilerde gösterilmemesini ve zorunlu ise numarasız kullanılmasını ister. LaTeX şablonu bu turda güncellendi: `\subsubsection` çıktısı numarasız yardımcı başlık gibi basılır ve içindekilere alınmaz.

Durum: Uyumlu hale getirildi.

### 8. Paragraf boşlukları

Word şablonunda `GOVDE` stilinde satır aralığı 1,5 olmakla birlikte bazı `before/after` boşluk değerleri görülüyor. 2025 kılavuzu paragraflar arasında ilave boşluk bırakılmamasını ister. LaTeX şablonunda `\parskip` sıfırdır ve paragraf girintisi 1,25 cm olarak ayarlanmıştır.

Durum: LaTeX güncel kılavuza daha yakın.

### 9. Kaynaklar satır aralığı

Word şablonunda kaynaklar için `Bu bölüm 1 satır aralıklı olarak yazılır` notu görülüyor. 2025 kılavuzu kaynakçada 11 punto, Calibri ve 1,5 satır aralığı ister. LaTeX şablonu kaynakça bölümünde 1,5 satır aralığını hedefler.

Durum: LaTeX güncel kılavuza daha yakın.

## Karşılaştırma Sonucu

Word şablonu sayfa ölçüleri ve genel bölüm organizasyonu açısından değerli bir referans olmaya devam ediyor. Ancak içeriğinde eski şablondan kalmış veya 2025 kılavuzuyla çelişebilecek notlar var. Bu nedenle LaTeX şablonu birebir Word şablonunu değil, öncelikle 2025 Tez Yazım Kılavuzu'nu izlemelidir.

Bu turdaki LaTeX güncellemeleri Word şablonunun güncel kılavuzla uyumlu taraflarını korur; Word şablonunda kılavuzla çelişen alanlarda ise 2025 kılavuzunu esas alır.

## Sonraki Karşılaştırma Önerisi

1. Word şablonundan aynı örnek bilgilerle PDF çıktısı alınmalı.
2. Word PDF ve LaTeX PDF kapak, iç kapak, onay, etik beyan, içindekiler, özet, dizinler, kaynaklar ve ekler bazında yan yana görsel karşılaştırılmalı.
3. Farklar `kılavuz`, `Word şablonu`, `LaTeX şablonu`, `karar gerekli` sütunlarıyla tabloya dökülmeli.
