# Tez Hazirlama Kontrol Listesi

Bu liste, `latexsablon` klasorundeki 2025 Inonu Universitesi Fen Bilimleri Enstitusu tez yazim kilavuzuna gore teslim oncesi kontrol icin hazirlanmistir. Kilavuza gore kontrol formu tez yazari ve danismani tarafindan imzalanarak Enstitu Mudurlugune tez ile birlikte teslim edilir; tezin basimina dahil edilmez.

## Derleme ve PDF

- [ ] `latexmk -pdf -interaction=nonstopmode tez.tex` komutu hatasiz tamamlandi.
- [ ] XeLaTeX kullanilacaksa `latexmk -xelatex -interaction=nonstopmode tez.tex` komutu hatasiz tamamlandi.
- [ ] APA kaynakca icin gerekli durumda `biber tez` calistirildi.
- [ ] Son PDF uzerinden sayfa duzeni, yazim, noktalama ve eksik bilgi kontrol edildi.
- [ ] PDF yeniden uretildikten sonra kritik LaTeX uyarilari temizlendi.

## On Bolumler

- [ ] Dis kapak ve ic kapakta tez basligi, tez turu, ogrenci adi, ana bilim dali, program, danisman, sehir ve yil dogru.
- [ ] Dis kapakta FBE amblemi ve alt bant PDF uzerinden gorsel olarak kontrol edildi.
- [ ] Cilt/sirt kapagi gerekiyorsa `sirt-kapak.tex` dolduruldu ve ayri PDF olarak uretildi.
- [ ] Kabul ve Onay sayfasinda savunma tarihi, teslim tarihi, oy durumu ve Enstitu Yonetim Kurulu bilgileri dolduruldu.
- [ ] Etik ve uretken yapay zeka beyan metni tezin gercek kullanim durumuna gore duzenlendi.
- [ ] Ozet ve Abstract birer sayfayi asmiyor; her biri 250 kelime siniri, anahtar kelime ve kaynak kullanmama kurallarina uyuyor.
- [ ] Simgeler ve Kisaltmalar Dizini, Sekiller Dizini ve Tablolar Dizini gerekli ise uretiliyor.

## Ana Metin

- [ ] Ana bolum akisi `GIRIS`, `GENEL BILGILER / KURAMSAL CERCEVE`, `MATERYAL VE METOT`, `BULGULAR`, `TARTISMA`, `SONUC VE ONERILER` duzenine uygun.
- [ ] `GIRIS` bolumunde alt baslik kullanilmadi.
- [ ] Basliklar en fazla ucuncu dereceye kadar icindekiler dizininde gorunuyor.
- [ ] Sekil, tablo ve denklemler metinde ilk gectikleri yerde aniliyor.
- [ ] `kontrol.ps1` raporunda tanimsiz `\ref`/`\eqref` ve metinde anilmayan sekil/tablo/denklem etiketi kalmadi.
- [ ] Sekil ve tablo basliklari nokta ile numaradan ayriliyor ve cumle sonunda nokta kullanilmiyor.
- [ ] Dipnotlar kisa, 10 punto ve tek satir aralikli.

## Kaynaklar ve Ekler

- [ ] Metin icinde verilen her kaynak `kaynaklar.bib` dosyasinda yer aliyor.
- [ ] `kaynaklar.bib` icinde metinde hic kullanilmayan kayitlar temizlendi veya bilincli olarak birakildi.
- [ ] APA atiflari icin `\parencite{...}` veya `\textcite{...}` kullanildi.
- [ ] Kaynakca `KAYNAKLAR` basligi altinda 11 punto, 1,5 satir aralikli ve asili girintili uretiliyor.
- [ ] Ekler bolumu `EK-1 Ozgecmis` ile basliyor.
- [ ] Eklerdeki sekil, tablo ve denklemler `EK-2.1`, `EK-3.1` gibi ek numarasina bagli uretiliyor.

## Teslim Oncesi

- [ ] Danismanla son PDF uzerinden bicim ve icerik kontrolu yapildi.
- [ ] Enstitunun istedigi imzali kontrol formu ayrica dolduruldu.
- [ ] Tezin basimina dahil edilmemesi gereken formlar PDF iceriginden cikarildi.
