# 📖 Kullanım Kılavuzu - Tüm Bilgiler

> Tüm kullanım senaryoları, model bilgileri ve sorun çözümleri bu dosyada.

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
pip install -r requirements.txt

# API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export TOGETHER_API_KEY="tgp_v1_..."
```

### 2. İlk Test

```bash
# Karşılaştırmalı test (10 soru, 4 model)
python3 examples/run_claude_comparison.py

# Veya tek model
python3 benchmark.py --provider openai --model gpt-5-mini --test-type mcq
```

---

## 🤖 Desteklenen Modeller (28 Model)

### OpenAI (GPT-5 Serisi)

```bash
# Genel kullanım
python3 benchmark.py --provider openai --model gpt-5 --test-type mcq
python3 benchmark.py --provider openai --model gpt-5-mini --test-type mcq

# Hız/ekonomi
python3 benchmark.py --provider openai --model gpt-5-nano --test-type mcq

# Chat ve Kod yetenekleri
python3 benchmark.py --provider openai --model gpt-5-chat-latest --test-type mcq
python3 benchmark.py --provider openai --model gpt-5-codex --test-type mcq
```

### Anthropic Claude (6 Model)

**Claude 4.5/4.1** (Türkçe için iyi):
```bash
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type mcq
python3 benchmark.py --provider anthropic --model claude-haiku-4-5-20251001 --test-type mcq
python3 benchmark.py --provider anthropic --model claude-opus-4-1-20250805 --test-type mcq
```

**Fiyat/Performans**:
- `claude-haiku-4-5`: $6 (MCQ) - Ekonomik
- `claude-sonnet-4-5`: $7 (MCQ) - **Önerilen** ⭐⭐
- `claude-opus-4-1`: $25 (MCQ) - En iyi 🏆

### Together.ai (8+ Model)

```bash
python3 benchmark.py --provider together --model meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo --test-type mcq
```

---

## ⚡ Hızlı Komutlar

### Temel Testler

```bash
# MCQ (131 soru, ~15 dk)
python3 benchmark.py --provider openai --model gpt-5-main-mini --test-type mcq

# SAQ (422 soru, ~10 dk - yeni optimizasyonla!)
python3 benchmark.py --provider openai --model gpt-5-main-mini --test-type saq

# Her ikisi
python3 benchmark.py --provider openai --model gpt-5-main-mini --test-type all
```

### Karşılaştırmalar

```bash
# Claude modelleri (5 model, 10 soru, ~25 dk)
python3 examples/run_claude_comparison.py

# GPT-5 modelleri (4 model, 10 soru, ~20 dk)
python3 examples/run_gpt5_comparison.py

# Genel (3 model, 10 soru, ~15 dk)
python3 examples/run_comparison_test.py
```

### Analiz Araçları

```bash
# Model kayıtları ve leaderboard
python3 tools/model_registry.py

# Tüm sonuçlar özeti
python3 tools/full_analysis.py

# MCQ karşılaştırma
python3 tools/compare_results.py --type mcq

# SAQ detaylı analiz
python3 tools/analyze_saq.py

# Sadece puanlama (test hatası durumunda)
python3 tools/rescore.py --type mcq
```

---

## 🔧 Sorun Giderme

### "command not found: python"

**Çözüm**: `python3` kullanın

```bash
# ❌ Yanlış
python benchmark.py ...

# ✅ Doğru
python3 benchmark.py ...
```

### "ModuleNotFoundError: No module named 'rich'"

**Çözüm**: Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### "API key not found"

**Çözüm**: Environment variable ayarlayın

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Kontrol
echo $OPENAI_API_KEY
```

### Puanlama Hatası (Kesinti/Network)

**Çözüm**: Sadece puanlama yapın

```bash
python3 rescore.py --type mcq
```

Test sonuçları `results/intermediate/` klasöründe kayıtlı!

### SAQ Puanlama Çok Yavaş (40 dk)

**Çözüm**: Paralel işleme zaten aktif, ama daha hızlı için:

`config.yaml`:
```yaml
judge:
  model: "gpt-5-nano"      # Ucuz ve hızlı
  parallel_workers: 20     # Daha fazla paralellik
```

**Sonuç**: 40 dk → 2-3 dk!

---

## 💰 Maliyet Rehberi

### MCQ Testi (131 soru)

| Model | Test | Judge | Toplam | Performans |
|-------|------|-------|--------|------------|
| gpt-5-nano | $0.08 | $5 | **$5** | C+ |
| gpt-5-mini | $0.42 | $5 | **$5** | A- ⭐ |
| claude-sonnet-4-5 | $0.50 | $5 | **$6** | A ⭐⭐ |
| gpt-5-pro | $32 | $5 | **$37** | A+ 🏆 |

### SAQ Testi (422 soru)

| Model | Test | Judge | Toplam | Performans |
|-------|------|-------|--------|------------|
| gpt-5-nano | $0.34 | $2* | **$2** | C 💰 |
| gpt-5-mini | $1.68 | $5* | **$7** | B+ ⭐ |
| claude-sonnet-4-5 | $2.55 | $5* | **$8** | A- ⭐⭐ |
| gpt-5-pro | $126 | $5* | **$131** | A+ 🏆 |

*Judge: gpt-5-nano kullanılırsa $2, gpt-4o kullanılırsa $20

---

## 🎯 Önerilen İş Akışı

### Yeni Başlayan İçin

```bash
# 1. Hızlı karşılaştırma (hangi model iyi?)
python3 examples/run_claude_comparison.py

# 2. Model kayıtlarını gör
python3 tools/model_registry.py

# 3. En iyi modelle tam MCQ
python3 benchmark.py --provider <provider> --model <kazanan-model> --test-type mcq

# 4. Sonuçları karşılaştır
python3 tools/compare_results.py --type mcq
```

### İleri Kullanıcı İçin

```bash
# 1. Hem GPT hem Claude karşılaştır
python3 examples/run_gpt5_comparison.py
python3 examples/run_claude_comparison.py

# 2. En iyi 2 modelle tam test
python3 benchmark.py --provider openai --model gpt-5-mini --test-type all
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type all

# 3. Detaylı analiz
python3 tools/full_analysis.py
python3 tools/compare_results.py
python3 tools/analyze_saq.py
```

---

## 📊 Performans Optimizasyonu

### Paralel Puanlama (Otomatik)

**Varsayılan**: 10 worker  
**Sonuç**: SAQ puanlama 40 dk → 4-5 dk (8x hızlı!)

### Daha Hızlı

`config.yaml`:
```yaml
judge:
  parallel_workers: 20  # 10 → 20
```

**Sonuç**: 4-5 dk → 2-3 dk

### Ultra Hızlı + Ekonomik

`config.yaml`:
```yaml
judge:
  model: "gpt-5-nano"      # Ucuz ve hızlı
  parallel_workers: 20
  max_tokens: 150
```

**Sonuç**:
- Süre: 40 dk → 2-3 dk (13x hızlı!)
- Maliyet: $20 → $2 (10x ucuz!)

---

## 🔄 Yeniden Puanlama

Test tamamlandı ama puanlama başarısız olduysa:

```bash
# MCQ
python3 rescore.py --type mcq

# SAQ
python3 rescore.py --type saq

# Belirli dosya
python3 rescore.py results/intermediate/mcq_intermediate.json
```

**Avantaj**: Test tekrar çalışmaz, sadece puanlama!

---

## 📈 Model Seçim Rehberi

### Maliyet Odaklı
- **En Ucuz**: gpt-5-nano ($5 MCQ + $2 SAQ = $7)
- **Dengeli**: gpt-5-mini ($5 MCQ + $7 SAQ = $12) ⭐

### Performans Odaklı
- **En İyi**: gpt-5-pro veya claude-opus-4-1 (~95% doğruluk) 🏆
- **Dengeli**: claude-sonnet-4-5 (~93% doğruluk) ⭐⭐

### Türkçe Odaklı
- **Önerilen**: claude-sonnet-4-5 (Claude Türkçe'de iyi)
- **Alternatif**: gpt-5-mini

### Hız Odaklı
- claude-haiku-4-5 (hızlı)
- gpt-5-nano (çok hızlı)

---

## 📊 Mevcut Test Sonuçları

**GPT-3.5-turbo**:
- MCQ: 80.15% (B)
- SAQ: 67.49/100 (D)
- Halüsinasyon: 19/100 🚨
- Üretim için: Sınırlı ⚠️

**Önerilen Modeller** (Test edilecek):
- gpt-5-mini: Beklenen A- (90%)
- claude-sonnet-4-5: Beklenen A (93%)

---

## 🎯 Sık Kullanılan Komutlar

```bash
# Karşılaştırma (ÖNERİLEN İLK ADIM)
python3 examples/run_claude_comparison.py

# Tam test
python3 benchmark.py --provider openai --model gpt-5-mini --test-type all

# Model kayıtları
python3 tools/model_registry.py

# Sonuç analizi
python3 tools/full_analysis.py

# Yeniden puanlama
python3 tools/rescore.py --type mcq

# Yardım
python3 benchmark.py --help
```

---

## 📞 Yardım ve Dokümantasyon

- **Hızlı Başlangıç**: `docs/QUICK_START.md`
- **Ana Dokümantasyon**: `README.md`
- **Bu Kılavuz**: `docs/USAGE_GUIDE.md`
- **Katkı**: `docs/CONTRIBUTING.md`
- **Model Listesi**: `docs/MODELS.md`

---

**Hemen başlayın**:
```bash
python3 examples/run_claude_comparison.py
```

