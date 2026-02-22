#!/usr/bin/env python3
"""
Re-scoring tool for completed tests.
Use this when test completed but scoring failed.
"""

import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

# Ensure project root is in sys.path (so 'from src...' works from any directory)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.judge import Judge
from src.reporter import Reporter
from src.evaluator import TestResult
from src.utils import load_config, setup_logger
from rich.console import Console
from rich.panel import Panel

console = Console()


def load_intermediate_results(file_path: Path) -> tuple[List[TestResult], str, dict]:
    """
    Load test results from JSON file.
    Supports both intermediate (flat list) and final result (dict with 'results' key) formats.
    
    Returns:
        Tuple of (results, test_type, source_metadata)
        source_metadata contains 'provider' and 'model' from the original file if available.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine test type from filename
        if '_mcq_' in file_path.name:
            test_type = 'mcq'
        elif '_saq_' in file_path.name:
            test_type = 'saq'
        else:
            test_type = 'mcq'  # default
        
        # Extract source metadata
        source_metadata = {'provider': 'unknown', 'model': 'unknown'}
        
        # Handle both formats:
        # 1. Final result format: {"metadata": {...}, "statistics": {...}, "results": [...]}
        # 2. Intermediate format: [{...}, {...}, ...]
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
            metadata = data.get('metadata', {})
            # Override test_type from metadata if available
            test_type = metadata.get('test_type', test_type)
            # Extract original provider and model
            source_metadata['provider'] = metadata.get('provider', 'unknown')
            source_metadata['model'] = metadata.get('model_name') or metadata.get('model', 'unknown')
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError(f"Beklenmeyen dosya formatı: {type(data)}")
        
        # Convert to TestResult objects
        results = []
        for item in items:
            if isinstance(item, str):
                continue  # Skip non-dict entries
            result = TestResult(
                question_id=item.get('question_id', 0),
                category=item.get('category', ''),
                question=item.get('question', ''),
                expected_answer=item.get('expected_answer', ''),
                model_answer=item.get('model_answer', ''),
                score=item.get('score'),
                judge_reasoning=item.get('judge_reasoning'),
                error=item.get('error'),
                response_time=item.get('response_time')
            )
            results.append(result)
        
        return results, test_type, source_metadata
        
    except Exception as e:
        console.print(f"[red]Dosya okuma hatası: {str(e)}[/red]")
        raise


def find_latest_intermediate(test_type: Optional[str] = None) -> Optional[Path]:
    """Find latest intermediate result file."""
    intermediate_dir = Path('results/intermediate')
    
    if not intermediate_dir.exists():
        return None
    
    # Find files
    if test_type:
        pattern = f"{test_type}_intermediate.json"
        files = list(intermediate_dir.glob(pattern))
    else:
        files = list(intermediate_dir.glob('*_intermediate.json'))
    
    if not files:
        return None
    
    # Return latest
    return max(files, key=lambda x: x.stat().st_mtime)


def rescore_results(file_path: Path, config: dict, model_name: str = None):
    """
    Re-score test results.
    
    Args:
        file_path: Path to intermediate results file
        config: Configuration dictionary
        model_name: Optional model name override
    """
    console.print(Panel.fit(
        "[bold cyan]PUANLAMA ARACI[/bold cyan]\n\n"
        "Tamamlanmış test sonuçlarını yeniden puanlar",
        border_style="cyan"
    ))
    
    console.print(f"\n[yellow]Dosya yükleniyor:[/yellow] {file_path.name}\n")
    
    # Load results
    results, test_type, source_metadata = load_intermediate_results(file_path)
    
    console.print(f"[green]✓[/green] {len(results)} sonuç yüklendi")
    console.print(f"[green]✓[/green] Test tipi: {test_type.upper()}")
    console.print(f"[green]✓[/green] Orijinal provider: {source_metadata['provider']}")
    console.print(f"[green]✓[/green] Orijinal model: {source_metadata['model']}\n")
    
    # Use original model name if not overridden by --model arg
    if not model_name:
        model_name = source_metadata['model']
    
    provider = source_metadata['provider']
    
    # Check if already scored
    already_scored = sum(1 for r in results if r.score is not None)
    if already_scored == len(results):
        console.print(f"[yellow]⚠️  Tüm sorular zaten puanlanmış ({already_scored}/{len(results)})[/yellow]")
        console.print(f"[yellow]    Yeniden puanlamak istiyorsanız devam edin.[/yellow]\n")
    else:
        console.print(f"[cyan]Puanlanmamış sorular: {len(results) - already_scored}/{len(results)}[/cyan]\n")
    
    # Setup logger
    logger = setup_logger()
    
    # Score results
    judge_provider = config.get('judge', {}).get('provider', '') or 'openai'
    judge_model = config.get('judge', {}).get('model', '') or 'gpt-4o'
    console.print(f"[bold yellow]Puanlama başlatılıyor ({judge_provider}/{judge_model} ile)...[/bold yellow]\n")
    
    judge = Judge(config, logger)
    scored_results = judge.score_results(results, test_type)
    judge.cleanup()
    
    console.print(f"\n[bold green]✓[/bold green] Puanlama tamamlandı!\n")
    
    # Generate report
    console.print(f"[yellow]Rapor oluşturuluyor...[/yellow]\n")
    
    reporter = Reporter(config)
    report = reporter.generate_report(scored_results, test_type, model_name, provider=provider)
    
    # Show report paths
    if report['report_paths']:
        console.print(f"\n[bold green]Raporlar kaydedildi:[/bold green]")
        for report_type, path in report['report_paths'].items():
            console.print(f"  • {report_type}: {path}")
    
    console.print(f"\n[bold green]{'='*80}[/bold green]")
    console.print(f"[bold green]PUANLAMA BAŞARIYLA TAMAMLANDI![/bold green]")
    console.print(f"[bold green]{'='*80}[/bold green]\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tamamlanmış testleri yeniden puanla",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Kullanım Senaryoları:

1. Puanlama sırasında hata aldınız:
   python3 rescore.py

2. Belirli bir dosyayı yeniden puanla:
   python3 rescore.py results/intermediate/mcq_intermediate.json

3. MCQ sonuçlarını puanla:
   python3 rescore.py --type mcq

4. SAQ sonuçlarını puanla:
   python3 rescore.py --type saq

5. Model adını belirt:
   python3 rescore.py --type mcq --model gpt-4

Örnekler:
  # En son MCQ intermediate dosyasını puanla
  python3 rescore.py --type mcq
  
  # En son SAQ intermediate dosyasını puanla
  python3 rescore.py --type saq
  
  # Belirli dosyayı puanla
  python3 rescore.py results/intermediate/mcq_intermediate.json --model gpt-3.5-turbo
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='Puanlanacak intermediate JSON dosyası (belirtilmezse otomatik bulunur)'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        choices=['mcq', 'saq'],
        help='Test tipi (dosya belirtilmezse bu zorunlu)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Model adı (rapor için, opsiyonel)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Konfigürasyon dosyası (varsayılan: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Determine file to process
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            console.print(f"[red]Hata: Dosya bulunamadı: {file_path}[/red]")
            return
    else:
        # Find latest intermediate file
        if not args.type:
            console.print("[red]Hata: --type belirtilmeli (mcq veya saq)[/red]")
            console.print("Veya dosya yolunu direkt belirtin:")
            console.print("  python3 rescore.py results/intermediate/mcq_intermediate.json")
            return
        
        file_path = find_latest_intermediate(args.type)
        
        if not file_path:
            console.print(f"[red]Hata: {args.type.upper()} intermediate dosyası bulunamadı![/red]")
            console.print(f"Aranılan: results/intermediate/{args.type}_intermediate.json")
            return
        
        console.print(f"[cyan]Otomatik bulundu:[/cyan] {file_path.name}\n")
    
    # Re-score
    rescore_results(file_path, config, args.model)


if __name__ == '__main__':
    main()

