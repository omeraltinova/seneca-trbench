# Katkıda Bulunma Rehberi

Türkçe Benchmark projesine katkıda bulunmak istediğiniz için teşekkürler! 🎉

## Katkı Yapma Yolları

1. **Yeni Sorular Eklemek**
   - MCQ veya SAQ kategorilerine yeni sorular ekleyebilirsiniz
   - Soruların Türkçe dil kurallarına uygun olduğundan emin olun
   - Kategori belirtin ve doğru cevabı sağlayın

2. **Kod İyileştirmeleri**
   - Bug fix'ler
   - Performans optimizasyonları
   - Yeni özellikler
   - Dokümantasyon güncellemeleri

3. **Yeni Model Desteği**
   - Farklı API provider'ları
   - Yeni model wrapper'ları

4. **Test ve Hata Raporları**
   - Bug'ları bildirin
   - Test coverage'ı artırın
   - Edge case'leri belirleyin

## Geliştirme Süreci

### 1. Projeyi Fork Edin

```bash
git clone https://github.com/your-username/Turkish-Benchmark.git
cd Turkish-Benchmark
```

### 2. Geliştirme Ortamını Kurun

```bash
# Virtual environment oluşturun (önerilir)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Development bağımlılıkları (opsiyonel)
pip install black flake8 pytest
```

### 3. Branch Oluşturun

```bash
git checkout -b feature/amazing-feature
```

Branch isimlendirme:
- `feature/` - Yeni özellik
- `fix/` - Bug fix
- `docs/` - Dokümantasyon
- `refactor/` - Kod iyileştirme

### 4. Değişikliklerinizi Yapın

**Kod Stili:**
- PEP 8 standartlarına uyun
- Type hints kullanın
- Docstring'ler ekleyin
- Açıklayıcı değişken isimleri kullanın

**Örnek:**

```python
def calculate_score(results: List[TestResult], test_type: str) -> float:
    """
    Calculate average score from test results.
    
    Args:
        results: List of test results
        test_type: Type of test ('mcq' or 'saq')
        
    Returns:
        Average score as float
    """
    scores = [r.score for r in results if r.score is not None]
    return sum(scores) / len(scores) if scores else 0.0
```

### 5. Test Edin

```bash
# Syntax kontrolü
python3 -m py_compile your_file.py

# Kod formatı (black kullanıyorsanız)
black .

# Linting (flake8 kullanıyorsanız)
flake8 .

# Manuel test
python3 benchmark.py --provider openai --model gpt-3.5-turbo --test-type mcq
```

### 6. Commit Edin

Commit mesajları açıklayıcı olmalı:

```bash
git add .
git commit -m "feat: Add support for Gemini API"
```

Commit mesaj formatı:
- `feat:` - Yeni özellik
- `fix:` - Bug fix
- `docs:` - Dokümantasyon
- `refactor:` - Kod iyileştirme
- `test:` - Test ekleme
- `chore:` - Bakım işleri

### 7. Push ve Pull Request

```bash
git push origin feature/amazing-feature
```

GitHub'da Pull Request açın ve şunları ekleyin:
- Değişikliklerin açıklaması
- Test sonuçları
- İlgili issue numarası (varsa)
- Screenshot'lar (UI değişikliği varsa)

## Yeni Soru Ekleme

### MCQ Sorusu

```json
{
  "Test Kategorisi": "TÜRKÇEYE ÖZGÜ DİL MEKANİKLERİ - Morfoloji Testleri",
  "Soru": "\"kitap\" kökünden \"kitaplarımızdakiler\" doğru yazımı hangisi?\nA) kitaplarımızdakiler\nB) kitaplarımızda'kiler\nC) kitap'larımızdakiler\nD) kitaplarımız'dakiler",
  "Cevap": "Doğru cevap: A"
}
```

### SAQ Sorusu

```json
{
  "Test Kategorisi": "ARİTMETİK & KISA ADIMLI MUHAKEME",
  "Soru": "15 × 4 + 8 = ?",
  "Cevap": "68"
}
```

**Soru Kriterleri:**
- Türkçe dilbilgisi kurallarına uygun
- Net ve anlaşılır
- Tek bir doğru cevabı olmalı
- Kategori uygun olmalı
- Zorluk seviyesi dengeli

## Code Review Süreci

Pull request'iniz şu kriterler üzerinden değerlendirilir:

1. **Kod Kalitesi**
   - PEP 8 uyumu
   - Type hints
   - Docstring'ler
   - Clean code prensipleri

2. **Fonksiyonellik**
   - Özellik çalışıyor mu?
   - Edge case'ler ele alınmış mı?
   - Hata yönetimi var mı?

3. **Test**
   - Manuel test yapılmış mı?
   - Test sonuçları paylaşılmış mı?

4. **Dokümantasyon**
   - README güncel mi?
   - Kod yorumları yeterli mi?
   - Örnek kullanım var mı?

## Soru ve Öneri

- GitHub Issues kullanın
- Açık ve net sorular sorun
- Mümkünse örnek kod paylaşın
- Hata mesajlarını tam olarak kopyalayın

## Davranış Kuralları

- Saygılı ve yapıcı olun
- Eleştirileri olumlu karşılayın
- Yardımsever olun
- Kapsayıcı bir topluluk oluşturalım

## Lisans

Katkılarınız MIT lisansı altında yayınlanacaktır.

---

Teşekkürler! 🙏

