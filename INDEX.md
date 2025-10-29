# 📚 Türkçe Benchmark - Dokümantasyon İndeksi

## 📄 Ana Dokümantasyon (4 Dosya)

### 1. **README.md** - Genel Bakış
- Proje tanıtımı
- Özellikler ve test kategorileri
- Hızlı başlangıç örnekleri
- Proje yapısı

**Ne zaman okuyun**: İlk kez projeyi görüyorsanız

---

### 2. **QUICK_START.md** - Hızlı Başlangıç
- 5 dakikalık kurulum
- İlk test adımları
- Basit örnekler
- Yaygın hatalar ve çözümler

**Ne zaman okuyun**: Hemen test yapmak istiyorsanız

---

### 3. **USAGE_GUIDE.md** - Detaylı Kullanım Kılavuzu
- 28 modelin tam listesi
- Tüm komutlar ve örnekler
- Model seçim rehberi
- Performans optimizasyonu
- Sorun giderme
- Maliyet karşılaştırmaları
- Yeniden puanlama

**Ne zaman okuyun**: Detaylı bilgi ve ileri kullanım için

---

### 4. **CONTRIBUTING.md** - Katkıda Bulunma
- Geliştirme ortamı kurulumu
- Kod standartları
- Pull request süreci
- Yeni soru ekleme

**Ne zaman okuyun**: Projeye katkıda bulunmak istiyorsanız

---

## 🎯 Hangi Dosyayı Okumalıyım?

### Yeni Kullanıcı
```
README.md → QUICK_START.md → İlk test çalıştır
```

### Deneyimli Kullanıcı
```
USAGE_GUIDE.md → Komutları kopyala-yapıştır
```

### Geliştirici
```
CONTRIBUTING.md → Kod yazın → Pull request
```

### Hata Aldım
```
USAGE_GUIDE.md → "Sorun Giderme" bölümü
```

---

## ⚡ Hızlı Komutlar

```bash
# Dokümantasyonu okuma
cat README.md          # Genel bakış
cat QUICK_START.md     # Hızlı başlangıç
cat USAGE_GUIDE.md     # Detaylı kullanım
cat CONTRIBUTING.md    # Katkı rehberi

# İlk test
python3 run_claude_comparison.py

# Model kayıtları
python3 model_registry.py

# Yardım
python3 benchmark.py --help
```

---

## 🎊 Temizleme Yapıldı!

**Önceki**: 17 MD dosyası  
**Sonrası**: 4 MD dosyası  
**Silinen**: 13 dosya (tekrar eden/gereksiz)  

**Tüm bilgiler** 4 dosyada toplanmıştır! ✅

---

## 📁 Proje Dosya Yapısı

```
Turkish-Benchmark/
├── README.md              # 📖 ANA DOKÜMANTASYON
├── QUICK_START.md         # 🚀 HIZLI BAŞLANGIÇ
├── USAGE_GUIDE.md         # 📚 DETAYLI KILAVUZ
├── CONTRIBUTING.md        # 🤝 KATKI REHBERİ
├── INDEX.md               # 📑 Bu dosya
│
├── benchmark.py           # Ana test scripti
├── run_claude_comparison.py   # Claude test
├── run_gpt5_comparison.py     # GPT-5 test
├── compare_results.py     # Sonuç karşılaştırma
├── model_registry.py      # Model kayıtları
├── analyze_saq.py         # SAQ analiz
├── rescore.py             # Yeniden puanlama
├── full_analysis.py       # Genel özet
│
├── config.yaml            # Konfigürasyon
├── requirements.txt       # Bağımlılıklar
└── ... (16 Python scripti toplam)
```

---

**Hemen başlayın**:
```bash
cat QUICK_START.md
```

Veya:
```bash
python3 run_claude_comparison.py
```

