# Eksik veya teyit gerektiren bilgiler

Bu rapor otomatik uretilir. Gercek tez bilgileri girildikten sonra tekrar calistirilabilir.

Onerilen is akisi:

1. tez-bilgileri.example.json dosyasini tez-bilgileri.json olarak kopyalayin.
2. Asagidaki alanlari resmi/danisman onayli bilgilerle doldurun.
3. tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json -WhatIf ile on izleme yapin.
4. tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json ile uygulayin.
5. kontrol.ps1 -Build -Engine xelatex -WithSpine -Report ile denetleyin.

## Otomatik bulunan alanlar

Otomatik taramada eksik veya ornek olarak birakilmis bilgi bulunmadi.

## Elle teyit edilecekler

- [ ] Kapak ve sirt kapakta uzun baslik tasmasi yok.
- [ ] Juri, tarih, karar numarasi ve Enstitu Muduru bilgileri resmi belgelerle uyumlu.
- [ ] Ozet ve abstract gercek tezin amac, yontem, bulgu ve sonucunu yansitiyor.
- [ ] Anahtar kelimeler gercek tez konusuna uygun ve alfabetik.
- [ ] APA 7 kaynak bicimi ve akademik icerik danisman/enstitu beklentisine uygun.
- [ ] Etik ve uretken yapay zeka beyan metni gercek kullanim durumunu yansitiyor.
- [ ] Son teslim paketi teslim-hazirla.ps1 -Engine xelatex -WithSpine ile uretildi.
