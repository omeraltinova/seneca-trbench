#!/usr/bin/env python3
"""
Comparison test script - Tests multiple models and compares results.
Tests first 10 MCQ questions with different models.
"""

import os
import json
from pathlib import Path

# Set API keys
os.environ['TOGETHER_API_KEY'] = "tgp_v1_FaDTR9zIxPUgIj94EaPGA7ebRBe1LYClp9JLWGXQ1JQ"
os.environ['OPENAI_API_KEY'] = "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"

from models import OpenAIModel, TogetherModel
from evaluator import Evaluator
from judge import Judge
from reporter import Reporter
from utils import load_config, setup_logger
from rich.console import Console
from rich.table import Table

console = Console()


def test_model(provider, model_name, config, logger, num_questions=10):
    """Test a specific model."""
    
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold cyan]TEST: {provider}/{model_name}[/bold cyan]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    # Create model
    if provider == 'openai':
        model = OpenAIModel(model_name, config)
    elif provider == 'together':
        model = TogetherModel(model_name, config)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Setup
    console.print(f"[yellow]Model hazırlanıyor...[/yellow]")
    model.setup()
    console.print("[green]✓[/green] Model hazır\n")
    
    # Create temp test file with limited questions
    mcq_backup = config['paths']['mcq_data']
    with open(mcq_backup, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
    
    test_questions = all_questions[:num_questions]
    temp_file = f'temp_test_{provider}_{model_name.replace("/", "_")}.json'
    
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
            'provider': provider,
            'model': model_name,
            'stats': stats,
            'results': scored_results
        }
        
    finally:
        # Cleanup
        config['paths']['mcq_data'] = mcq_backup
        if Path(temp_file).exists():
            Path(temp_file).unlink()


def save_comparison_report(results_all):
    """Save comparison report to JSON file."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path('results') / f'comparison_report_{timestamp}.json'
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'num_questions': results_all[0]['stats']['total_questions'] if results_all else 0,
        'models': []
    }
    
    for result in results_all:
        model_data = {
            'provider': result['provider'],
            'model': result['model'],
            'accuracy': result['stats']['accuracy'],
            'correct': result['stats']['correct_answers'],
            'total': result['stats']['total_questions'],
            'avg_response_time': result['stats'].get('response_time', {}).get('average', 0)
        }
        report_data['models'].append(model_data)
    
    # Sort by accuracy
    report_data['models'].sort(key=lambda x: x['accuracy'], reverse=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    console.print(f"\n[green]✓ Karşılaştırma raporu kaydedildi:[/green] {report_file}")


def main():
    """Run comparison tests."""
    
    console.print("\n[bold green]TÜRKÇE BENCHMARK - KARŞILAŞTIRMALI TEST[/bold green]\n")
    
    # Load config
    config = load_config('config.yaml')
    logger = setup_logger()
    
    # Models to test
    test_configs = [
        ('openai', 'gpt-3.5-turbo'),                           # Baseline (ucuz)
        ('openai', 'gpt-4o-mini'),                             # GPT-4 dengeli
        ('together', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo'),  # Open source
    ]
    
    results_all = []
    
    # Test each model
    for provider, model_name in test_configs:
        try:
            result = test_model(provider, model_name, config, logger, num_questions=10)
            results_all.append(result)
        except Exception as e:
            console.print(f"[red]✗ Hata ({provider}/{model_name}): {str(e)}[/red]")
            continue
    
    # Create comparison table
    console.print("\n" + "="*80)
    console.print("[bold green]SONUÇLAR[/bold green]")
    console.print("="*80 + "\n")
    
    table = Table(title="Model Karşılaştırması")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Doğru", justify="right", style="green")
    table.add_column("Doğruluk", justify="right", style="yellow")
    table.add_column("Ort. Süre", justify="right", style="blue")
    
    for result in results_all:
        stats = result['stats']
        table.add_row(
            result['provider'],
            result['model'],
            f"{stats['correct_answers']}/{stats['total_questions']}",
            f"{stats['accuracy']:.1f}%",
            f"{stats.get('response_time', {}).get('average', 0):.2f}s"
        )
    
    console.print(table)
    
    # Find best model
    if results_all:
        best = max(results_all, key=lambda x: x['stats']['accuracy'])
        worst = min(results_all, key=lambda x: x['stats']['accuracy'])
        fastest = min(results_all, key=lambda x: x['stats'].get('response_time', {}).get('average', float('inf')))
        
        console.print(f"\n[bold green]🏆 En İyi Performans:[/bold green] {best['provider']}/{best['model']} ({best['stats']['accuracy']:.1f}%)")
        console.print(f"[bold red]❌ En Zayıf Performans:[/bold red] {worst['provider']}/{worst['model']} ({worst['stats']['accuracy']:.1f}%)")
        console.print(f"[bold blue]⚡ En Hızlı:[/bold blue] {fastest['provider']}/{fastest['model']} ({fastest['stats'].get('response_time', {}).get('average', 0):.2f}s/soru)")
    
    console.print("\n" + "="*80)
    console.print("[bold green]TEST TAMAMLANDI![/bold green]")
    console.print("="*80 + "\n")
    
    # Save comparison report
    if results_all:
        save_comparison_report(results_all)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Test iptal edildi.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Hata: {str(e)}[/red]")
        import traceback
        traceback.print_exc()

