"""Automated judging system using GPT-4o."""

import re
from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models.api_models import OpenAIModel
from src.evaluator import TestResult
from src.utils.logger import setup_logger


class Judge:
    """Automated judge using GPT-4o for scoring."""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize judge.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or setup_logger()
        
        judge_config = config['judge']
        self.model = OpenAIModel(judge_config['model'], config)
        self.temperature = judge_config['temperature']
        self.max_tokens = judge_config.get('max_tokens', 300)
        self.parallel_workers = judge_config.get('parallel_workers', 10)
        
        # Setup model
        self.model.setup()
    
    def score_mcq(self, result: TestResult) -> Tuple[float, str]:
        """
        Score MCQ question (0 or 100).
        
        Args:
            result: Test result to score
            
        Returns:
            Tuple of (score, reasoning)
        """
        prompt = f"""Sen Türkçe dil testlerinde uzman bir değerlendiricisin. Aşağıdaki çoktan seçmeli soruya verilen cevabı değerlendir.

Soru:
{result.question}

Beklenen Cevap:
{result.expected_answer}

Model Cevabı:
{result.model_answer}

Görevin:
1. Model cevabını analiz et
2. Doğru şıkkı belirlemiş mi kontrol et
3. 0 (yanlış) veya 100 (doğru) puan ver

Cevabını şu formatta ver:
PUAN: [0 veya 100]
GEREKÇE: [Kısa açıklama]"""
        
        try:
            response = self.model.generate(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            score_match = re.search(r'PUAN:\s*(\d+)', response)
            reasoning_match = re.search(r'GEREKÇE:\s*(.+)', response, re.DOTALL)
            
            score = float(score_match.group(1)) if score_match else 0.0
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response
            
            return score, reasoning
            
        except Exception as e:
            self.logger.error(f"MCQ puanlama hatası: {str(e)}")
            return 0.0, f"Puanlama hatası: {str(e)}"
    
    def score_saq(self, result: TestResult) -> Tuple[float, str]:
        """
        Score SAQ question (0-100).
        
        Args:
            result: Test result to score
            
        Returns:
            Tuple of (score, reasoning)
        """
        prompt = f"""Türkçe test cevabını değerlendir.

Soru: {result.question}
Beklenen: {result.expected_answer}
Model: {result.model_answer}

Doğruluk (0-40) + İçerik (0-30) + Dil (0-30) = Toplam (0-100)

Format:
PUAN: [sayı]
GEREKÇE: [kısa açıklama]"""
        
        try:
            response = self.model.generate(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            score_match = re.search(r'PUAN:\s*(\d+(?:\.\d+)?)', response)
            reasoning_match = re.search(r'GEREKÇE:\s*(.+)', response, re.DOTALL)
            
            score = float(score_match.group(1)) if score_match else 0.0
            score = max(0.0, min(100.0, score))  # Clamp to 0-100
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response
            
            return score, reasoning
            
        except Exception as e:
            self.logger.error(f"SAQ puanlama hatası: {str(e)}")
            return 0.0, f"Puanlama hatası: {str(e)}"
    
    def _score_single(self, result: TestResult, test_type: str) -> TestResult:
        """Score a single result."""
        if result.error:
            result.score = 0.0
            result.judge_reasoning = f"Test hatası: {result.error}"
        else:
            score_func = self.score_mcq if test_type == 'mcq' else self.score_saq
            score, reasoning = score_func(result)
            result.score = score
            result.judge_reasoning = reasoning
        return result
    
    def score_results(self, results: List[TestResult], test_type: str, max_workers: int = None) -> List[TestResult]:
        """
        Score all test results with parallel processing.
        
        Args:
            results: List of test results
            test_type: 'mcq' or 'saq'
            max_workers: Number of parallel workers (None = use config value)
            
        Returns:
            List of scored results
        """
        if max_workers is None:
            max_workers = self.parallel_workers
        
        self.logger.info(f"{test_type.upper()} sonuçları puanlanıyor (paralel: {max_workers} worker)...")
        
        scored_results = [None] * len(results)
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._score_single, result, test_type): i
                for i, result in enumerate(results)
            }
            
            # Collect results with progress bar
            with tqdm(total=len(results), desc="Puanlama") as pbar:
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        scored_result = future.result()
                        scored_results[index] = scored_result
                    except Exception as e:
                        self.logger.error(f"Soru {index} puanlama hatası: {str(e)}")
                        results[index].score = 0.0
                        results[index].judge_reasoning = f"Puanlama hatası: {str(e)}"
                        scored_results[index] = results[index]
                    pbar.update(1)
        
        self.logger.info(f"Puanlama tamamlandı: {len(scored_results)} soru")
        return scored_results
    
    def cleanup(self):
        """Cleanup judge resources."""
        if self.model:
            self.model.cleanup()

