#!/bin/bash
# Turkish Benchmark System Installation Script

echo "=================================="
echo "TÜRKÇE BENCHMARK SİSTEMİ KURULUMU"
echo "=================================="
echo ""

# Check Python version
echo "Python versiyonu kontrol ediliyor..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [[ $python_major -gt 3 ]] || [[ $python_major -eq 3 && $python_minor -ge 8 ]]; then
    echo "✓ Python $python_version bulundu (gerekli: 3.8+)"
else
    echo "✗ Python 3.8 veya üzeri gerekli (mevcut: $python_version)"
    exit 1
fi

# Install dependencies
echo ""
echo "Bağımlılıklar yükleniyor..."

# Check if in virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Virtual environment tespit edildi: $VIRTUAL_ENV"
    pip install -r requirements.txt
else
    echo "Virtual environment tespit edilmedi, pip3 kullanılıyor..."
    pip3 install -r requirements.txt --user 2>/dev/null || pip3 install -r requirements.txt --break-system-packages
fi

if [ $? -eq 0 ]; then
    echo "✓ Bağımlılıklar başarıyla yüklendi"
else
    echo "✗ Bağımlılık yükleme başarısız"
    echo ""
    echo "Manuel kurulum için:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Create necessary directories
echo ""
echo "Klasörler oluşturuluyor..."
mkdir -p results/intermediate
mkdir -p logs
mkdir -p models
echo "✓ Klasörler oluşturuldu"

# Make scripts executable
echo ""
echo "Script'ler çalıştırılabilir yapılıyor..."
chmod +x benchmark.py
chmod +x example_usage.py
echo "✓ Script'ler hazır"

# Check for API keys
echo ""
echo "API anahtarları kontrol ediliyor..."
api_key_found=false

if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "✓ OPENAI_API_KEY bulundu"
    api_key_found=true
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "✓ ANTHROPIC_API_KEY bulundu"
    api_key_found=true
fi

if [ ! -z "$TOGETHER_API_KEY" ]; then
    echo "✓ TOGETHER_API_KEY bulundu"
    api_key_found=true
fi

if [ "$api_key_found" = false ]; then
    echo ""
    echo "⚠️  Hiçbir API anahtarı bulunamadı!"
    echo ""
    echo "En az bir API anahtarı ayarlamanız gerekiyor:"
    echo "  export OPENAI_API_KEY='sk-...'"
    echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "  export TOGETHER_API_KEY='...'"
    echo ""
fi

# Final message
echo ""
echo "=================================="
echo "KURULUM TAMAMLANDI!"
echo "=================================="
echo ""
echo "Hızlı başlangıç için:"
echo "  python3 benchmark.py --provider openai --model gpt-3.5-turbo --test-type mcq"
echo ""
echo "Detaylı bilgi için:"
echo "  cat README.md"
echo "  cat QUICK_START.md"
echo ""

