#!/usr/bin/env python3
"""
Turkish Language Benchmark System
Main entry point for running benchmarks on language models.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.models import create_model, PROVIDER_MAP
from src.evaluator import Evaluator
from src.judge import Judge
from src.reporter import Reporter
from src.utils import load_config, setup_logger


console = Console()

# All supported provider names (for CLI choices)
SUPPORTED_PROVIDERS = sorted(PROVIDER_MAP.keys())


def run_benchmark(
    provider: str,
    model_name: str,
    test_type: str,
    config_path: str,
    resume: bool = False,
    judge_provider: Optional[str] = None,
    judge_model: Optional[str] = None,
):
    """
    Run benchmark on specified model.
    
    Args:
        provider: Model provider
        model_name: Model identifier
        test_type: 'mcq', 'saq', or 'all'
        config_path: Path to config file
        resume: Resume from interrupted test
        judge_provider: Override judge provider from config
        judge_model: Override judge model from config
    """
    # Load configuration
    console.print("[bold blue]Konfigürasyon yükleniyor...[/bold blue]")
    config = load_config(config_path)
    
    # Override judge settings from CLI if provided
    if judge_provider:
        config['judge']['provider'] = judge_provider
    if judge_model:
        config['judge']['model'] = judge_model
    
    # Setup logger
    logger = setup_logger(log_dir=config['paths']['logs_dir'])
    logger.info(f"Benchmark başlatılıyor: {provider}/{model_name}")
    
    # Display banner
    judge_info = f"{config['judge'].get('provider', 'openai')}/{config['judge']['model']}"
    console.print(Panel.fit(
        f"[bold green]TÜRKÇE DİL BENCHMARK SİSTEMİ[/bold green]\n\n"
        f"Provider: {provider}\n"
        f"Model: {model_name}\n"
        f"Test Tipi: {test_type}\n"
        f"Judge: {judge_info}",
        border_style="green"
    ))
    
    try:
        # Create model
        console.print(f"\n[bold yellow]Model hazırlanıyor: {model_name}[/bold yellow]")
        model = create_model(provider, model_name, config)
        
        # Setup model (download if needed, start server, etc.)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Model kurulumu yapılıyor...", total=None)
            # Preflight: basic model validation with helpful error message
            try:
                model.setup()
            except Exception as e:
                console.print(f"[bold red]Model başlatılamadı:[/bold red] {str(e)}")
                logger.error(f"Model setup hatası: {str(e)}", exc_info=True)
                raise
            progress.update(task, completed=True)
        
        console.print("[bold green]✓[/bold green] Model hazır\n")
        
        # Determine which tests to run
        tests_to_run = []
        if test_type in ['mcq', 'all']:
            tests_to_run.append('mcq')
        if test_type in ['saq', 'all']:
            tests_to_run.append('saq')
        
        # Run tests
        all_reports = {}
        
        for current_test in tests_to_run:
            console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
            console.print(f"[bold cyan]{current_test.upper()} TESTİ BAŞLIYOR[/bold cyan]")
            console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
            
            # Create evaluator
            evaluator = Evaluator(config, model, logger)
            
            # Run test
            try:
                results = evaluator.run_test(current_test, resume_from=0 if not resume else None)
            except Exception as e:
                console.print(f"[bold red]{current_test.upper()} testi başlatılamadı:[/bold red] {str(e)}")
                logger.error(f"{current_test} testi hatası: {str(e)}", exc_info=True)
                raise
            
            console.print(f"\n[bold green]✓[/bold green] Test tamamlandı: {len(results)} soru\n")
            
            # Score results
            judge_display = f"{config['judge'].get('provider', 'openai')}/{config['judge']['model']}"
            console.print(f"[bold yellow]Puanlama yapılıyor ({judge_display} ile)...[/bold yellow]\n")
            judge = Judge(config, logger)
            scored_results = judge.score_results(results, current_test)
            judge.cleanup()
            
            console.print(f"[bold green]✓[/bold green] Puanlama tamamlandı\n")
            
            # Generate report
            console.print(f"[bold yellow]Rapor oluşturuluyor...[/bold yellow]\n")
            reporter = Reporter(config)
            report = reporter.generate_report(scored_results, current_test, model_name, provider)
            
            all_reports[current_test] = report
            
            # Show report paths
            if report['report_paths']:
                console.print(f"\n[bold green]Raporlar kaydedildi:[/bold green]")
                for report_type, path in report['report_paths'].items():
                    console.print(f"  • {report_type}: {path}")
        
        # Cleanup
        console.print(f"\n[bold yellow]Temizlik yapılıyor...[/bold yellow]")
        model.cleanup()
        
        # Final summary
        console.print(Panel.fit(
            "[bold green]BENCHMARK BAŞARIYLA TAMAMLANDI[/bold green]\n\n"
            f"Test Edilen Model: {model_name}\n"
            f"Judge Model: {judge_display}\n"
            f"Tamamlanan Testler: {', '.join(tests_to_run)}\n"
            f"Sonuçlar: {config['paths']['results_dir']}",
            border_style="green"
        ))
        
        logger.info("Benchmark başarıyla tamamlandı")
        
    except KeyboardInterrupt:
        console.print("\n[bold red]Benchmark kullanıcı tarafından durduruldu[/bold red]")
        logger.warning("Benchmark interrupted by user")
        if 'model' in locals():
            model.cleanup()
        sys.exit(1)
        
    except Exception as e:
        console.print(f"\n[bold red]Hata: {str(e)}[/bold red]")
        logger.error(f"Benchmark hatası: {str(e)}", exc_info=True)
        if 'model' in locals():
            model.cleanup()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Türkçe Dil Benchmark Sistemi - LLM modellerini Türkçe dil yetenekleri açısından test eder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # OpenAI GPT-4 ile tüm testleri çalıştır
  python benchmark.py --provider openai --model gpt-4 --test-type all
  
  # Ollama ile lokal model test et
  python benchmark.py --provider ollama --model llama3 --test-type mcq
  
  # LM Studio ile test et
  python benchmark.py --provider lmstudio --model loaded-model --test-type mcq
  
  # OpenRouter ile test et
  python benchmark.py --provider openrouter --model anthropic/claude-3.5-sonnet --test-type saq
  
  # Judge modelini değiştirerek test et
  python benchmark.py --provider openai --model gpt-4 --judge-provider ollama --judge-model llama3
  
  # Judge olarak OpenRouter kullan
  python benchmark.py --provider ollama --model llama3 --judge-provider openrouter --judge-model openai/gpt-4o
        """
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        required=True,
        choices=SUPPORTED_PROVIDERS,
        help='Test modeli sağlayıcı'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Test modeli adı/kimliği'
    )
    
    parser.add_argument(
        '--test-type',
        type=str,
        default='all',
        choices=['mcq', 'saq', 'all'],
        help='Test tipi (varsayılan: all)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Konfigürasyon dosyası yolu (varsayılan: config.yaml)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Kesilen testten devam et'
    )
    
    # Judge override arguments
    parser.add_argument(
        '--judge-provider',
        type=str,
        choices=SUPPORTED_PROVIDERS,
        default=None,
        help='Judge (puanlama) modeli sağlayıcı (config.yaml\'daki varsayılanı geçersiz kılar)'
    )
    
    parser.add_argument(
        '--judge-model',
        type=str,
        default=None,
        help='Judge (puanlama) modeli adı (config.yaml\'daki varsayılanı geçersiz kılar)'
    )
    
    args = parser.parse_args()
    
    # Run benchmark
    run_benchmark(
        provider=args.provider,
        model_name=args.model,
        test_type=args.test_type,
        config_path=args.config,
        resume=args.resume,
        judge_provider=args.judge_provider,
        judge_model=args.judge_model,
    )


if __name__ == '__main__':
    main()
