"""Report generation for benchmark results."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

from src.evaluator import TestResult
from tools.model_registry import ModelRegistry


class Reporter:
    """Generate detailed benchmark reports."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize reporter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results_dir = Path(config['paths']['results_dir'])
        self.save_json = config['output']['save_json']
        self.save_markdown = config['output']['save_markdown']
        self.detailed_errors = config['output']['detailed_errors']
    
    def get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        elif score >= 50:
            return 'E'
        else:
            return 'F'
    
    def calculate_statistics(self, results: List[TestResult], test_type: str) -> Dict[str, Any]:
        """
        Calculate statistics from results.
        
        Args:
            results: List of test results
            test_type: 'mcq' or 'saq'
            
        Returns:
            Statistics dictionary
        """
        total = len(results)
        scores = [r.score for r in results if r.score is not None]
        
        if not scores:
            return {
                'total_questions': total,
                'overall_score': 0.0,
                'category_scores': {},
                'grade': 'F'
            }
        
        # Overall statistics
        if test_type == 'mcq':
            correct = sum(1 for s in scores if s == 100.0)
            overall_score = (correct / total * 100) if total > 0 else 0.0
            stats = {
                'total_questions': total,
                'correct_answers': correct,
                'accuracy': overall_score,
                'overall_score': overall_score,
                'grade': self.get_grade(overall_score)
            }
        else:
            overall_score = sum(scores) / len(scores) if scores else 0.0
            stats = {
                'total_questions': total,
                'average_score': overall_score,
                'overall_score': overall_score,
                'min_score': min(scores) if scores else 0.0,
                'max_score': max(scores) if scores else 0.0,
                'grade': self.get_grade(overall_score)
            }
        
        # Category-wise statistics
        category_scores = defaultdict(list)
        for result in results:
            if result.score is not None and result.category:
                category_scores[result.category].append(result.score)
        
        category_stats = {}
        for category, cat_scores in category_scores.items():
            if not cat_scores:
                continue
            
            if test_type == 'mcq':
                correct = sum(1 for s in cat_scores if s == 100.0)
                accuracy = (correct / len(cat_scores) * 100) if cat_scores else 0.0
                category_stats[category] = {
                    'total': len(cat_scores),
                    'correct': correct,
                    'accuracy': accuracy
                }
            else:
                category_stats[category] = {
                    'total': len(cat_scores),
                    'average_score': sum(cat_scores) / len(cat_scores),
                    'min_score': min(cat_scores),
                    'max_score': max(cat_scores)
                }
        
        stats['category_scores'] = category_stats
        
        # Response time statistics
        response_times = [r.response_time for r in results if r.response_time is not None]
        if response_times:
            stats['response_time'] = {
                'average': sum(response_times) / len(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'total': sum(response_times)
            }
        
        # Category analysis - identify strengths and weaknesses
        if category_stats:
            if test_type == 'mcq':
                sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)
            else:
                sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['average_score'], reverse=True)
            
            # Top 5 and bottom 5 categories
            top_categories = sorted_cats[:5] if len(sorted_cats) >= 5 else sorted_cats
            weak_categories = sorted_cats[-5:] if len(sorted_cats) >= 5 else []
            
            # Critical categories (score < 30 for SAQ, < 50% for MCQ)
            critical_threshold = 50.0 if test_type == 'mcq' else 30.0
            critical_categories = []
            
            for cat, cat_stats in category_stats.items():
                score = cat_stats.get('accuracy' if test_type == 'mcq' else 'average_score', 0)
                if score < critical_threshold:
                    critical_categories.append({
                        'category': cat,
                        'score': score,
                        'count': cat_stats.get('total', 0)
                    })
            
            stats['analysis'] = {
                'top_categories': [(cat, cs) for cat, cs in top_categories],
                'weak_categories': [(cat, cs) for cat, cs in weak_categories],
                'critical_categories': critical_categories
            }
        
        return stats
    
    def generate_markdown_report(self, stats: Dict[str, Any], test_type: str, model_name: str) -> str:
        """
        Generate markdown report.
        
        Args:
            stats: Statistics dictionary
            test_type: 'mcq' or 'saq'
            model_name: Name of tested model
            
        Returns:
            Markdown formatted report
        """
        lines = []
        lines.append("# TÜRKÇE BENCHMARK SONUÇLARI\n")
        lines.append(f"**Model:** {model_name}\n")
        lines.append(f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Test Tipi:** {test_type.upper()}\n")
        lines.append("\n---\n")
        
        # Overall performance
        lines.append(f"## {test_type.upper()} PERFORMANSI\n")
        
        # Add grade
        grade = stats.get('grade', 'N/A')
        grade_emoji = {
            'A': '🟢 Mükemmel',
            'B': '🟢 Çok İyi', 
            'C': '🟡 İyi',
            'D': '🟡 Orta',
            'E': '🟠 Zayıf',
            'F': '🔴 Başarısız'
        }
        lines.append(f"**Genel Not:** {grade} ({grade_emoji.get(grade, '')})\n\n")
        
        if test_type == 'mcq':
            lines.append(f"**Toplam Soru:** {stats['total_questions']}\n")
            lines.append(f"**Doğru Cevap:** {stats['correct_answers']}\n")
            lines.append(f"**Doğruluk Oranı:** {stats['accuracy']:.2f}%\n")
        else:
            lines.append(f"**Toplam Soru:** {stats['total_questions']}\n")
            lines.append(f"**Ortalama Puan:** {stats['average_score']:.2f}/100\n")
            lines.append(f"**En Düşük Puan:** {stats['min_score']:.2f}\n")
            lines.append(f"**En Yüksek Puan:** {stats['max_score']:.2f}\n")
        
        # Response time
        if 'response_time' in stats:
            rt = stats['response_time']
            lines.append(f"\n**Yanıt Süreleri:**\n")
            lines.append(f"- Ortalama: {rt['average']:.2f}s\n")
            lines.append(f"- Toplam: {rt['total']:.2f}s\n")
        
        # Critical warnings
        analysis = stats.get('analysis', {})
        critical_cats = analysis.get('critical_categories', [])
        
        if critical_cats:
            lines.append("\n## ⚠️ KRİTİK UYARILAR\n")
            lines.append("\nAşağıdaki kategorilerde kritik düşük performans tespit edildi:\n\n")
            for crit in critical_cats:
                score = crit['score']
                category = crit['category']
                count = crit['count']
                lines.append(f"- 🚨 **{category}**: {score:.2f} puan ({count} soru)\n")
            lines.append("\n⚠️ **Bu kategorilerde model güvenilir değildir. Üretim kullanımı için dikkat!**\n")
        
        # Performance summary
        if analysis:
            lines.append("\n## 📊 PERFORMANS ÖZETİ\n")
            
            top_cats = analysis.get('top_categories', [])
            if top_cats:
                lines.append("\n### ✅ En Güçlü Kategoriler (Top 5)\n\n")
                for i, (cat, cat_stats) in enumerate(top_cats, 1):
                    if test_type == 'mcq':
                        score = cat_stats.get('accuracy', 0)
                    else:
                        score = cat_stats.get('average_score', 0)
                    
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                    lines.append(f"{emoji} **{cat}**: {score:.2f}{'%' if test_type == 'mcq' else '/100'}\n")
            
            weak_cats = analysis.get('weak_categories', [])
            if weak_cats:
                lines.append("\n### ⚠️ Geliştirilmesi Gereken Kategoriler (Bottom 5)\n\n")
                for cat, cat_stats in weak_cats:
                    if test_type == 'mcq':
                        score = cat_stats.get('accuracy', 0)
                    else:
                        score = cat_stats.get('average_score', 0)
                    lines.append(f"- **{cat}**: {score:.2f}{'%' if test_type == 'mcq' else '/100'}\n")
        
        # Category performance
        lines.append("\n## KATEGORİ BAZLI SONUÇLAR\n")
        
        category_scores = stats.get('category_scores', {})
        
        # Sort categories by score (descending) then by name
        if test_type == 'mcq':
            sorted_categories = sorted(
                category_scores.items(),
                key=lambda x: (x[1]['accuracy'], x[0]),
                reverse=True
            )
        else:
            sorted_categories = sorted(
                category_scores.items(),
                key=lambda x: (x[1]['average_score'], x[0]),
                reverse=True
            )
        
        for category, cat_stats in sorted_categories:
            if not category:
                category = "Kategori Belirtilmemiş"
            
            lines.append(f"\n### {category}\n")
            
            if test_type == 'mcq':
                lines.append(f"- Toplam: {cat_stats['total']} soru\n")
                lines.append(f"- Doğru: {cat_stats['correct']} soru\n")
                lines.append(f"- Doğruluk: **{cat_stats['accuracy']:.2f}%**\n")
            else:
                lines.append(f"- Toplam: {cat_stats['total']} soru\n")
                lines.append(f"- Ortalama Puan: **{cat_stats['average_score']:.2f}/100**\n")
                lines.append(f"- En Düşük: {cat_stats['min_score']:.2f}\n")
                lines.append(f"- En Yüksek: {cat_stats['max_score']:.2f}\n")
        
        return ''.join(lines)
    
    def generate_report(
        self,
        results: List[TestResult],
        test_type: str,
        model_name: str,
        provider: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate complete report.
        
        Args:
            results: List of test results
            test_type: 'mcq' or 'saq'
            model_name: Name of tested model
            provider: Provider name (openai, anthropic, etc.)
            
        Returns:
            Report dictionary with paths to saved files
        """
        # Calculate statistics
        stats = self.calculate_statistics(results, test_type)
        
        # Prepare output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"{model_name.replace('/', '_')}_{test_type}_{timestamp}"
        
        report_paths = {}
        
        # Save JSON
        if self.save_json:
            json_path = self.results_dir / f"{base_name}.json"
            
            report_data = {
                'metadata': {
                    'model_name': model_name,
                    'provider': provider,
                    'test_type': test_type,
                    'timestamp': datetime.now().isoformat(),
                    'total_questions': len(results),
                    'judge_provider': self.config.get('judge', {}).get('provider', 'unknown'),
                    'judge_model': self.config.get('judge', {}).get('model', 'unknown'),
                    'overall_score': stats.get('overall_score', 0),
                    'grade': stats.get('grade', 'N/A'),
                    'benchmark_version': '1.0.0'
                },
                'statistics': stats,
                'results': [
                    {
                        'question_id': r.question_id,
                        'category': r.category,
                        'question': r.question,
                        'expected_answer': r.expected_answer,
                        'model_answer': r.model_answer,
                        'score': r.score,
                        'judge_reasoning': r.judge_reasoning if self.detailed_errors else None,
                        'error': r.error if self.detailed_errors else None,
                        'response_time': r.response_time
                    }
                    for r in results
                ]
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            report_paths['json'] = str(json_path)
        
        # Save Markdown
        if self.save_markdown:
            md_path = self.results_dir / f"{base_name}.md"
            md_content = self.generate_markdown_report(stats, test_type, model_name)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            report_paths['markdown'] = str(md_path)
        
        # Print summary to console
        print("\n" + "="*80)
        md_report = self.generate_markdown_report(stats, test_type, model_name)
        print(md_report)
        print("="*80)
        
        # Print critical warnings to console if any
        critical_cats = stats.get('analysis', {}).get('critical_categories', [])
        if critical_cats:
            print("\n" + "🚨" * 40)
            print("⚠️  KRİTİK UYARI: Düşük Performanslı Kategoriler Tespit Edildi!")
            print("🚨" * 40)
            for crit in critical_cats:
                print(f"  • {crit['category']}: {crit['score']:.2f} puan")
            print("\n⚠️  Bu kategorilerde model güvenilir değildir!")
            print("🚨" * 40 + "\n")
        
        # Register model result
        try:
            registry = ModelRegistry()
            registry.register_result(
                provider=provider,
                model_name=model_name,
                test_type=test_type,
                score=stats.get('overall_score', 0),
                grade=stats.get('grade', 'N/A'),
                total_questions=len(results),
                report_path=str(report_paths.get('json', ''))
            )
        except Exception as e:
            # Don't fail the report if registry fails
            print(f"[Uyarı] Model kaydı başarısız: {str(e)}")
        
        return {
            'statistics': stats,
            'report_paths': report_paths
        }
