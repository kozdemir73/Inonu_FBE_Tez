# Yazım ve Dilbilgisi Ön Denetim Raporu

Bu rapor yerel kural tabanlı ve sözlük destekli ön denetimdir. Ayrıca tez yazım kılavuzunda öğrencinin metin yazarken dikkat etmesi beklenen noktalama, sayı-birim, yüzde, renk ve vurgu kullanımı gibi kurallar için ön uyarılar üretir. Gelişmiş yapay zekâ incelemesi için aşağıdaki `ai-yazim-denetimi-istegi.md` dosyası kullanılabilir.

- Bulgu sayısı: 1
- Önceki denetime göre: 0 bulgu giderilmiş/yok sayılmış, 0 yeni veya devam eden bulgu
- Sözlük durumu: Türkçe Zemberek morfoloji sözlüğü aktif.
- Kişisel sözlük/yok say: 0 kelime, 1 yok sayma kuralı

## Toplu Özet

### Bulgu Türleri

- Kılavuz yazım kuralı: 1

### Dosyaya Göre

- `ozet.tex`: 1

### En Sık Görülen Bulgular

- 1 kez: kılavuz yazım kuralı: ondalık sayı virgül ile yazılmış olabilir: `...`. referans: tez yazım kılavuzu metin biçimi, noktalama, sayı ve birim kullanımı kuralları. öneri: seçili ondalık ayırıcı nokta olduğu için `...` biçimini kullanın; denklem/kod bağlamıysa kontrol edin.

## Bulgular

- `ozet.tex:7` - Kılavuz yazım kuralı: Ondalık sayı virgül ile yazılmış olabilir: `1,15`. Referans: tez yazım kılavuzu metin biçimi, noktalama, sayı ve birim kullanımı kuralları. Öneri: Seçili ondalık ayırıcı nokta olduğu için `1.15` biçimini kullanın; denklem/kod bağlamıysa kontrol edin.
  - Metin: `\textbf{Sonuç:} Özet başlık ve anahtar kelimeler hariç en fazla 250 kelime olmalı, tercihen tek sayfaya sığmalıdır. Gerektiğinde satır aralığı 1,15'e indirilebilir.`
