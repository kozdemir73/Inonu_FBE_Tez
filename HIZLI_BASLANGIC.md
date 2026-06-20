# Hizli Baslangic

## Sablon klasoru

Birlesik sablon klasoru `inonu-fbe-tez-sablonu-2025` klasorudur. APA 7 veya
numarali kaynak stili bu sablon icinden secilir; kilavuzun ana yonelimi APA 7
oldugu icin numarali kaynak gosterimi bolum/enstitu onayi ile tercih
edilmelidir.

## Gorsel arayuz

Tez bilgilerini kod satirlariyla ugrasmadan girmek icin proje kokundeki
`tez_gui_baslat.bat` dosyasini cift tiklayin.

Arayuzde:

- APA 7 veya numarali kaynak stili secilir.
- Yuksek lisans/doktora tez turu secilir.
- Ogrenci, baslik, danisman, juri, tarih ve karar bilgileri formdan girilir.
- `tez.tex'e Guvenli Yaz` dugmesi bu bilgileri `tez.tex` dosyasina uygular.
- Eksikler sekmesi doldurulmasi gereken alanlari sade Turkceyle gosterir.
- Sistem sekmesi bilgisayarda hangi TeX araclarinin bulundugunu ve hangi
  derleme motorunun kullanilabilecegini gosterir.
- Derleme ve teslim islemleri tek pencereden baslatilir.
- `PDF ve Teslim` sekmesindeki `Eski Tezi Donustur` dugmesi, eski sablonla
  hazirlanmis bir tez klasorunu yeni sablonlu ayri bir calisma klasorune
  aktarir.

Tez yazari isterse ana bolumleri yine LaTeX ile duzenleyebilir; isterse
Scientific Workplace gibi araclarla uretilen bolum iceriklerini ilgili
`bolum1.tex` ... `bolum6.tex` dosyalarina yerlestirebilir.

## Eski tezleri yeni sablona donusturme

GUI icinden:

1. `PDF ve Teslim` sekmesine gecin.
2. `Eski Tezi Donustur` dugmesine basin.
3. Eski tezin bulundugu klasoru secin.
4. Donusturulen tez `converted_theses` klasoru altinda olusur.
5. Uretilen klasoru GUI'de `Calisma klasoru` olarak secip kapak bilgilerini
   gozden gecirin.

Komut satirindan:

```powershell
python .\adapt_sample_theses.py --source "D:\EskiTezKlasoru" --output ".\converted_theses"
```

Donusturucu eski klasoru degistirmez. Bolum dosyalarini, kaynakcayi ve yerel
yardimci LaTeX dosyalarini yeni sablon klasorune kopyalar; raporu Markdown ve
JSON olarak yazar.

## Ilk kurulum

Gorsel arayuzu kullanmiyorsaniz secilen sablon klasorunde:

```powershell
Copy-Item .\tez-bilgileri.example.json .\tez-bilgileri.json
```

`tez-bilgileri.json` dosyasinda ogrenci, baslik, danisman, juri, tarih ve karar
bilgilerini doldurun.

Once degisecek satirlari gormek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json -WhatIf
```

Uygulamak icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json
```

## Icerik dosyalari

- `ozet.tex`: Turkce ozet.
- `abstract.tex`: Ingilizce abstract.
- `onsoz.tex`: Onsoz.
- `bolum1.tex` ... `bolum6.tex`: Ana bolumler.
- `kaynaklar.bib`: Kaynaklar.
- `ozgecmis.tex`: Ozgecmis.

## Kontrol

Eksik bilgi raporu:

```powershell
powershell -ExecutionPolicy Bypass -File .\eksik-bilgiler.ps1
```

Tam otomatik uygunluk denetimi:

```powershell
powershell -ExecutionPolicy Bypass -File .\kontrol.ps1 -Build -Engine xelatex -WithSpine -Report
```

## Teslim paketi

```powershell
powershell -ExecutionPolicy Bypass -File .\teslim-hazirla.ps1 -Engine xelatex -WithSpine
```

Bu komut `teslim\YYYYAAGG-SSddss` klasoru altinda PDF'leri, kontrol raporlarini,
eksik bilgi raporunu, notlari ve `kaynak.zip` dosyasini uretir.

## Son elle kontrol

- Kapak ve sirt kapakta uzun baslik tasmasi yok.
- Danisman, juri, tarih, karar no ve Enstitu Muduru bilgileri resmi belgelerle
  uyumlu.
- Ozet/abstract ve ana bolumler gercek tez icerigini yansitiyor.
- APA 7 veya numarali kaynak bicimi danisman/enstitu beklentisine uygun.
- Etik ve uretken yapay zeka beyan metni gercek kullanim durumunu yansitiyor.
