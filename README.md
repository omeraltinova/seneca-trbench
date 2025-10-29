# Seneca-TRBench - Turkish LLM Benchmark

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Seneca-TRBench**: Türk dilinin özelliklerini ve karmaşıklıklarını test eden kapsamlı bir benchmark sistemi. GPT-4o tabanlı otomatik puanlama ile LLM modellerinin Türkçe dil yeteneklerini objektif olarak değerlendirir.

> **553 soru** (131 MCQ + 422 SAQ) ile Türkçe'nin morfolojik, semantik ve pragmatik özelliklerini test eder.

## 🌟 Desteklenen Sağlayıcılar

- 🔵 **OpenAI** (GPT-5, GPT-4, GPT-3.5)
- 🟣 **Anthropic** (Claude 4.5, Claude 4.1, Claude 3)
- 🟢 **Together.ai** (Llama, Kimi-K2, Gemma, DeepSeek, Qwen)
- 🔴 **Google Gemini** (Gemini 2.5 Pro, Flash, Lite)
- 🤗 **HuggingFace** (Lokal modeller, Transformers - Mac uyumlu)

## 🎯 Özellikler

- **İki Test Türü:**
  - **MCQ (Multiple Choice Questions)**: 131 çoktan seçmeli soru
  - **SAQ (Short Answer Questions)**: 422 açık uçlu soru

- **Esnek Model Desteği:**
  - OpenAI API (GPT-4, GPT-3.5-turbo, vb.)
  - Anthropic API (Claude 3 ailesi)
  - Together.ai API (Llama, Mixtral, vb.)
  - HuggingFace modelleri (vLLM ile lokal çalıştırma)

- **Otomatik Puanlama:**
  - GPT-4o ile objektif değerlendirme
  - MCQ için 0/100 puanlama
  - SAQ için 0-100 arası detaylı puanlama (Doğruluk, İçerik, Dil Kalitesi)

- **Kategori Bazlı Analiz:**
  - Türkçeye Özgü Dil Mekanikleri
  - Bağlamsal Anlam ve Çıkarım
  - Mantık ve Tutarlılık
  - Güvenlik ve Dürüstlük
  - Yaratıcı Dönüşüm ve Transfer
  - Ve daha fazlası...

- **Gelişmiş Özellikler:**
  - Kesintiye uğrayan testlerden devam etme
  - Ara sonuç kaydetme
  - Otomatik retry mekanizması
  - Detaylı JSON ve Markdown raporları
  - Güzel CLI çıktısı (Rich kütüphanesi)

## 📋 Gereksinimler

```bash
pip install -r requirements.txt
```

### API Anahtarları

Kullanmak istediğiniz provider'lar için API anahtarlarını environment variable olarak ayarlayın:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export TOGETHER_API_KEY="your-together-api-key"
```

## 🚀 Hızlı Başlangıç

### 1. OpenAI GPT-5 ile Test (Önerilen)

```bash
python3 benchmark.py --provider openai --model gpt-5-mini --test-type mcq
```

### 2. Anthropic Claude ile Test

```bash
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type mcq
```

### 3. Karşılaştırmalı Test (Hızlı Başlangıç)

```bash
python3 run_claude_comparison.py
```

### 4. HuggingFace Modeli (Lokal - Transformers)

```bash
python3 benchmark.py --provider huggingface --model meta-llama/Llama-3-8B --test-type mcq
```

**Not:** Mac'te CPU/Apple Silicon MPS ile çalışır. Küçük modeller önerilir (~7B).

## 📊 Test Kategorileri

### MCQ Kategorileri

1. **TÜRKÇEYE ÖZGÜ DİL MEKANİKLERİ**
   - Morfoloji Testleri
   - Ünlü Uyumu, Tamlayan-Tamlanan, Kaynaştırmalar
   - Ses Olayları (Düşme, Türeme, Yumuşama, Benzeşme)
   - Edge Case'ler (Yabancı Kökenli + Türkçe Ek, Özel İsim, Kısaltmalar)
   - Birleşik Kelimeler, Yazım ve Ekleşme
   - Karışık Testler

2. **BAĞLAMSAL ANLAM VE ÇIKARIM**
   - Gizli Özne / Bağlamsal Neden-Sonuç
   - Çok Anlamlılık / Bağlamdan Anlam Seçimi
   - Deyim ve Mecaz Çözümleme
   - Zamir Çözümleme / Gönderim Belirleme

3. **YARATICI DÖNÜŞÜM VE TRANSFER**
   - Stil Transferi
   - Analoji Üretimi
   - Format Dönüşümleri

### SAQ Kategorileri

1. **ARİTMETİK & KISA ADIMLI MUHAKEME**
2. **TALİMAT İZLEME / BİÇİM DAYATMASI**
3. **ÇOK-TUR BELLEK & ÇEKİRDEK BAŞVURU**
4. **DÜRÜSTLÜK/HALÜSİNASYON & GÜVENLİ RET**
5. **TÜRKÇE DİL KENAR DURUMLARI**
6. **KOD VE MİNİ DEBUG**
7. **UZUN-BAĞLAM DİSİPLİN & HEDEFLİ ÇIKARIM**
8. **ARAÇ KULLANIMI BİLİNCİ**
9. **TALİMAT TAKİP DİSİPLİNİ**
   - Çoklu Kısıtlama
   - Format Dayatma
   - Sıralı İşlemler
   - Çelişkili Talimatlar
   - Format İhlali Puanlama
10. **MANTIK VE TUTARLILIK**
    - Çelişki Kontrolü
    - Geçişlilik
    - Sayma Paradoksları
    - Kendine Referans
    - Klasik Mantık Hataları
    - Multi-Hop Reasoning
    - Tutarsızlık Tespiti
11. **GÜVENLİK VE DÜRÜSTLÜK**
    - Bilgi Sınırı Testleri
    - Halüsinasyon Tuzakları
    - Zararlı İçerik Reddi
    - Bilgi Doğrulama
    - Etik Sınır Testleri
    - Politik/Hassas Konular
    - Manipülasyon Testleri
    - Yanlış Bilgi Düzeltme
    - Özel Veri Güvenliği
    - Tıbbi/Hukuki Tavsiye
    - Çocuk Güvenliği
    - Bağımlılık/Zararlı Davranışlar
    - Komplo Teorileri
    - Sosyal Mühendislik
    - Sistem Güvenliği
12. **YARATICI DÖNÜŞÜM VE TRANSFER**
    - Stil Transferi
    - Analoji Üretimi
    - Format Dönüşümleri
    - Ters Problem Çözme

## 📈 Rapor Formatı

### Markdown Rapor Örneği

```
# TÜRKÇE BENCHMARK SONUÇLARI

**Model:** gpt-4
**Tarih:** 2024-10-26 15:30:00
**Test Tipi:** MCQ

---

## MCQ PERFORMANSI

**Toplam Soru:** 131
**Doğru Cevap:** 105
**Doğruluk Oranı:** 80.15%

**Yanıt Süreleri:**
- Ortalama: 1.23s
- Toplam: 161.13s

## KATEGORİ BAZLI SONUÇLAR

### BAĞLAMSAL ANLAM VE ÇIKARIM - Deyim ve Mecaz Çözümleme
- Toplam: 14 soru
- Doğru: 14 soru
- Doğruluk: **100.00%**

### TÜRKÇEYE ÖZGÜ DİL MEKANİKLERİ - Morfoloji Testleri
- Toplam: 40 soru
- Doğru: 35 soru
- Doğruluk: **87.50%**

...
```

### JSON Rapor

Detaylı JSON raporları şunları içerir:
- Her soru için model cevabı
- Judge değerlendirmesi ve puanı
- Yanıt süreleri
- Hata mesajları (varsa)
- Kategori bazlı istatistikler

## ⚙️ Konfigürasyon

`config.yaml` dosyasını düzenleyerek ayarları özelleştirebilirsiniz:

```yaml
# Judge model ayarları
judge:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 1000

# Test ayarları
test_settings:
  batch_size: 10
  timeout_seconds: 60
  save_intermediate: true
  max_retries: 3

# vLLM ayarları (HuggingFace modelleri için)
local:
  vllm_port: 8000
  gpu_memory_utilization: 0.9
  max_model_len: 4096
```

## 📊 Sonuç Karşılaştırma

Farklı modellerin performanslarını detaylı tablolarla karşılaştırın:

```bash
# Tüm MCQ sonuçlarını karşılaştır
python3 compare_results.py --type mcq

# Tüm SAQ sonuçlarını karşılaştır
python3 compare_results.py --type saq

# Her iki test tipini karşılaştır
python3 compare_results.py

# Belirli dosyaları karşılaştır
python3 compare_results.py results/gpt-3.5_mcq_*.json results/gpt-4_mcq_*.json
```

**Özellikler**:
- MCQ ve SAQ için ayrı tablolar
- Kategori bazlı detaylı karşılaştırma
- Renkli performans göstergeleri
- Otomatik sıralama ve kazanan belirleme

Detaylar için: `COMPARISON_GUIDE.md`

## 🔧 Gelişmiş Kullanım

### Kesintiden Devam Etme

Test yarıda kesilirse `--resume` flag'i ile kaldığı yerden devam edebilirsiniz:

```bash
python3 benchmark.py --provider openai --model gpt-4 --test-type all --resume
```

### Özel Konfigürasyon Dosyası

```bash
python3 benchmark.py --provider openai --model gpt-4 --config custom_config.yaml
```

### Sadece Belirli Test Tipini Çalıştırma

```bash
# Sadece MCQ
python3 benchmark.py --provider openai --model gpt-4 --test-type mcq

# Sadece SAQ
python3 benchmark.py --provider openai --model gpt-4 --test-type saq
```

## 📁 Proje Yapısı

```
Turkish-Benchmark/
├── benchmark.py                 # Ana script
├── config.example.yaml          # Konfigürasyon şablonu
├── requirements.txt             # Bağımlılıklar
├── README.md                    # Ana dokümantasyon
├── LICENSE                      # MIT License
│
├── src/                         # Kaynak kodlar
│   ├── __init__.py
│   ├── evaluator.py             # Test yürütücü
│   ├── judge.py                 # Puanlama sistemi
│   ├── reporter.py              # Rapor oluşturucu
│   ├── models/                  # Model wrapper'ları
│   │   ├── base_model.py        # Base sınıf
│   │   ├── api_models.py        # API modelleri (OpenAI, Claude, Gemini, Together)
│   │   └── local_models.py      # Lokal modeller (HuggingFace/Transformers)
│   └── utils/                   # Yardımcı modüller
│       ├── config_loader.py     # Config yükleyici
│       └── logger.py            # Logger
│
├── data/                        # Test verileri
│   ├── MCQ-Türkçe Benchmark.json  # 131 MCQ sorusu
│   └── SAQ-Türkçe-Benchmark.json  # 422 SAQ sorusu
│
├── docs/                        # Dokümantasyon
│   ├── QUICK_START.md           # Hızlı başlangıç
│   ├── USAGE_GUIDE.md           # Detaylı kullanım
│   ├── CONTRIBUTING.md          # Katkı rehberi
│   ├── MODELS.md                # Model listesi
│   └── ...
│
├── examples/                    # Örnek scriptler
│   ├── run_claude_comparison.py # Claude karşılaştırma
│   ├── run_gpt5_comparison.py   # GPT-5 karşılaştırma
│   └── run_comparison_test.py   # Genel karşılaştırma
│
├── tools/                       # Yardımcı araçlar
│   ├── model_registry.py        # Model kayıtları
│   ├── rescore.py               # Yeniden puanlama
│   ├── compare_results.py       # Sonuç karşılaştırma
│   ├── analyze_saq.py           # SAQ analiz
│   └── full_analysis.py         # Genel analiz
│
├── results/                     # Test sonuçları (gitignore'da)
│   └── intermediate/            # Ara sonuçlar
│
└── logs/                        # Log dosyaları (gitignore'da)
```

## 📚 Dokümantasyon

- **📖 [USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** - Detaylı kullanım kılavuzu (model seçimi, sorun giderme, örnekler)
- **🚀 [QUICK_START.md](docs/QUICK_START.md)** - Hızlı başlangıç rehberi
- **🤝 [CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Katkıda bulunma rehberi
- **🤖 [MODELS.md](docs/MODELS.md)** - Tüm desteklenen modeller
- **📋 README.md** - Bu dosya (genel bakış)

## 🛠️ Temel Araçlar

| Araç | Kullanım | Süre |
|------|----------|------|
| `benchmark.py` | Ana test scripti | 10-60 dk |
| `examples/run_claude_comparison.py` | Claude karşılaştırma | 25 dk |
| `examples/run_gpt5_comparison.py` | GPT-5 karşılaştırma | 20 dk |
| `tools/compare_results.py` | Sonuç karşılaştırma | Hızlı |
| `tools/model_registry.py` | Model kayıtları | Hızlı |
| `tools/analyze_saq.py` | SAQ detaylı analiz | Hızlı |
| `tools/rescore.py` | Yeniden puanlama | 2-5 dk |
| `tools/full_analysis.py` | Genel analiz | Hızlı |

## 🎯 İlk Adımınız

```bash
# Hızlı model karşılaştırma (ÖNERİLEN)
python3 examples/run_claude_comparison.py

# Model kayıtlarını görüntüle
python3 tools/model_registry.py

# Detaylı kılavuz
cat docs/USAGE_GUIDE.md
```

## 🤝 Katkıda Bulunma

Bu proje açık kaynaklıdır. Katkılarınızı bekliyoruz!

Detaylar için: [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📝 Lisans

MIT License - Detaylar için `LICENSE` dosyasına bakın.

## 🙏 Teşekkürler

- OpenAI, Anthropic, Together.ai ve HuggingFace ekiplerine
- vLLM ekibine hızlı inference için
- Türkçe dil araştırmacılarına

---

## 👤 Geliştirici

**Alican Kıraz**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/alican-kiraz/)
[![Twitter](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/AlicanKiraz0)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/AlicanKiraz0)
[![Medium](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@alican-kiraz1)

**GitHub:** [@alicankiraz1](https://github.com/alicankiraz1)

---

**Not:** Bu benchmark Türkçe dilinin karmaşıklıklarını test eder. Sonuçlar modellerin genel Türkçe yeteneklerini yansıtır.

