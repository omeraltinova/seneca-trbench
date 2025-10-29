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
cat README.md               # Genel bakış
cat docs/QUICK_START.md     # Hızlı başlangıç
cat docs/USAGE_GUIDE.md     # Detaylı kullanım
cat docs/CONTRIBUTING.md    # Katkı rehberi

# İlk test
python3 examples/run_claude_comparison.py

# Model kayıtları
python3 tools/model_registry.py

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
├── README.md                    # 📖 ANA DOKÜMANTASYON
├── benchmark.py                 # Ana test scripti
├── config.example.yaml          # Konfigürasyon şablonu
├── requirements.txt             # Bağımlılıklar
├── LICENSE                      # MIT License
│
├── docs/                        # 📚 Dokümantasyon
│   ├── QUICK_START.md           # 🚀 Hızlı başlangıç
│   ├── USAGE_GUIDE.md           # 📖 Detaylı kullanım
│   ├── CONTRIBUTING.md          # 🤝 Katkı rehberi
│   ├── MODELS.md                # 🤖 Model listesi
│   └── INDEX.md                 # 📑 Bu dosya
│
├── src/                         # 💻 Kaynak kodlar
│   ├── evaluator.py             # Test yürütücü
│   ├── judge.py                 # Puanlama sistemi
│   ├── reporter.py              # Rapor oluşturucu
│   ├── models/                  # Model wrapper'ları
│   └── utils/                   # Yardımcı modüller
│
├── data/                        # 📊 Test verileri
│   ├── MCQ-Türkçe Benchmark.json  # 131 MCQ
│   └── SAQ-Türkçe-Benchmark.json  # 422 SAQ
│
├── examples/                    # 📋 Örnek scriptler
│   ├── run_claude_comparison.py
│   ├── run_gpt5_comparison.py
│   └── run_comparison_test.py
│
├── tools/                       # 🔧 Yardımcı araçlar
│   ├── model_registry.py
│   ├── compare_results.py
│   ├── analyze_saq.py
│   └── rescore.py
│
├── results/                     # Test sonuçları (git'te yok)
└── logs/                        # Log dosyaları (git'te yok)
```

---

**Hemen başlayın**:
```bash
cat docs/QUICK_START.md
```

Veya:
```bash
python3 examples/run_claude_comparison.py
```

