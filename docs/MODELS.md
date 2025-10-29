# 🤖 Desteklenen Modeller - Güncel Liste

**Son Güncelleme**: 28 Ekim 2025

---

## 🔵 OpenAI Modelleri (9 Model)

### GPT-5 Ailesi (7 Ağustos 2025 - En Yeni) ⭐

#### gpt-5-main
```bash
python3 benchmark.py --provider openai --model gpt-5-main --test-type mcq
```
- **Açıklama**: Genel amaçlı, en iyi GPT-5 modeli
- **Kullanım**: Karmaşık muhakeme, geniş bilgi gerektiren görevler
- **Halüsinasyon**: %80 daha az (GPT-4o'ya göre)
- **Performans**: A (90-95%)
- **Önerilen**: Kritik uygulamalar

#### gpt-5-main-mini ⭐ ÖNERİLEN
```bash
python3 benchmark.py --provider openai --model gpt-5-main-mini --test-type mcq
```
- **Açıklama**: Hafif ve hızlı, dengeli performans
- **Kullanım**: Günlük kullanım, orta karmaşıklık
- **Halüsinasyon**: Çok düşük
- **Performans**: A- (88-92%)
- **Önerilen**: **İLK SEÇİM** - Maliyet/performans dengesi mükemmel

#### gpt-5-thinking
```bash
python3 benchmark.py --provider openai --model gpt-5-thinking --test-type mcq
```
- **Açıklama**: Derinlemesine analiz için
- **Kullanım**: Karmaşık mantık, çok adımlı muhakeme
- **Halüsinasyon**: Minimal
- **Performans**: A+ (93-97%)
- **Önerilen**: Mantık ve tutarlılık soruları için

#### gpt-5-thinking-mini
```bash
python3 benchmark.py --provider openai --model gpt-5-thinking-mini --test-type mcq
```
- **Açıklama**: Düşünen modelin kompakt versiyonu
- **Kullanım**: Orta seviye mantık soruları
- **Performans**: A- (90-93%)

#### gpt-5-thinking-nano
```bash
python3 benchmark.py --provider openai --model gpt-5-thinking-nano --test-type mcq
```
- **Açıklama**: En hafif düşünen model
- **Kullanım**: Basit mantık, hızlı yanıt
- **Performans**: B+ (85-88%)
- **Önerilen**: Hızlı iterasyon, düşük maliyet

### GPT-4 Ailesi (Legacy)

#### gpt-4o
```bash
python3 benchmark.py --provider openai --model gpt-4o --test-type mcq
```
- **Performans**: B+ (85-88%)
- **Durum**: Hala güçlü, GPT-5'ten biraz düşük

#### gpt-4o-mini
```bash
python3 benchmark.py --provider openai --model gpt-4o-mini --test-type mcq
```
- **Performans**: B (80-85%)
- **Durum**: Ekonomik alternatif

#### gpt-4-turbo, gpt-4, gpt-3.5-turbo
- Legacy modeller
- Hala kullanılabilir ama GPT-5 önerilir

---

## 🟣 Anthropic Claude Modelleri (6 Model)

### Claude 4.5 Ailesi (29 Eylül 2025 - En Yeni) ⭐

#### claude-sonnet-4-5-20250929 ⭐⭐ ÖNERİLEN
```bash
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type mcq
```
- **Açıklama**: En iyi Claude modeli - Kodlama ve ajan görevleri
- **Kullanım**: Genel kullanım, Türkçe'de mükemmel
- **Halüsinasyon**: Çok düşük
- **Performans**: A (92-95%)
- **Fiyat**: $3/$15 per 1M token
- **Önerilen**: **Türkçe için en iyi seçim olabilir**

#### claude-haiku-4-5-20251001
```bash
python3 benchmark.py --provider anthropic --model claude-haiku-4-5-20251001 --test-type mcq
```
- **Açıklama**: Hızlı ve ekonomik
- **Performans**: B+ (85-88%)
- **Önerilen**: Yüksek hacim, düşük maliyet

### Claude 4.1 Ailesi

#### claude-opus-4-1-20250805 🏆
```bash
python3 benchmark.py --provider anthropic --model claude-opus-4-1-20250805 --test-type mcq
```
- **Açıklama**: Premium - Özel akıl yürütme
- **Performans**: A+ (95-98%)
- **Fiyat**: $15/$75 per 1M token
- **Önerilen**: Maksimum performans gerekiyorsa

### Claude 3 (Legacy)
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3-haiku-20240307

---

## 🟢 Together.ai Modelleri (8+ Model)

```bash
python3 benchmark.py --provider together --model meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo --test-type mcq
```

**Mevcut Modeller**:
- meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
- meta-llama/Llama-3-70b-chat-hf
- mistralai/Mixtral-8x7B-Instruct-v0.1
- NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO

**Not**: Open source modeller Türkçe'de zayıf (%40-60), GPT/Claude önerilir.

---

## 🎯 Model Seçim Rehberi

### İLK TEST İÇİN (ÖNERİLEN)

**Karşılaştırmalı Test**:
```bash
python3 run_claude_comparison.py
```

**Test Edecek**:
1. GPT-3.5-turbo (baseline)
2. Claude-Haiku-4-5 (ekonomik)
3. Claude-Sonnet-4-5 (önerilen) ⭐⭐
4. GPT-5-main-mini (önerilen) ⭐

**Süre**: 25-30 dakika  
**Maliyet**: ~$5-8  
**Sonuç**: Hangi model sizin için en iyi?

### ÜRETİM İÇİN

**1. Seçim**: `claude-sonnet-4-5-20250929`
- Türkçe'de mükemmel
- Halüsinasyon çok düşük
- Dengeli maliyet

**2. Seçim**: `gpt-5-main-mini`
- GPT-5 teknolojisi
- Hızlı ve ekonomik
- İyi performans

### KRİTİK UYGULAMALAR İÇİN

**1. Seçim**: `claude-opus-4-1-20250805` 🏆
- En yüksek doğruluk
- Halüsinasyon neredeyse yok
- Mantık ve muhakemede en iyi

**2. Seçim**: `gpt-5-thinking`
- Derinlemesine analiz
- Karmaşık mantık
- Çok adımlı muhakeme

### EKONOMİK KULLANIM İÇİN

**1. Seçim**: `gpt-5-thinking-nano`
- Ultra hızlı
- Çok ucuz
- Basit görevler için yeterli

**2. Seçim**: `claude-haiku-4-5-20251001`
- Hızlı
- Ekonomik
- Orta performans

---

## 📊 Model Karşılaştırması (Tahmini)

| Model | MCQ Doğruluk | SAQ Puan | Halüsinasyon | Maliyet (MCQ+SAQ) |
|-------|--------------|----------|--------------|-------------------|
| **claude-sonnet-4-5** | 93-95% | 87-90 | 85-90 | ~$40 ⭐⭐ |
| **gpt-5-main-mini** | 90-92% | 82-85 | 75-80 | ~$15 ⭐ |
| **gpt-5-thinking** | 95-97% | 90-93 | 90-95 | ~$50 🏆 |
| **claude-opus-4-1** | 96-98% | 92-95 | 95+ | ~$110 🏆🏆 |
| gpt-5-thinking-nano | 85-88% | 75-78 | 65-70 | ~$8 💰 |
| gpt-4o-mini | 82-85% | 75-80 | 60-70 | ~$15 |
| gpt-3.5-turbo | 80% | 67 | 19 🚨 | ~$30 ✅ Test edildi |

---

## 🚀 Hızlı Başlangıç Komutları

### Test 1: Hızlı Karşılaştırma (ÖNERİLEN İLK ADIM)

```bash
python3 run_claude_comparison.py
```

**Sonuç**: Hangi model en iyi performansı veriyor?

### Test 2: GPT-5-main-mini Tam MCQ

```bash
python3 benchmark.py --provider openai --model gpt-5-main-mini --test-type mcq
```

**Beklenen**: ~90% (GPT-3.5'ten +10%)

### Test 3: Claude-Sonnet-4-5 Tam MCQ

```bash
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type mcq
```

**Beklenen**: ~93% (GPT-3.5'ten +13%)

### Test 4: Model Kayıtlarını Gör

```bash
python3 model_registry.py
```

**Gösterir**: Tüm test edilmiş modeller ve leaderboard

---

## ⚠️ HATIRLATMALAR

### Model İsimleri Değişti!

❌ **Eski (Yanlış)**:
- gpt-5
- gpt-5-mini
- gpt-5-nano
- gpt-5-pro

✅ **Yeni (Doğru)**:
- gpt-5-main
- gpt-5-main-mini
- gpt-5-thinking-nano
- gpt-5-thinking

### Python Komutu

❌ `python` kullanmayın  
✅ `python3` kullanın

---

## 📖 Daha Fazla Bilgi

- Detaylı kullanım: `USAGE_GUIDE.md`
- Hızlı başlangıç: `QUICK_START.md`
- Ana dokümantasyon: `README.md`

---

**Hemen test edin**:
```bash
python3 run_claude_comparison.py
```

Güncel model isimleriyle artık çalışacak! 🚀

