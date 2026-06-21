# Inonu FBE Tez Sablonu 2025 - APA

Bu klasor Inonu Universitesi Fen Bilimleri Enstitusu 2025 lisansustu tez
yazim kilavuzuna gore duzenlenen APA 7 kaynak stilli LaTeX sablonudur.

Derleme icin XeLaTeX kullanilir. Bu secim Calibri yazitipi ve Turkce karakter
uyumu icin sabit tutulur:

```powershell
latexmk -xelatex -interaction=nonstopmode tez.tex
```

Ana tezi derleyip kritik LaTeX log uyarilarini otomatik kontrol etmek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Engine xelatex
```

Sirt kapagi da ayni turda uretmek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Engine xelatex -WithSpine
```

`-WithSpine` kullanildiginda `sirt-kapak.tex` dosyasi ana `tez.tex`
bilgilerinden otomatik guncellenir. Sadece sirt kapak kaynak dosyasini
guncellemek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\sirt-kapak-guncelle.ps1
```

Tez kapak/onay bilgilerinin buyuk bolumunu tek dosyadan doldurmak icin
`tez-bilgileri.example.json` dosyasini `tez-bilgileri.json` adiyla kopyalayip
duzenleyin. Once degisecek satirlari gormek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json -WhatIf
```

Uygulamak icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json
```

Eksik veya teyit gerektiren alanlari raporlamak icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\eksik-bilgiler.ps1
```

Otomatik uygunluk denetimi icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\kontrol.ps1 -Build -Engine xelatex -WithSpine -Report
```

Bu denetim derleme, kritik log kayitlari, zorunlu PDF basliklari, font gomulmesi,
zorunlu kaynak dosyalari, kapak logosu, yer tutucu alanlari, sirt kapak
tutarliligi, ozet/abstract kelime sayisi, anahtar kelime sayisi ve alfabetikligi,
ozetlerde kaynak/sekil/tablo komutu ve atif-bib anahtari eslesmesini kontrol
eder. `-Report` kullanildiginda `kontrol-raporu.json` ve `kontrol-raporu.md`
`raporlar` klasoru altinda uretilir. `MANUEL` satirlari danisman/enstitu onayi
ve son PDF gorsel kontrolu gerektirir.

Derleme ara dosyalarini temizlemek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\temizle.ps1
```

Tek komutla derleme, uygunluk denetimi, rapor ve teslim klasoru olusturmak icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\teslim-hazirla.ps1 -Engine xelatex -WithSpine
```

Bu komut `teslim\YYYYAAGG-SSddss` klasoru altinda PDF'leri, kontrol raporlarini,
eksik bilgi raporunu, kontrol notlarini ve `kaynak.zip` dosyasini hazirlar.

`latexmk` gerekli durumda `biber` aracini kendisi calistirir. Elle derleme
yapilacaksa sira `xelatex -> biber -> xelatex -> xelatex` olmalidir.

Notlar:

- Ana resmi kaynak stili APA 7 olarak ayarlanmistir.
- Kaynak dosyasi `kaynaklar.bib` dosyasidir.
- Tez Asistani icindeki `Kaynakca Havuzu` denetimi `kaynaklar.bib` dosyasini
  okur, kaynak anahtarlarini ilk yazar soyadi ve yil bicimine gore onerir
  (`Zuckerman1994`, ayni yil tekrarinda `Zuckerman1994a` gibi) ve istenirse
  ana bilim dalina ait yerel havuza ekler. Yerel havuzlar sablon klasorunun
  disinda, calisma alaninin `kaynakca-havuzlari` klasorunde tutulur.
- APA surumunde parantezli atif icin `\parencite{anahtar}`, anlatimli atif
  icin `\textcite{anahtar}` kullanilmalidir.
- Tesekkur ve onsoz sayfasi `tesekkur.tex` dosyasindan gelir. Eski tezlerden
  gelen `\onsoz{...}` komutu uyumluluk icin desteklenir; yeni sablonda baslik
  `TESEKKUR VE ONSOZ` olarak uretilir.
- Etik ve uretken yapay zeka beyan metni `etik-beyan.tex` dosyasindan gelir.
- Ozet ve abstract metinleri baslik ve anahtar kelimeler haric en fazla 250
  kelime olmalidir. Metinlerde kaynak, sekil ve tablo verilmemelidir.
- Turkce ve Ingilizce ozetlerde en az 3 anahtar kelime bulunmali; anahtar
  kelimeler virgulle ayrilmali, ilk harfleri buyuk olmali ve kendi icinde
  alfabetik siralanmalidir.
- Simgeler ve kisaltmalar `SIMGELER VE KISALTMALAR DIZINI` basligi altinda
  birlikte verilir. Ornek liste `simgeler-ve-kisaltmalar.tex`
  dosyasindadir; girdiler 1,25 cm iceriden baslar, terim ve iki nokta kalin
  yazilir, aciklamalar bas harfleri buyuk ve alfabetik duzende tutulur.
- Dipnotlar 10 punto ve tek satir aralikli ayarlanmistir; ayirici cizgi
  metin genisliginin yarisina kadar uzanir ve numaralandirma her sayfada 1'den
  yeniden baslar.
- Sekil ve tablo altindaki aciklayici notlar icin `\sekilnotu{...}` ve
  `\tablonotu{...}` komutlari kullanilir; bu notlar 9 punto uretilir.
- Denklemler bolum numarasi ile birlikte artan bicimde numaralandirilir
  (`3.1`, `3.2` gibi). Cok satirli denklemlerde numara son satir hizasinda
  kalacak sekilde `align` ortaminda onceki satirlara `\notag` verilmelidir.
- Kaynakca `KAYNAKLAR` basligi altinda 11 punto, 1,5 satir aralikli ve 1,25 cm
  asili girintili olarak uretilir.
- Teslim oncesi kontrol icin `kilavuz-notlari\KONTROL_LISTESI.md` dosyasi kullanilabilir.
  Kilavuzdaki kontrol formu tezin basimina dahil edilmez; imzalanarak tez ile
  birlikte ayrica teslim edilir.
- Sablonun otomatik karsiladigi noktalar ve gercek tez uzerinden elle kontrol
  edilmesi gerekenler `kilavuz-notlari\UYGUNLUK_NOTLARI.md` dosyasinda ozetlenmistir.
- Kabul ve onay sayfasindaki oy durumu `\oy{...}` ile, Enstitu Yonetim Kurulu
  tarihi ve karar numarasi `\yonetimkurulukarar{...}{...}` ile doldurulur.
- Kapakta Turkce buyuk harflerin dogru cikmasi icin ornek `\yazar` ve
  `\anabilimdali` alanlarinda noktali i `i`, noktasiz i `ı` seklinde
  verilmistir.
- Dis kapak Ek-1 kapak duzenine uygun olarak logo, universite/enstitu adi,
  tez basligi, tez turu, ogrenci adi, sehir ve yil alt bandini kullanir.
  Ana bilim dali, danisman, ogrenci numarasi ve program bilgisi ic kapakta
  yer alir.
- Cilt baskisi icin gereken sirt yazisi ana teze otomatik eklenmez; ayri
  uretmek gerektiginde `sirt-kapak.tex` dosyasindaki bilgiler doldurulup
  `latexmk -pdf -interaction=nonstopmode sirt-kapak.tex` komutu calistirilir.
- XeLaTeX ile derlemede sistemde varsa gercek Calibri kullanilir; bulunamazsa
  Carlito'ya geri donulur. Enstitu teslimi icin Calibri hedeflendiginden
  pdfLaTeX/PDFTeXify secenegi sablondan kaldirilmistir.
