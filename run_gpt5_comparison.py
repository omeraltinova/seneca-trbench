#!/usr/bin/env python3
"""
GPT-5 Model Comparison Test
Tests GPT-5 family models and compares with GPT-3.5-turbo baseline.
"""

import os
import json
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')

from models import OpenAIModel
from evaluator import Evaluator
from judge import Judge
from reporter import Reporter
from utils import load_config, setup_logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_model(model_name, config, logger, num_questions=10):
    """Test a specific model."""
    
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold cyan]TEST: {model_name}[/bold cyan]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    # Create model
    model = OpenAIModel(model_name, config)
    
    # Setup
    console.print(f"[yellow]Model hazırlanıyor...[/yellow]")
    model.setup()
    console.print("[green]✓[/green] Model hazır\n")
    
    # Create temp test file with limited questions
    mcq_backup = config['paths']['mcq_data']
    with open(mcq_backup, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
    
    test_questions = all_questions[:num_questions]
    temp_file = f'temp_test_{model_name.replace("/", "_").replace(".", "_")}.json'
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(test_questions, f, ensure_ascii=False, indent=2)
    
    config['paths']['mcq_data'] = temp_file
    
    try:
        # Run test
        console.print(f"[yellow]Test çalıştırılıyor ({num_questions} soru)...[/yellow]")
        evaluator = Evaluator(config, model, logger)
        results = evaluator.run_test('mcq')
        
        # Score
        console.print(f"\n[yellow]Puanlama yapılıyor...[/yellow]")
        judge = Judge(config, logger)
        scored_results = judge.score_results(results, 'mcq')
        judge.cleanup()
        
        # Calculate stats
        reporter = Reporter(config)
        stats = reporter.calculate_statistics(scored_results, 'mcq')
        
        # Cleanup
        model.cleanup()
        
        return {
            'model': model_name,
            'stats': stats,
            'results': scored_results
        }
        
    finally:
        # Cleanup
        config['paths']['mcq_data'] = mcq_backup
        if Path(temp_file).exists():
            Path(temp_file).unlink()


def main():
    """Run GPT-5 comparison tests."""
    
    console.print(Panel.fit(
        "[bold green]GPT-5 MODELLERİ KARŞILAŞTIRMA TESTİ[/bold green]\n\n"
        "Bu test GPT-5 ailesini GPT-3.5-turbo ile karşılaştırır.\n"
        "10 MCQ sorusu ile hızlı performans değerlendirmesi yapar.",
        border_style="green"
    ))
    
    # Load config
    config = load_config('config.yaml')
    logger = setup_logger()
    
    # Models to test (Resmi API isimleri)
    test_configs = [
        'gpt-3.5-turbo',   # Baseline
        'gpt-5-nano',      # En hafif GPT-5
        'gpt-5-mini',      # Önerilen GPT-5 ⭐
        'gpt-5',           # Tam GPT-5
    ]
    
    console.print(f"\n[bold]Test Edilecek Modeller:[/bold]")
    for i, model in enumerate(test_configs, 1):
        console.print(f"  {i}. {model}")
    
    console.print("\n[yellow]⚠️  Not: Her model ~2-3 dakika + puanlama ~1-2 dakika sürer[/yellow]")
    console.print("[yellow]    Toplam tahmini süre: ~15-20 dakika[/yellow]\n")
    
    results_all = []
    
    # Test each model
    for model_name in test_configs:
        try:
            result = test_model(model_name, config, logger, num_questions=10)
            results_all.append(result)
        except Exception as e:
            console.print(f"[red]✗ Hata ({model_name}): {str(e)}[/red]")
            console.print(f"[yellow]  (Model henüz mevcut olmayabilir)[/yellow]")
            continue
    
    if not results_all:
        console.print("[red]Hiçbir test tamamlanamadı![/red]")
        return
    
    # Create comparison table
    console.print("\n" + "="*100)
    console.print("[bold green]GPT-5 KARŞILAŞTIRMA SONUÇLARI[/bold green]")
    console.print("="*100 + "\n")
    
    table = Table(title="Model Performans Karşılaştırması")
    table.add_column("Model", style="cyan")
    table.add_column("Doğru", justify="right", style="green")
    table.add_column("Doğruluk", justify="right", style="yellow")
    table.add_column("Not", justify="center", style="bold")
    table.add_column("Ort. Süre", justify="right", style="blue")
    table.add_column("Tahmini Maliyet", justify="right", style="magenta")
    
    # Calculate estimated costs
    cost_per_model = {
        'gpt-3.5-turbo': '$5',
        'gpt-5-nano': '$5',
        'gpt-5-mini': '$5',
        'gpt-5': '$7',
        'gpt-5-pro': '$37'
    }
    
    for result in results_all:
        stats = result['stats']
        model = result['model']
        grade = stats.get('grade', 'N/A')
        
        # Color grade
        grade_colors = {'A': 'bold green', 'B': 'green', 'C': 'yellow', 'D': 'yellow', 'E': 'red', 'F': 'bold red'}
        grade_color = grade_colors.get(grade, 'white')
        
        table.add_row(
            model,
            f"{stats['correct_answers']}/{stats['total_questions']}",
            f"{stats['accuracy']:.1f}%",
            f"[{grade_color}]{grade}[/{grade_color}]",
            f"{stats.get('response_time', {}).get('average', 0):.2f}s",
            cost_per_model.get(model, '~$5')
        )
    
    console.print(table)
    
    # Analysis
    if len(results_all) > 1:
        baseline = next((r for r in results_all if r['model'] == 'gpt-3.5-turbo'), None)
        gpt5_models = [r for r in results_all if r['model'] != 'gpt-3.5-turbo']
        
        if baseline and gpt5_models:
            baseline_acc = baseline['stats']['accuracy']
            
            console.print(f"\n[bold]GPT-5 vs GPT-3.5-turbo Karşılaştırması:[/bold]\n")
            
            for gpt5 in gpt5_models:
                gpt5_acc = gpt5['stats']['accuracy']
                improvement = gpt5_acc - baseline_acc
                
                if improvement > 0:
                    console.print(f"  [green]✓ {gpt5['model']}:[/green] +{improvement:.1f}% daha iyi")
                elif improvement < 0:
                    console.print(f"  [red]✗ {gpt5['model']}:[/red] {improvement:.1f}% daha kötü")
                else:
                    console.print(f"  [yellow]= {gpt5['model']}:[/yellow] Aynı performans")
    
    # Best model
    best = max(results_all, key=lambda x: x['stats']['accuracy'])
    console.print(f"\n[bold green]🏆 En İyi Performans:[/bold green] {best['model']} ({best['stats']['accuracy']:.1f}%)")
    
    # Save comparison
    timestamp = Path(results_all[0]['results'][0].question_id if results_all[0]['results'] else 0)
    from datetime import datetime
    comparison_file = Path('results') / f'gpt5_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    comparison_data = {
        'test_type': 'mcq',
        'num_questions': 10,
        'models': [
            {
                'model': r['model'],
                'accuracy': r['stats']['accuracy'],
                'grade': r['stats'].get('grade', 'N/A'),
                'correct': r['stats']['correct_answers'],
                'total': r['stats']['total_questions']
            }
            for r in results_all
        ]
    }
    
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)
    
    console.print(f"\n[green]✓ Karşılaştırma raporu:[/green] {comparison_file}")
    
    console.print("\n" + "="*100)
    console.print("[bold green]GPT-5 KARŞILAŞTIRMA TAMAMLANDI![/bold green]")
    console.print("="*100 + "\n")
    
    console.print("[bold]Sonraki Adımlar:[/bold]")
    console.print("  1. Tam MCQ testi: python3 benchmark.py --provider openai --model gpt-5-mini --test-type mcq")
    console.print("  2. Detaylı karşılaştırma: python3 compare_results.py --type mcq")
    console.print("  3. SAQ testi: python3 benchmark.py --provider openai --model gpt-5-mini --test-type saq\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Test iptal edildi.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Hata: {str(e)}[/red]")
        import traceback
        traceback.print_exc()

