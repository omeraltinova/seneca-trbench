"""Automated judging system using configurable LLM provider."""

import re
from typing import Dict, List, Any, Tuple, Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models import create_model
from src.evaluator import TestResult
from src.utils.logger import setup_logger


class Judge:
    """Automated judge using a configurable LLM for scoring."""
    
    def __init__(self, config: Dict[str, Any], logger=None, mcq_type: str = 'ai'):
        """
        Initialize judge.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            mcq_type: MCQ scoring mode ('ai' for LLM judge, 'tool' for auto scoring)
        """
        self.config = config
        self.logger = logger or setup_logger()
        self.mcq_type = mcq_type
        
        judge_config = config['judge']
        self.temperature = judge_config['temperature']
        self.max_tokens = judge_config.get('max_tokens', 5000)
        self.parallel_workers = judge_config.get('parallel_workers', 10)
        
        # Judge model is only needed when AI scoring is required
        self.model = None
        self._needs_ai_judge = False
    
    def _ensure_ai_judge(self) -> None:
        """Lazily initialize the AI judge model when needed."""
        if self.model is not None:
            return
        
        judge_config = self.config['judge']
        judge_provider = judge_config.get('provider', '') or 'openai'
        judge_model_name = judge_config.get('model', '') or 'gpt-4o'
        
        self.logger.info(f"Judge modeli başlatılıyor: {judge_provider}/{judge_model_name}")
        self.model = create_model(judge_provider, judge_model_name, self.config)
        self.model.setup()
    
    @staticmethod
    def _extract_expected_letter(expected_answer: str) -> Optional[str]:
        """
        Extract expected answer letter from various answer formats.
        
        Handles: "Doğru cevap: A", "Doğru: A", "A) Heyecan", etc.
        
        Args:
            expected_answer: Raw expected answer string
            
        Returns:
            Single letter (A/B/C/D) or None if extraction fails
        """
        answer = expected_answer.strip()
        
        # Son karakter A-D ise direkt al (130/131 soru)
        if answer and answer[-1].upper() in 'ABCD':
            return answer[-1].upper()
        
        # Fallback: başında "A)" formatı varsa (1 outlier)
        match = re.match(r'([A-D])\)', answer)
        if match:
            return match.group(1)
        
        return None
    
    def score_mcq_auto(self, result: TestResult) -> Tuple[float, str]:
        """
        Score MCQ question automatically without LLM (0 or 100).
        
        Compares model's tool-call answer directly with expected answer letter.
        
        Args:
            result: Test result to score
            
        Returns:
            Tuple of (score, reasoning)
        """
        expected_letter = self._extract_expected_letter(result.expected_answer)
        
        if expected_letter is None:
            self.logger.warning(
                f"Soru {result.question_id}: Beklenen cevap harfi çıkarılamadı: '{result.expected_answer}'"
            )
            return 0.0, f"Otomatik doğrulama hatası: Beklenen cevap harfi çıkarılamadı ('{result.expected_answer}')"
        
        model_letter = result.model_answer.strip().upper()
        
        if model_letter == expected_letter:
            return 100.0, f"Otomatik doğrulama: Doğru ({expected_letter})"
        else:
            return 0.0, f"Otomatik doğrulama: Yanlış (Beklenen: {expected_letter}, Model: {model_letter})"
    
    def score_mcq(self, result: TestResult) -> Tuple[float, str]:
        """
        Score MCQ question (0 or 100).
        
        Args:
            result: Test result to score
            
        Returns:
            Tuple of (score, reasoning)
        """
        self._ensure_ai_judge()
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
        self._ensure_ai_judge()
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
            if test_type == 'mcq' and self.mcq_type == 'tool':
                score, reasoning = self.score_mcq_auto(result)
            elif test_type == 'mcq':
                score, reasoning = self.score_mcq(result)
            else:
                score, reasoning = self.score_saq(result)
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
