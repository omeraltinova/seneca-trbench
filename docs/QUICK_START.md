# Hızlı Başlangıç Kılavuzu

Bu kılavuz, Türkçe Benchmark Sistemini 5 dakikada çalıştırmanız için hazırlanmıştır.

## 1. Kurulum (2 dakika)

### Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### API Anahtarınızı Ayarlayın

En az bir provider için API key'inizi ayarlamanız gerekiyor:

**macOS/Linux:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

## 2. İlk Testinizi Çalıştırın (3 dakika)

### Basit Test (OpenAI GPT-5 ile) - ÖNERİLEN

```bash
python3 benchmark.py --provider openai --model gpt-5-mini --test-type mcq
```

Bu komut:
- OpenAI'ın GPT-5-mini modelini test eder (en yeni!)
- Sadece MCQ (çoktan seçmeli) sorularını çalıştırır
- Yaklaşık 10-15 dakika sürer
- Beklenen: ~90% doğruluk (GPT-3.5'ten çok daha iyi!)
- Sonuçları `results/` klasörüne kaydeder

### Alternatif: GPT-3.5 ile Test (Daha Ucuz)

```bash
python3 benchmark.py --provider openai --model gpt-3.5-turbo --test-type mcq
```

### Alternatif: Claude ile Test

```bash
python3 benchmark.py --provider anthropic --model claude-sonnet-4-5-20250929 --test-type mcq
```

### Tüm Testleri Çalıştırma

```bash
python3 benchmark.py --provider openai --model gpt-4 --test-type all
```

⚠️ **Uyarı:** Tüm testler (MCQ + SAQ) yaklaşık 1-2 saat sürebilir ve API maliyeti oluşturur.

## 3. Sonuçları İnceleyin

Test tamamlandığında sonuçlar şurada olacak:

```
results/
├── gpt-3.5-turbo_mcq_20241026_153045.json     # Detaylı JSON raporu
└── gpt-3.5-turbo_mcq_20241026_153045.md       # Okunabilir Markdown raporu
```

Markdown raporunu herhangi bir text editörde açabilirsiniz.

## 4. Diğer Provider'ları Deneyin

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
python3 benchmark.py --provider anthropic --model claude-3-haiku-20240307 --test-type mcq
```

### Together.ai

```bash
export TOGETHER_API_KEY="your-key"
python3 benchmark.py --provider together --model meta-llama/Llama-3-8b-chat-hf --test-type mcq
```

### HuggingFace (Lokal)

⚠️ **GPU gerektirir**

```bash
python3 benchmark.py --provider huggingface --model meta-llama/Llama-3-8B --test-type mcq
```

Model otomatik olarak indirilir ve vLLM ile çalıştırılır.

## 5. Kesintiden Devam Etme

Test yarıda kesilirse:

```bash
python3 benchmark.py --provider openai --model gpt-4 --test-type all --resume
```

## Yaygın Sorunlar

### "API key not found"

API anahtarınızı environment variable olarak ayarladığınızdan emin olun:

```bash
echo $OPENAI_API_KEY  # Boş değilse doğru
```

### "Model not found"

Model adını kontrol edin. Örnek doğru model adları:
- OpenAI: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- Together: `meta-llama/Llama-3-70b-chat-hf`

### vLLM Hatası (HuggingFace modelleri)

- GPU'nuz olduğundan emin olun
- CUDA driver'ların yüklü olduğunu kontrol edin
- `config.yaml` dosyasındaki `gpu_memory_utilization` değerini düşürün (0.9 → 0.7)

## İleri Düzey

### Konfigürasyonu Özelleştirme

`config.yaml` dosyasını düzenleyin:

```yaml
judge:
  model: "gpt-4o"  # Puanlama modeli
  temperature: 0.1

test_settings:
  batch_size: 10      # Her 10 soruda bir kaydet
  timeout_seconds: 60  # Soru başına timeout
```

### Programatik Kullanım

```python
from src.models import OpenAIModel
from src.evaluator import Evaluator
from src.judge import Judge
from src.reporter import Reporter
from src.utils import load_config

config = load_config('config.yaml')
model = OpenAIModel('gpt-4', config)
model.setup()

evaluator = Evaluator(config, model)
results = evaluator.run_test('mcq')

judge = Judge(config)
scored_results = judge.score_results(results, 'mcq')

reporter = Reporter(config)
report = reporter.generate_report(scored_results, 'mcq', 'gpt-4', 'openai')
```

## Yardım

Daha fazla bilgi için:
- `README.md` - Detaylı dokümantasyon
- `python3 benchmark.py --help` - Komut satırı yardımı
- GitHub Issues - Sorun bildirimi

## Maliyet Tahmini

**MCQ Testi (131 soru):**
- GPT-3.5-turbo: ~$2-3
- GPT-4: ~$15-20
- Judge (GPT-4o): ~$5-10

**SAQ Testi (422 soru):**
- GPT-3.5-turbo: ~$5-10
- GPT-4: ~$40-60
- Judge (GPT-4o): ~$20-30

**Toplam (Her İki Test):**
- GPT-3.5-turbo: ~$10-15
- GPT-4: ~$70-100

*Not: Fiyatlar tahmindir ve API fiyatlandırmasına göre değişebilir.*

---

Herhangi bir sorunla karşılaşırsanız issue açmaktan çekinmeyin!

