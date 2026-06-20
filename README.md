# Inonu FBE Tez Sablonu 2025

Bu calisma alaninda Inonu Universitesi Fen Bilimleri Enstitusu 2025 lisansustu
tez yazim kilavuzuna gore hazirlanan tek LaTeX sablonu vardir.

- `inonu-fbe-tez-sablonu-2025`: APA 7 ve numarali kaynak stillerini secilebilir
  bicimde destekleyen birlesik sablon.

Genel baslangic icin `HIZLI_BASLANGIC.md` dosyasini okuyun.

Gorsel arayuz ile kullanmak icin:

```text
tez_gui_baslat.bat
```

Bu dosyayi cift tiklayarak tez yazari icin hazirlanan form arayuzu acilir.
Arayuzde kapak bilgileri `tez.tex` dosyasina guvenli bicimde yazilabilir,
APA 7 veya numarali kaynak stili secilebilir, tez turu belirlenebilir, eksikler
insanin anlayacagi dille gorulebilir, bilgisayardaki TeX araclari kontrol
edilebilir, eski sablonla hazirlanmis tezler yeni sablona donusturulebilir ve
derleme/teslim islemleri tek pencereden baslatilabilir.

Eski tez klasorlerini GUI kullanmadan donusturmek icin:

```powershell
python .\adapt_sample_theses.py --source "D:\EskiTezKlasoru" --output ".\converted_theses"
```

Komut, eski klasore dokunmadan yeni sablonlu ciktiyi `converted_theses`
klasorune yazar ve donusum raporu uretir.

Sablonu hizli kontrol etmek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tumunu-kontrol-et.ps1
```

Sablon icin teslim paketini uretmek icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tumunu-teslime-hazirla.ps1 -Engine xelatex -WithSpine
```

Gercek tez bilgileri girilmeden once kontrol raporlarinda placeholder uyarisi
gorulmesi beklenir. Bu uyarilar `eksik-bilgiler.md` dosyasinda satir satir
listelenir.
