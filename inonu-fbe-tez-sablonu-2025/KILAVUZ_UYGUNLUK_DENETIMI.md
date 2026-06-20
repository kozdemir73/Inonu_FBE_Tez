# Inonu FBE 2025 Kılavuzuna Uygunluk Denetimi

Denetim tarihi: 12.06.2026

Denetlenen kaynaklar:

- Kılavuz: `D:\Developments\Yeni_Tez_LaTeX\Tez Yazım Kılavuzu\İnönü Üniversitesi Lisansüstü Tez Yazım Kılavuzu.pdf`
- Şablon: `tez.tex`, `inonutez.cls`, `defs.tex`
- Güncel çıktı: `tez.pdf`

Kullanılan kontroller:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\kontrol.ps1`
- `pdfinfo tez.pdf`
- `pdffonts tez.pdf`
- `pdftotext -layout -enc UTF-8 tez.pdf`
- `pdftotext -bbox-layout -enc UTF-8 tez.pdf`
- TeX kaynaklarında elle/regex tabanlı tarama

## Özet Karar

Bu turda kullanıcı kararı gereği iki konuya müdahale edilmedi:

- Matematik için numaralı kaynak gösterimi: `num` korunmuştur.
- Dış kapak başlık/tez türü punto esnekliği: uzun başlıklarda taşma riskini azaltmak için mevcut esnek düzen korunmuştur.

Bu iki konu Enstitü Yönetim Kurulu değerlendirmesine bırakılmış bilinçli istisna olarak izlenmelidir.

Bunların dışındaki başlıca kılavuz uyumsuzlukları giderildi. Güncel otomatik kontrol sonucu `0 FAIL, 5 UYARI, 4 MANUEL` durumundadır. Kalan uyarıların çoğu örnek içerik, kullanılmayan kaynak kayıtları, anılmayan örnek etiketler ve danışman/enstitü tarafından elle doğrulanması gereken resmi bilgilerle ilgilidir.

## Güncel Olarak Uyumlu Hale Getirilen Alanlar

### 1. Dördüncü derece başlıklar

2025 kılavuzu, üçüncü dereceden ileri başlıkların zorunlu olmadıkça kullanılmamasını; kullanılırsa numarasız ve içindekiler dışında kalmasını ister.

Güncelleme:

- `\subsubsection{...}` artık numaralı `4.1.2.1` gibi görünmez.
- `\subsubsection{...}` içindekilere yazılmaz.
- `\subsubsubsection{...}` zaten numarasız yardımcı başlık davranışını korur.

Doğrulama:

- Güncel `tez.toc` içinde `subsubsection` satırı kalmadı.
- Güncel PDF metninde `\d+.\d+.\d+.\d+` kalıbı bulunmadı.

Durum: OK

### 2. Ek başlıkları

Kılavuz 4.9, her ekin ayrı sayfada ve sayfa başı sol üstte `EK-1`, `EK-2` biçiminde verilmesini ister.

Güncelleme:

- Ek başlıkları merkezli ana bölüm başlığı gibi değil, sol üstte basılacak şekilde sınıf davranışı değiştirildi.
- `EKLER` ana kapak sayfası korunur; tek tek ekler sol üst yerleşimdedir.

Doğrulama:

- Güncel PDF metninde `EK-1 Özgeçmiş` ek sayfasında sol üstten başlamaktadır.

Durum: OK

### 3. Sayfa üst/alt metin alanı

Kılavuz sayfa kenarlarında 2,5 cm boşluk ister.

Güncelleme:

- `topmargin` 2,5 cm metin başlangıcıyla uyumlu hale getirildi.
- Ana başlık üst boşluğu `0mm` yapıldı; başlıklar sayfanın metin alanı üst satırında başlıyor.
- Metin yüksekliği 245 mm yapılarak alt boşluk için güvenli pay bırakıldı.

Doğrulama:

- `pdftotext -bbox-layout` ölçümünde metin alanı için 2,5 cm sınırını aşan sayfa kalmadı.

Durum: OK

### 4. PDF karakter bozulması kontrolü

Önceki kontrolde Türkçede geçerli `Â` karakteri, örneğin `ZEKÂ`, yanlışlıkla bozulma belirtisi sayılabiliyordu.

Güncelleme:

- `kontrol.ps1` ve yazım denetimi tarafında `Â` tek başına mojibake belirtisi olmaktan çıkarıldı.
- `pdftotext` çıktısı UTF-8 geçici dosyadan okunacak hale getirildi.

Doğrulama:

- Güncel kontrol: `PDF metninde yaygın karakter bozulması işareti görünmedi.`

Durum: OK

### 5. Örnek içerik ve önizleme

Güncel örnek PDF daha önce boş başlık, boş anahtar kelime ve kapak şehri gibi alanlar üretiyordu.

Güncelleme:

- Örnek başlık, anabilim dalı, program, danışman, şehir/yıl, karar bilgisi ve anahtar kelime alanları şablon önizlemesini anlaşılır kılacak biçimde dolduruldu.
- Örnek tablolardaki `Satı r` yazımları `Satır` olarak düzeltildi.
- Sırt kapak bilgileri ana `tez.tex` ile eşitlendi.

Durum: OK

## Bilinçli İstisnalar

### Kaynak gösterimi

Kılavuz genel olarak APA 7 ister. Ancak Matematik alanı için kullanıcı tarafından belirtilen istisna nedeniyle `num` korunmuştur.

Durum: Karar bekliyor

### Dış kapak punto esnekliği

Kılavuzdaki dış kapak punto değerleri uzun başlıklarda taşma riski oluşturduğu için mevcut esnek düzen korunmuştur.

Durum: Karar bekliyor

## Kalan Uyarılar

- LaTeX logunda küçük yerleşim uyarıları var; derleme başarılıdır. Son ölçümde kılavuz kenar boşluğu ihlali görülmedi.
- `tez.tex:78` satırında örnek İngilizce danışman adı `Prof. Dr. Name SURNAME` olarak kalıyor; bu bir şablon örneğidir ve gerçek tezde GUI/form üzerinden değiştirilecektir.
- Örnek `kaynaklar.bib` içinde metinde atıf verilmeyen kayıtlar var; gerçek tezde kaynakça temizlenmelidir.
- Bazı örnek şekil/tablo/denklem etiketleri metinde anılmıyor; örnek içerik temizlenirken ele alınmalıdır.
- Jüri, tarih, karar numarası, etik/yapay zeka beyanı ve uzun başlık taşması son PDF üzerinde danışman/enstitü bilgileriyle elle doğrulanmalıdır.

## Word Şablonu Karşılaştırması

Word şablonu ile ilk teknik karşılaştırma ayrıca kaydedildi:

- `WORD_SABLON_KARSILASTIRMA.md`

İlk sonuç: Word şablonu sayfa ölçüleri bakımından güçlü bir referanstır; ancak bazı metin/stil notları 2025 kılavuzuyla çelişen eski izler taşır. Bu nedenle LaTeX şablonu birebir Word dosyasını değil, öncelikle 2025 Tez Yazım Kılavuzu'nu izlemelidir.
