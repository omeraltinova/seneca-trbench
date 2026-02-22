#!/usr/bin/env python3
"""
SAQ Results Deep Analysis Tool
Provides detailed analysis of SAQ test results with actionable insights.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def analyze_saq_file(file_path: Path):
    """Analyze a single SAQ result file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    model_name = data['metadata'].get('model_name') or data['metadata'].get('model', 'unknown')
    stats = data['statistics']
    
    console.print(Panel.fit(
        f"[bold cyan]SAQ DETAYLI ANALİZ RAPORU[/bold cyan]\n\n"
        f"Model: {model_name}\n"
        f"Toplam Soru: {stats['total_questions']}\n"
        f"Genel Not: {stats.get('grade', 'N/A')}"
        , border_style="cyan"
    ))
    
    # Overall stats
    console.print(f"\n[bold]GENEL PERFORMANS:[/bold]")
    console.print(f"  • Ortalama Puan: {stats['average_score']:.2f}/100")
    console.print(f"  • Puan Aralığı: {stats['min_score']:.2f} - {stats['max_score']:.2f}")
    console.print(f"  • Harf Notu: {stats.get('grade', 'N/A')}")
    
    # Category analysis
    category_scores = stats.get('category_scores', {})
    
    if not category_scores:
        console.print("\n[yellow]Kategori bilgisi bulunamadı[/yellow]")
        return
    
    # Group categories by performance level
    excellent = []  # 90+
    good = []  # 70-89
    acceptable = []  # 50-69
    weak = []  # 30-49
    critical = []  # <30
    
    for cat, cat_stats in category_scores.items():
        score = cat_stats['average_score']
        item = (cat, score, cat_stats['total'])
        
        if score >= 90:
            excellent.append(item)
        elif score >= 70:
            good.append(item)
        elif score >= 50:
            acceptable.append(item)
        elif score >= 30:
            weak.append(item)
        else:
            critical.append(item)
    
    # Create performance table
    console.print(f"\n[bold]PERFORMANS DAĞILIMI:[/bold]\n")
    
    perf_table = Table(show_header=True, header_style="bold")
    perf_table.add_column("Seviye", style="cyan")
    perf_table.add_column("Kategori Sayısı", justify="right")
    perf_table.add_column("Puan Aralığı", justify="right")
    perf_table.add_column("Durum")
    
    perf_table.add_row("🟢 Mükemmel", str(len(excellent)), "90-100", "Üretim için uygun ✅")
    perf_table.add_row("🟢 İyi", str(len(good)), "70-89", "Kabul edilebilir ✅")
    perf_table.add_row("🟡 Orta", str(len(acceptable)), "50-69", "Dikkatli kullanılmalı ⚠️")
    perf_table.add_row("🟠 Zayıf", str(len(weak)), "30-49", "Önerilmez ❌")
    perf_table.add_row("🔴 Kritik", str(len(critical)), "<30", "Kullanılmamalı 🚨")
    
    console.print(perf_table)
    
    # Show critical categories
    if critical:
        console.print(f"\n[bold red]🚨 KRİTİK UYARI - HALÜSINASYON RİSKİ YÜKSEK![/bold red]\n")
        
        crit_table = Table(title="Kritik Düşük Performanslı Kategoriler", show_header=True)
        crit_table.add_column("Kategori", style="red", width=60)
        crit_table.add_column("Puan", justify="right", style="bold red")
        crit_table.add_column("Soru Sayısı", justify="right")
        
        for cat, score, count in sorted(critical, key=lambda x: x[1]):
            crit_table.add_row(cat, f"{score:.2f}/100", str(count))
        
        console.print(crit_table)
        console.print("\n[bold yellow]⚠️  Öneri:[/bold yellow] Bu kategorilerde model [bold red]güvenilir değil[/bold red]. Üretim kullanımında bu alanlarda farklı model veya kontrol mekanizması kullanın.\n")
    
    # Show excellent categories
    if excellent:
        console.print(f"\n[bold green]✅ GÜÇLÜ KATEGORİLER[/bold green]\n")
        
        exc_table = Table(title="Mükemmel Performans Kategorileri", show_header=True)
        exc_table.add_column("Kategori", style="green", width=60)
        exc_table.add_column("Puan", justify="right", style="bold green")
        exc_table.add_column("Soru Sayısı", justify="right")
        
        for cat, score, count in sorted(excellent, key=lambda x: x[1], reverse=True):
            exc_table.add_row(cat, f"{score:.2f}/100", str(count))
        
        console.print(exc_table)
    
    # Recommendations
    console.print(f"\n[bold]💡 ÖNERİLER:[/bold]\n")
    
    overall_score = stats['average_score']
    grade = stats.get('grade', 'N/A')
    
    if overall_score >= 80:
        console.print(f"  ✅ [green]Model genel olarak iyi performans gösteriyor (Not: {grade})[/green]")
        console.print(f"  ✅ Çoğu kategori için üretimde kullanılabilir")
    elif overall_score >= 60:
        console.print(f"  ⚠️  [yellow]Model orta düzeyde performans gösteriyor (Not: {grade})[/yellow]")
        console.print(f"  ⚠️  Kritik uygulamalar için yetersiz olabilir")
    else:
        console.print(f"  ❌ [red]Model düşük performans gösteriyor (Not: {grade})[/red]")
        console.print(f"  ❌ Üretim kullanımı önerilmez")
    
    if critical:
        console.print(f"  🚨 [bold red]{len(critical)} kritik kategori tespit edildi - Halüsinasyon riski![/bold red]")
    
    if len(weak) + len(critical) > len(excellent):
        console.print(f"  💡 Daha güçlü bir model deneyin (ör: GPT-4o, Claude Sonnet, Gemini Pro)")
    
    console.print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SAQ test sonuçlarını detaylı analiz et",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # En son SAQ sonucunu analiz et
  python analyze_saq.py
  
  # Belirli dosyayı analiz et
  python analyze_saq.py results/gpt-3.5-turbo_saq_20251028_040622.json
  
  # Tüm SAQ sonuçlarını karşılaştır
  python analyze_saq.py --all
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='Analiz edilecek JSON dosyası (belirtilmezse en son SAQ dosyası)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Tüm SAQ dosyalarını karşılaştır'
    )
    
    args = parser.parse_args()
    
    results_dir = Path('results')
    
    if args.all:
        # Compare all SAQ results
        saq_files = sorted(results_dir.glob('*_saq_*.json'))
        if not saq_files:
            console.print("[red]SAQ sonuç dosyası bulunamadı![/red]")
            return
        
        console.print(f"\n[bold cyan]Bulunan SAQ Dosyaları: {len(saq_files)}[/bold cyan]\n")
        for f in saq_files:
            console.print(f"  • {f.name}")
        
        console.print("\n" + "="*100 + "\n")
        
        # Use compare_results.py for comparison
        import os
        os.system(f"python compare_results.py --type saq")
        
    elif args.file:
        # Analyze specific file
        file_path = Path(args.file)
        if not file_path.exists():
            console.print(f"[red]Dosya bulunamadı: {file_path}[/red]")
            return
        
        analyze_saq_file(file_path)
        
    else:
        # Find latest SAQ file
        saq_files = sorted(results_dir.glob('*_saq_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not saq_files:
            console.print("[red]SAQ sonuç dosyası bulunamadı![/red]")
            console.print("Önce SAQ testi çalıştırın:")
            console.print("  python benchmark.py --provider <provider> --model <model> --test-type saq")
            console.print("  Örnek: python benchmark.py --provider openrouter --model openai/gpt-4o --test-type saq")
            return
        
        latest_file = saq_files[0]
        console.print(f"[cyan]Analiz ediliyor: {latest_file.name}[/cyan]\n")
        analyze_saq_file(latest_file)


if __name__ == '__main__':
    main()

