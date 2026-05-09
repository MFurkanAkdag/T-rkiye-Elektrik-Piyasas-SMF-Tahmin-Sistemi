# EnerjiPusula: Türkiye Elektrik Piyasası SMF Tahmin Sistemi

EnerjiPusula, Türkiye elektrik piyasasında oluşan Sistem Marjinal Fiyatı'nı (SMF/SMP) saatlik zaman serisi verileri üzerinden tahmin etmeyi amaçlayan bir makine öğrenmesi projesidir. Proje, SEN22325E Learning From Data dönem projesi kapsamında verilen EPİAŞ verisini temel alır; hava durumu, finansal göstergeler ve üretim kaynakları gibi ek değişkenlerle zenginleştirilebilecek uçtan uca bir fiyat tahmin sistemi tasarlamayı hedefler.

Bu README dosyası projenin amacını, veri yapısını, kullanılan yöntemleri, mevcut kod organizasyonunu ve önerilen geliştirme akışını teknik rapor formatında özetler.

## Projenin Amacı

Elektrik piyasasında fiyatlar; talep, arz, üretim kompozisyonu, hava koşulları, döviz kuru ve piyasa davranışı gibi birçok değişkenden etkilenir. Bu nedenle SMF tahmini klasik bir regresyon probleminden daha karmaşık bir zaman serisi problemidir.

Bu projenin temel amacı:

- 01.01.2019 - 27.02.2023 aralığındaki saatlik EPİAŞ verilerini kullanarak SMF tahmini yapmak
- Tek değişkenli ve çok değişkenli tahmin yaklaşımlarını karşılaştırmak
- Zaman serisi doğasına uygun eğitim/test ayrımı ve 24 saatlik tahmin ufku kullanmak
- Farklı model ailelerinin performansını MAPE, RMSE ve MAE metrikleriyle ölçmek
- Veri toplama, ön işleme, özellik mühendisliği, modelleme ve değerlendirme adımlarını modüler bir proje yapısı içinde düzenlemek

## Problem Tanımı

Hedef değişken `Smf` sütunudur. Modelden beklenen çıktı, belirli bir eğitim aralığı kullanılarak bir sonraki 24 saat için saatlik SMF değerlerini tahmin etmektir.

Dönem projesi yönergesine göre tüm modeller aynı test günleri üzerinde değerlendirilmelidir:

| Eğitim Bitişi | Test Aralığı |
| --- | --- |
| 20.02.2023 23:00 | 21.02.2023 00:00 - 21.02.2023 23:00 |
| 21.02.2023 23:00 | 22.02.2023 00:00 - 22.02.2023 23:00 |
| 22.02.2023 23:00 | 23.02.2023 00:00 - 23.02.2023 23:00 |
| 23.02.2023 23:00 | 24.02.2023 00:00 - 24.02.2023 23:00 |
| 24.02.2023 23:00 | 25.02.2023 00:00 - 25.02.2023 23:00 |
| 25.02.2023 23:00 | 26.02.2023 00:00 - 26.02.2023 23:00 |
| 26.02.2023 23:00 | 27.02.2023 00:00 - 27.02.2023 23:00 |

Her model bu 7 farklı eğitim/test penceresinde çalıştırılmalı ve ortalama performans raporlanmalıdır.

## Veri Seti

Ana veri seti `data/raw/smfdb.csv` dosyasında yer alır.

Veri özeti:

- Kayıt sayısı: 36.456
- Sütun sayısı: 29
- Zaman aralığı: 01.01.2019 00:00 - 27.02.2023 23:00
- Frekans: Saatlik
- Eksik değer: Mevcut veri dosyasında eksik değer bulunmamaktadır
- Hedef değişken: `Smf`
- Yardımcı piyasa fiyatı: `Ptf`

Temel sütun grupları:

- Zaman: `Tarih`
- Eşleşme miktarları: `Blokeslesmemiktari`, `Saatlikeslesmemiktari`
- Alış/satış fiyatları: `Minalisfiyati`, `Maxalisfiyati`, `Minsatisfiyati`, `Maxsatisfiyati`
- Eşleşme fiyatları: `Mineslesmefiyati`, `Maxeslesmefiyati`
- Talep/arz işlem hacmi: `Talepislemhacmi`, `Arzislemhacmi`
- Üretim kaynakları: doğal gaz, barajlı, linyit, akarsu, ithal kömür, rüzgar, güneş, fuel-oil, jeotermal, biyokütle ve diğer kaynaklar
- Toplam gerçekleşen üretim: `Gerceklesentoplam`
- Piyasa fiyatları: `Smf`, `Ptf`

Veri setinde `Smf` ve `Ptf` değerleri Türk lirası bazındadır. Proje yönergesine göre döviz kuru verisi uygun bir API üzerinden toplanarak SMF ve PTF değerlerinin USD bazlı sürümleri de üretilebilir.

## Ek Veri Kaynakları

Projede sadece EPİAŞ verisiyle sınırlı kalınmaması önerilir. PDF yönergesinde aşağıdaki ek verilerin toplanması beklenir:

- Hava durumu verileri: sıcaklık, nem, rüzgar, güneşlenme/radyasyon gibi değişkenler
- Döviz kuru verileri: özellikle USD/TRY dönüşümü
- Ekonomik göstergeler: piyasa koşullarını açıklayabilecek makro veriler

`notebooks/epias_weather_historical_forecast_data.ipynb` dosyası Weatherbit API üzerinden geçmiş ve ileriye dönük saatlik hava durumu verisi toplamak için örnek kod içerir. Notebook içinde İstanbul Anadolu, İstanbul Avrupa ve Bursa için sıcaklık ve nem verilerinin çekilmesi, tarih formatının düzenlenmesi ve ana veriyle `Tarih` alanı üzerinden birleştirilmesi gösterilmiştir.

## Kullanılan Yöntem ve Teknikler

### 1. Veri Ön İşleme

`src/models/preprocessors.py` dosyasında `DataPreprocessor` sınıfı tanımlanmıştır. Bu sınıf aşağıdaki işlemleri kapsar:

- Eksik değer işleme: Sayısal sütunlarda doğrusal interpolasyon
- Aykırı değer temizleme: IQR yöntemine göre alt ve üst sınır dışında kalan gözlemlerin filtrelenmesi
- Ölçekleme: `StandardScaler` ile sayısal özelliklerin standartlaştırılması

Zaman serisi problemlerinde ön işleme yapılırken veri sızıntısına dikkat edilmelidir. Ölçekleyici, aykırı değer sınırları ve seçilen dönüşümler sadece eğitim verisi üzerinde öğrenilmeli; test verisine aynı parametreler uygulanmalıdır.

### 2. Özellik Mühendisliği

Proje için önerilen özellik mühendisliği adımları:

- Takvim özellikleri: saat, gün, ay, hafta içi/hafta sonu, mevsim
- Gecikmeli değişkenler: `Smf_lag_1`, `Smf_lag_24`, `Smf_lag_168`
- Hareketli istatistikler: 24 saatlik ve 168 saatlik ortalama, standart sapma, minimum ve maksimum
- Üretim karması özellikleri: toplam üretim içindeki doğal gaz, rüzgar, güneş ve hidroelektrik payları
- Piyasa farkları: `Ptf - Smf`, maksimum/minimum alış-satış fiyat farkları
- Hava durumu özellikleri: sıcaklık, nem, rüzgar ve şehir bazlı ortalamalar
- Döviz kuru dönüşümü: `Smf_USD` ve `Ptf_USD`

Özellik seçimi için korelasyon analizi, lag analizi, model tabanlı feature importance ve mRMR gibi yöntemler kullanılabilir.

### 3. Modelleme Yaklaşımları

Proje iki ana yaklaşımı karşılaştırmayı hedefler.

#### Tek Değişkenli Yaklaşım

Tek değişkenli yaklaşımda model yalnızca geçmiş `Smf` değerlerini kullanır. Bu yaklaşım başlangıç modeli kurmak için uygundur ve zaman serisinin kendi mevsimselliğini, trendini ve gecikmeli etkilerini öğrenmeye çalışır.

Kullanılabilecek modeller:

- ARIMA
- SARIMA
- Prophet
- SVR
- Random Forest
- XGBoost
- LSTM
- Transformer tabanlı modeller

#### Çok Değişkenli Yaklaşım

Çok değişkenli yaklaşımda `Smf` geçmişine ek olarak piyasa, üretim, hava durumu ve finansal göstergeler kullanılır. Elektrik fiyatı birçok dış etkenden beslendiği için bu yaklaşım genellikle daha açıklayıcıdır.

Kullanılabilecek ek girdiler:

- `Ptf`
- Arz ve talep işlem hacimleri
- Üretim kaynakları
- Hava durumu değişkenleri
- Döviz kuru
- Takvim ve lag özellikleri

### 4. Model Soyutlaması

`src/models/base.py` dosyasında tüm tahmin modelleri için ortak bir `BaseModel` soyut sınıfı bulunur. Bu sınıf aşağıdaki temel metotları standartlaştırır:

- `fit(X, y)`: modeli eğitir
- `predict(X)`: tahmin üretir
- `save(path)`: modeli diske kaydetmek için ayrılmıştır
- `load(path)`: modeli diskten yüklemek için ayrılmıştır

Bu yapı, ARIMA, SVR, Random Forest, XGBoost veya LSTM gibi farklı model türlerinin aynı arayüzle çalıştırılmasını kolaylaştırır.

### 5. Değerlendirme

`src/models/evaluation.py` dosyası model performansını ölçmek için üç temel metriği içerir:

- MAPE: Ortalama mutlak yüzde hata
- RMSE: Kök ortalama kare hata
- MAE: Ortalama mutlak hata

`evaluate_model(model, X_test, y_test)` fonksiyonu modelin tahminlerini alır ve bu metrikleri tek bir sözlük olarak döndürür.

Not: MAPE hesaplamasında gerçek değer sıfıra yakın olduğunda sonuç yanıltıcı olabilir. SMF veri setinde sıfır değerler bulunduğu için değerlendirme aşamasında MAPE kullanımı dikkatli yorumlanmalıdır.

## Proje Yapısı

Mevcut proje dizini aşağıdaki yapıdadır:

```text
LFD_24-25-main/
|
├── data/
│   └── raw/
│       └── smfdb.csv
|
├── notebooks/
│   └── epias_weather_historical_forecast_data.ipynb
|
├── src/
│   ├── __init__.py
│   └── models/
│       ├── base.py
│       ├── evaluation.py
│       └── preprocessors.py
|
└── README.md
```

Önerilen nihai proje yapısı:

```text
LFD_24-25-main/
|
├── data/
│   ├── raw/
│   └── processed/
|
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_data_exploration.ipynb
│   └── 03_model_evaluation.ipynb
|
├── src/
│   ├── config.py
│   ├── data/
│   │   ├── collectors.py
│   │   └── preprocessors.py
│   ├── features/
│   │   ├── builders.py
│   │   └── selectors.py
│   ├── models/
│   │   ├── base.py
│   │   ├── statistical.py
│   │   ├── ml_models.py
│   │   └── dl_models.py
│   └── utils/
│       ├── evaluation.py
│       └── visualization.py
|
├── tests/
├── requirements.txt
└── README.md
```

## Kurulum

Gerekli temel paketler:

```bash
pip install pandas numpy scikit-learn matplotlib seaborn jupyter requests
```

Model çeşitliliğine göre ek paketler:

```bash
pip install statsmodels prophet xgboost tensorflow torch
```

Not: Projede şu anda `requirements.txt` dosyası bulunmamaktadır. Tekrarlanabilir kurulum için kullanılan tüm paketlerin bu dosyaya eklenmesi önerilir.

## Kullanım Akışı

1. Ham EPİAŞ verisini `data/raw/smfdb.csv` konumundan yükleyin.
2. `Tarih` sütununu tarih-saat formatına dönüştürün.
3. Eksik değer, aykırı değer ve ölçekleme işlemlerini uygulayın.
4. Hava durumu ve döviz kuru verilerini API üzerinden toplayın.
5. Ana veri setiyle ek verileri saatlik `Tarih` alanı üzerinden birleştirin.
6. Lag, rolling ve takvim özelliklerini üretin.
7. Tek değişkenli ve çok değişkenli veri setlerini ayrı ayrı hazırlayın.
8. Her model için 7 günlük 24 saatlik test penceresinde eğitim ve tahmin yapın.
9. MAPE, RMSE ve MAE değerlerini hesaplayın.
10. Model performanslarını tablo ve grafiklerle karşılaştırın.

## Beklenen Görselleştirmeler

Teknik raporda aşağıdaki görselleştirmeler yer almalıdır:

- SMF ve PTF zaman serisi grafikleri
- Saatlik, günlük ve aylık fiyat dağılımları
- Üretim kaynaklarının zaman içindeki değişimi
- Korelasyon matrisi
- Lag korelasyonu grafikleri
- Gerçek ve tahmin edilen SMF karşılaştırmaları
- Model bazlı MAPE, RMSE ve MAE karşılaştırma grafikleri
- Test günlerine göre hata analizi

## Mevcut Kodların Rolü

Bu repodaki mevcut kodlar proje için başlangıç altyapısı sağlar:

- `BaseModel`: Modellerin ortak arayüzünü tanımlar.
- `DataPreprocessor`: Eksik değer, aykırı değer ve ölçekleme işlemlerini merkezi hale getirir.
- `calculate_metrics`: Tahmin sonuçları için temel hata metriklerini hesaplar.
- `epias_weather_historical_forecast_data.ipynb`: Weatherbit API ile saatlik hava durumu verisi toplama örneği sunar.

Henüz model sınıfları, feature engineering modülleri, görselleştirme yardımcıları ve tam eğitim pipeline'ı tamamlanmamıştır. Bu README, mevcut iskeletin dönem projesi gereksinimlerine göre nasıl genişletileceğini de belgelemektedir.

## Geliştirme Yol Haritası

- `requirements.txt` dosyasını oluşturmak
- API anahtarlarını kod içinden çıkarıp `.env` veya config yapısına taşımak
- Döviz kuru verisini toplayıp `Smf_USD` ve `Ptf_USD` sütunlarını üretmek
- `src/features/builders.py` içinde lag, rolling ve takvim özelliklerini modülerleştirmek
- ARIMA/SARIMA veya Prophet ile istatistiksel baseline oluşturmak
- SVR, Random Forest ve XGBoost modellerini eklemek
- LSTM ve en az iki farklı derin öğrenme yaklaşımı denemek
- 7 günlük rolling test değerlendirme fonksiyonunu yazmak
- Sonuçları grafik ve tablolarla raporlamak
- Test dosyaları ve geliştirme günlükleri eklemek

## Akademik Notlar

Proje yönergesine göre kullanılan tüm dış kaynaklar, API servisleri, kütüphaneler ve varsa yapay zeka araçları raporda belirtilmelidir. AI araçları kullanıldıysa hangi amaçla kullanıldığı, üretilen önerilerin nasıl değiştirildiği ve öğrencinin katkısı açıkça yazılmalıdır.

## Referanslar

- EPİAŞ Şeffaflık Platformu: https://seffaflik.epias.com.tr/
- SMF/SMP açıklaması: https://seffaflik.epias.com.tr/electricity/electricity-markets/balancing-power-market-bpm/system-marginal-price
- PTF/MCP açıklaması: https://seffaflik.epias.com.tr/electricity/electricity-markets/day-ahead-market-dam/market-clearing-price-mcp
- Weatherbit API: https://www.weatherbit.io/api
- Dönem projesi yönergesi: `Term_Project (1).pdf`
