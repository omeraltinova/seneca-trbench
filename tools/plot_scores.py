#!/usr/bin/env python3
"""
Benchmark score visualization tool.

Generates:
1. Combined score chart (all selected models together)
2. Per-model score charts (single model, potentially across multiple runs)

Selection modes:
- judge: same judge provider + judge model
- tool: MCQ runs completed with auto tool-call scoring
"""

import argparse
import json
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure matplotlib can build font/cache files in restricted environments.
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'matplotlib-cache'))

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_IMPORT_ERROR = None
except ImportError as e:
    MATPLOTLIB_IMPORT_ERROR = e
    plt = None


@dataclass
class RunRecord:
    """Structured result row used by chart generation."""
    file_path: Path
    provider: str
    model_name: str
    model_key: str
    test_type: str
    timestamp: datetime
    timestamp_raw: str
    score: float
    judge_model: str
    judge_provider: str
    judge_key: str
    judge_provider_inferred: bool
    auto_tool_call: bool


def safe_parse_datetime(value: str) -> datetime:
    """Parse ISO-like timestamp safely."""
    if not value:
        return datetime.min

    normalized = value.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min


def sanitize_filename(value: str) -> str:
    """Create filesystem-safe filename part."""
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]+', '_', value.strip())
    return sanitized.strip('._') or 'unknown'


def get_judge_provider(metadata: Dict[str, Any]) -> Tuple[str, bool]:
    """Resolve judge provider from metadata and return inference flag."""
    judge_provider = (metadata.get('judge_provider') or '').strip()
    if judge_provider:
        return judge_provider, False

    judge_model = (metadata.get('judge_model') or '').strip()
    if '/' in judge_model:
        return judge_model.split('/', 1)[0], True

    return 'unknown', True


def infer_auto_tool_call(metadata: Dict[str, Any], results: List[Dict[str, Any]]) -> bool:
    """
    Infer whether this run used MCQ tool-call auto scoring.

    Priority:
    1) Explicit metadata flag if available
    2) judge_reasoning pattern check for MCQ results
    """
    explicit_mode = (
        metadata.get('mcq_type')
        or metadata.get('mcq_scoring_mode')
        or metadata.get('scoring_mode')
        or metadata.get('evaluation_mode')
    )
    if isinstance(explicit_mode, str) and explicit_mode.lower() == 'tool':
        return True

    if metadata.get('test_type') != 'mcq':
        return False

    if not results:
        return False

    auto_count = 0
    total_count = 0
    for row in results:
        reasoning = row.get('judge_reasoning')
        if reasoning is None:
            continue
        total_count += 1
        if str(reasoning).startswith('Otomatik doğrulama'):
            auto_count += 1

    if total_count == 0:
        return False

    return (auto_count / total_count) >= 0.9


def extract_score(test_type: str, stats: Dict[str, Any]) -> Optional[float]:
    """Extract comparable score from result stats."""
    if test_type == 'mcq':
        value = stats.get('accuracy', stats.get('overall_score'))
    elif test_type == 'saq':
        value = stats.get('average_score', stats.get('overall_score'))
    else:
        value = stats.get('overall_score')

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_records(results_dir: Path, test_type_filter: str) -> List[RunRecord]:
    """Load valid result records from JSON files."""
    records: List[RunRecord] = []

    for file_path in sorted(results_dir.glob('*.json')):
        file_name = file_path.name
        if 'model_registry' in file_name or 'comparison_report' in file_name:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Atlandı (okunamadı): {file_path.name} - {str(e)}")
            continue

        metadata = data.get('metadata', {})
        stats = data.get('statistics', {})
        results = data.get('results', [])

        if not metadata or not stats:
            continue

        test_type = metadata.get('test_type', 'unknown')
        if test_type_filter != 'all' and test_type != test_type_filter:
            continue

        score = extract_score(test_type, stats)
        if score is None:
            continue

        provider = metadata.get('provider', 'unknown')
        model_name = metadata.get('model_name') or metadata.get('model', 'unknown')
        model_key = f"{provider}/{model_name}"
        judge_model = metadata.get('judge_model', 'unknown')
        judge_provider, provider_inferred = get_judge_provider(metadata)
        judge_key = f"{judge_provider}::{judge_model}"
        timestamp_raw = metadata.get('timestamp', '')
        timestamp = safe_parse_datetime(timestamp_raw)
        auto_tool_call = infer_auto_tool_call(metadata, results)

        records.append(
            RunRecord(
                file_path=file_path,
                provider=provider,
                model_name=model_name,
                model_key=model_key,
                test_type=test_type,
                timestamp=timestamp,
                timestamp_raw=timestamp_raw,
                score=score,
                judge_model=judge_model,
                judge_provider=judge_provider,
                judge_key=judge_key,
                judge_provider_inferred=provider_inferred,
                auto_tool_call=auto_tool_call,
            )
        )

    return records


def select_latest_run_per_model(records: List[RunRecord]) -> List[RunRecord]:
    """Keep only latest run for each model key."""
    latest_by_model: Dict[str, RunRecord] = {}
    for record in records:
        current = latest_by_model.get(record.model_key)
        if current is None or record.timestamp > current.timestamp:
            latest_by_model[record.model_key] = record

    return sorted(latest_by_model.values(), key=lambda r: r.score, reverse=True)


def score_axis_label(test_type: str) -> str:
    """Label for score axis."""
    if test_type == 'saq':
        return 'Puan (0-100)'
    return 'Doğruluk / Puan (0-100)'


def score_color(score: float) -> str:
    """Traffic-light color by score."""
    if score >= 80:
        return '#1976D2'
    if score >= 60:
        return '#F9A825'
    return '#B71C1C'


def format_timestamp(value: datetime, fallback: str) -> str:
    """Readable timestamp for plot labels."""
    if value == datetime.min:
        return fallback[:19] if isinstance(fallback, str) else 'unknown'
    return value.strftime('%Y-%m-%d %H:%M')


def plot_combined_chart(records: List[RunRecord], title: str, output_path: Path) -> None:
    """Create combined horizontal bar chart."""
    if not records:
        return

    labels = [r.model_key for r in records]
    scores = [r.score for r in records]
    colors = [score_color(s) for s in scores]

    fig_height = max(5.0, 0.55 * len(labels) + 1.5)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    bars = ax.barh(labels, scores, color=colors)

    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel(score_axis_label(records[0].test_type))
    ax.set_title(title)
    ax.grid(axis='x', linestyle='--', alpha=0.3)

    for bar, score in zip(bars, scores):
        y_pos = bar.get_y() + bar.get_height() / 2
        ax.text(min(score + 1.0, 99.0), y_pos, f'{score:.2f}', va='center', fontsize=9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_single_model_chart(
    records: List[RunRecord],
    title_prefix: str,
    output_path: Path,
) -> None:
    """Create per-model chart (line if multiple runs, single bar otherwise)."""
    if not records:
        return

    sorted_records = sorted(records, key=lambda r: r.timestamp)
    scores = [r.score for r in sorted_records]
    tick_labels = [format_timestamp(r.timestamp, r.timestamp_raw) for r in sorted_records]

    fig_width = 10 if len(sorted_records) > 1 else 8
    fig, ax = plt.subplots(figsize=(fig_width, 5))

    if len(sorted_records) == 1:
        bar = ax.bar(['Son Koşu'], [scores[0]], color=[score_color(scores[0])])
        ax.text(0, scores[0] + 1.0, f'{scores[0]:.2f}', ha='center', fontsize=10)
        bar[0].set_edgecolor('#333333')
    else:
        x_values = list(range(len(sorted_records)))
        ax.plot(x_values, scores, marker='o', linewidth=2, color='#1565C0')
        for idx, score in enumerate(scores):
            ax.text(idx, score + 1.0, f'{score:.2f}', ha='center', fontsize=9)
        ax.set_xticks(x_values)
        ax.set_xticklabels(tick_labels, rotation=30, ha='right')

    ax.set_ylim(0, 100)
    ax.set_ylabel(score_axis_label(sorted_records[0].test_type))
    ax.set_title(f"{title_prefix} - {sorted_records[0].model_key}")
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def print_selection_table(records: List[RunRecord], title: str) -> None:
    """Print selected records summary."""
    print('\n' + title)
    print('-' * len(title))
    print(f"{'Model':<50} {'Test':<5} {'Skor':>8} {'Judge Provider':<14} {'Judge Model':<24} {'Tool':<5} {'Tarih'}")
    print('-' * 110)

    for row in sorted(records, key=lambda r: r.timestamp, reverse=True):
        tool_flag = 'Evet' if row.auto_tool_call else 'Hayır'
        date_str = format_timestamp(row.timestamp, row.timestamp_raw)
        print(
            f"{row.model_key[:50]:<50} "
            f"{row.test_type.upper():<5} "
            f"{row.score:>8.2f} "
            f"{row.judge_provider[:14]:<14} "
            f"{row.judge_model[:24]:<24} "
            f"{tool_flag:<5} "
            f"{date_str}"
        )


def generate_charts_for_group(
    records: List[RunRecord],
    output_dir: Path,
    group_key: str,
    title_prefix: str,
) -> Tuple[Optional[Path], List[Path]]:
    """Generate combined + per-model charts for a selected group."""
    if not records:
        return None, []

    latest_records = select_latest_run_per_model(records)
    test_type = latest_records[0].test_type if latest_records else 'all'
    safe_key = sanitize_filename(group_key)

    combined_path = output_dir / f'combined_{safe_key}_{test_type}.png'
    plot_combined_chart(
        latest_records,
        title=f"{title_prefix} - Toplu Model Skorları ({test_type.upper()})",
        output_path=combined_path,
    )

    single_dir = output_dir / f'single_{safe_key}_{test_type}'
    single_paths: List[Path] = []

    by_model: Dict[str, List[RunRecord]] = defaultdict(list)
    for record in records:
        by_model[record.model_key].append(record)

    for model_key, model_records in sorted(by_model.items()):
        model_safe = sanitize_filename(model_key)
        file_path = single_dir / f'{model_safe}.png'
        plot_single_model_chart(
            records=model_records,
            title_prefix=title_prefix,
            output_path=file_path,
        )
        single_paths.append(file_path)

    return combined_path, single_paths


def run_judge_mode(
    records: List[RunRecord],
    output_dir: Path,
    judge_provider: Optional[str],
    judge_model: Optional[str],
) -> None:
    """Generate charts for same judge provider+model runs."""
    selected = records
    if judge_provider:
        selected = [r for r in selected if r.judge_provider == judge_provider]
    if judge_model:
        selected = [r for r in selected if r.judge_model == judge_model]

    if not selected:
        filter_desc = f"provider={judge_provider or '*'}, model={judge_model or '*'}"
        print(f'Belirtilen judge filtresi için kayıt bulunamadı: {filter_desc}')
        return

    grouped: Dict[str, List[RunRecord]] = defaultdict(list)
    for record in selected:
        grouped[record.judge_key].append(record)

    if not grouped:
        print('Judge provider+model bazında uygun kayıt bulunamadı.')
        return

    for group_key, group in sorted(grouped.items()):
        provider = group[0].judge_provider
        model = group[0].judge_model
        title = f"Seçilen Sonuçlar (Judge: {provider} + {model})"
        print_selection_table(group, title)
        combined_path, single_paths = generate_charts_for_group(
            group,
            output_dir,
            group_key=f'judge_{provider}_{model}',
            title_prefix=f"Judge: {provider} + {model}",
        )
        print(f"\nToplu grafik: {combined_path}")
        print(f"Tekil grafik sayısı: {len(single_paths)}\n")


def run_tool_mode(records: List[RunRecord], output_dir: Path) -> None:
    """Generate charts for auto tool-call completed runs."""
    selected = [r for r in records if r.auto_tool_call]
    if not selected:
        print('Auto tool-call ile tamamlanmış uygun sonuç bulunamadı.')
        return

    print_selection_table(selected, "Seçilen Sonuçlar (MCQ Auto Tool-Call)")
    combined_path, single_paths = generate_charts_for_group(
        selected,
        output_dir,
        group_key='auto_tool_call',
        title_prefix='MCQ Auto Tool-Call',
    )
    print(f"\nToplu grafik: {combined_path}")
    print(f"Tekil grafik sayısı: {len(single_paths)}")


def main() -> None:
    """Main entry point."""
    if MATPLOTLIB_IMPORT_ERROR is not None:
        print('Hata: matplotlib kurulu değil.')
        print('Kurulum için: pip install -r requirements.txt')
        return

    parser = argparse.ArgumentParser(
        description='Benchmark sonuçları için puan grafikleri üret',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Judge provider + model bazlı tüm gruplar için grafik üret
  python3 tools/plot_scores.py --mode judge

  # Sadece belirli judge provider + model için çiz
  python3 tools/plot_scores.py --mode judge --judge-provider openrouter --judge-model openai/gpt-5-mini

  # Auto tool-call ile tamamlanan MCQ sonuçlarını çiz
  python3 tools/plot_scores.py --mode tool --test-type mcq
        """,
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['judge', 'tool'],
        required=True,
        help='Seçim modu: judge veya tool',
    )
    parser.add_argument(
        '--judge-provider',
        type=str,
        default=None,
        help='(mode=judge) filtrelenecek judge provider adı',
    )
    parser.add_argument(
        '--judge-model',
        type=str,
        default=None,
        help='(mode=judge) filtrelenecek judge model adı (ör: openai/gpt-5-mini)',
    )
    parser.add_argument(
        '--test-type',
        type=str,
        choices=['mcq', 'saq', 'all'],
        default='mcq',
        help='Hangi test tipindeki sonuçlar yüklensin (varsayılan: mcq)',
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='results',
        help='Sonuç JSON dosyalarının klasörü',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/plots',
        help='Grafiklerin kaydedileceği klasör',
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f'Hata: Sonuç klasörü bulunamadı: {results_dir}')
        return

    all_records = load_records(results_dir, args.test_type)
    if not all_records:
        print('Grafik üretimi için uygun sonuç dosyası bulunamadı.')
        return

    output_dir = Path(args.output_dir)
    print(f'Toplam uygun kayıt: {len(all_records)}')
    print(f'Çıktı klasörü: {output_dir}\n')

    if args.mode == 'judge':
        inferred_count = sum(1 for r in all_records if r.judge_provider_inferred)
        if inferred_count > 0:
            print(
                f'Uyarı: {inferred_count} kayıtta judge_provider metadata içinde yok; '
                'judge_model üzerinden türetildi.'
            )
        run_judge_mode(all_records, output_dir, args.judge_provider, args.judge_model)
    else:
        if args.test_type == 'saq':
            print('Uyarı: tool modu yalnızca MCQ için anlamlıdır; SAQ sonuçlarında kayıt bulunmayabilir.')
        run_tool_mode(all_records, output_dir)


if __name__ == '__main__':
    main()
