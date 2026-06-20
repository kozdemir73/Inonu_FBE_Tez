# Inonu FBE 2025 Uygunluk Notlari

Bu dosya sablonun 2025 Inonu Universitesi Fen Bilimleri Enstitusu tez yazim
kilavuzuna gore hangi noktalari otomatik urettigini ve teslim oncesinde hangi
noktalarin gercek tez PDF'i uzerinden kontrol edilmesi gerektigini ozetler.

## Sablonda Otomatik Ayarlananlar

- Dis kapak Ek-1/Ek-2 duzenine gore FBE amblemi, universite/enstitu adi, tez
  basligi, tez turu, ogrenci adi ve `MALATYA, 2025` alt bandi ile uretilir.
- Ic kapakta anabilim dali, program, ogrenci numarasi ve danisman bilgileri
  yer alir.
- `yukseklisans` ve `doktora` sinif secenekleri tez turu metinlerini ayirir.
- `sirt-kapak.tex`, cilt/sirt kapagi icin ana tezden ayri tek sayfalik PDF
  uretir.
- Kabul ve onay, etik/uretken yapay zeka beyan sayfasi, ozet/abstract, dizinler,
  kaynakca, ekler ve ozgecmis akisi 2025 kilavuzuna gore duzenlenmistir.
- Dipnotlar 10 punto, sekil/tablo notlari 9 punto, kaynakca 11 punto olarak
  ayarlanmistir.
- XeLaTeX ile sistemde varsa Calibri kullanilir; bulunamazsa Carlito'ya geri
  donulur. Calibri hedefi nedeniyle pdfLaTeX/PDFTeXify yolu sablonda
  onerilmez.

## Teslim Oncesi Manuel Kontrol Edilecekler

- Gercek tez basligi uzunluguna gore dis kapak, ic kapak ve sirt kapakta satir
  tasmasi olmadigi PDF uzerinden kontrol edilmelidir.
- Ozet ve abstract metinlerinin 250 kelime sinirini, anahtar kelime kurallarini
  ve kaynak/sekil/tablo kullanmama kuralini sagladigi kontrol edilmelidir.
- Kabul ve onay sayfasindaki tarih, karar numarasi, oy durumu ve juri bilgileri
  gercek bilgilerle doldurulmalidir.
- Etik ve uretken yapay zeka beyan metni tezin gercek kullanim durumuna gore
  gozden gecirilmelidir.
- Kaynakca ve metin ici atiflar APA 7 kurallarina gore danismanla birlikte son
  PDF uzerinden kontrol edilmelidir.
- Enstitunun ayrica istedigi imzali kontrol formu tezin basimina eklenmemeli,
  ayri teslim edilmelidir.
