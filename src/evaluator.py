"""Test evaluation and execution module."""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from tqdm import tqdm

from src.models.base_model import BaseModel
from src.utils.logger import setup_logger


# Tool definition for MCQ tool-call mode
MCQ_TOOL_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "submit_answer",
            "description": "Çoktan seçmeli sorunun doğru cevap şıkkını gönder",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "enum": ["A", "B", "C", "D"],
                        "description": "Doğru cevap şıkkı (A, B, C veya D)",
                    }
                },
                "required": ["answer"],
            },
        },
    }
]


@dataclass
class TestResult:
    """Container for test result."""
    question_id: int
    category: str
    question: str
    expected_answer: str
    model_answer: str
    score: Optional[float] = None
    judge_reasoning: Optional[str] = None
    error: Optional[str] = None
    response_time: Optional[float] = None


class Evaluator:
    """Evaluates model on MCQ and SAQ benchmarks."""
    
    def __init__(self, config: Dict[str, Any], model: BaseModel, logger=None, mcq_type: str = 'ai'):
        """
        Initialize evaluator.
        
        Args:
            config: Configuration dictionary
            model: Model instance to evaluate
            logger: Logger instance
            mcq_type: MCQ scoring mode ('ai' for LLM judge, 'tool' for tool-call auto scoring)
        """
        self.config = config
        self.model = model
        self.logger = logger or setup_logger()
        self.mcq_type = mcq_type
        
        self.mcq_path = config['paths']['mcq_data']
        self.saq_path = config['paths']['saq_data']
        self.batch_size = config['test_settings']['batch_size']
        self.timeout = config['test_settings']['timeout_seconds']
        self.save_intermediate = config['test_settings']['save_intermediate']
        self.intermediate_dir = Path(config['test_settings']['intermediate_dir'])
    
    def load_questions(self, test_type: str) -> List[Dict[str, Any]]:
        """
        Load questions from JSON file.
        
        Args:
            test_type: 'mcq' or 'saq'
            
        Returns:
            List of question dictionaries
        """
        path = self.mcq_path if test_type == 'mcq' else self.saq_path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Fill empty categories with the last non-empty category
            last_category = ""
            for question in questions:
                if question.get('Test Kategorisi', '').strip():
                    last_category = question['Test Kategorisi'].strip()
                else:
                    question['Test Kategorisi'] = last_category
            
            self.logger.info(f"{test_type.upper()} soruları yüklendi: {len(questions)} soru")
            return questions
        except Exception as e:
            self.logger.error(f"Soru yükleme hatası ({path}): {str(e)}")
            raise
    
    def create_mcq_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create prompt for MCQ question.
        
        Args:
            question_data: Question dictionary
            
        Returns:
            Formatted prompt
        """
        question = question_data['Soru']
        prompt = f"""Aşağıdaki Türkçe çoktan seçmeli soruyu yanıtlayın. Sadece doğru şıkkı belirtin (örn: "A", "Doğru cevap: B", vb.).

Soru:
{question}

Cevap:"""
        return prompt
    
    def create_mcq_tool_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create prompt for MCQ question in tool-call mode.
        
        Args:
            question_data: Question dictionary
            
        Returns:
            Formatted prompt instructing the model to use submit_answer tool
        """
        question = question_data['Soru']
        prompt = f"""Aşağıdaki Türkçe çoktan seçmeli soruyu analiz et ve doğru cevabı submit_answer fonksiyonunu kullanarak gönder.

Soru:
{question}"""
        return prompt
    
    def create_saq_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create prompt for SAQ question.
        
        Args:
            question_data: Question dictionary
            
        Returns:
            Formatted prompt
        """
        question = question_data['Soru']
        prompt = f"""Aşağıdaki soruyu yanıtlayın. Kısa ve öz bir cevap verin.

Soru: {question}

Cevap:"""
        return prompt
    
    def run_test(self, test_type: str = 'mcq', resume_from: Optional[int] = None) -> List[TestResult]:
        """
        Run test on model.
        
        Args:
            test_type: 'mcq' or 'saq'
            resume_from: Question index to resume from (if interrupted)
            
        Returns:
            List of test results
        """
        self.logger.info(f"{test_type.upper()} testi başlatılıyor...")
        
        # Load questions
        questions = self.load_questions(test_type)
        
        # Load intermediate results if resuming
        results = []
        start_idx = resume_from or 0
        
        if start_idx > 0:
            intermediate_file = self.intermediate_dir / f"{test_type}_intermediate.json"
            if intermediate_file.exists():
                with open(intermediate_file, 'r', encoding='utf-8') as f:
                    results = [TestResult(**r) for r in json.load(f)]
                self.logger.info(f"Ara sonuçlar yüklendi: {len(results)} soru tamamlanmış")
        
        # Process questions
        prompt_func = self.create_mcq_prompt if test_type == 'mcq' else self.create_saq_prompt
        use_tool_call = (test_type == 'mcq' and self.mcq_type == 'tool')
        
        if use_tool_call:
            prompt_func = self.create_mcq_tool_prompt
            self.logger.info("MCQ tool-call modu aktif: Model cevapları tool call ile alınacak")
        
        for idx in tqdm(range(start_idx, len(questions)), desc=f"{test_type.upper()} Test"):
            question_data = questions[idx]
            
            try:
                # Create prompt
                prompt = prompt_func(question_data)
                
                # Get model response
                start_time = time.time()
                
                if use_tool_call:
                    # Tool call mode: model calls submit_answer with the answer letter
                    tool_result = self.model.generate_with_tools(
                        prompt,
                        tools=MCQ_TOOL_DEFINITION,
                        tool_choice="required",
                        temperature=0.3,
                        max_tokens=10240,
                        timeout=self.config.get('test_settings', {}).get('timeout_seconds', 60),
                    )
                    model_answer = tool_result['arguments'].get('answer', '')
                else:
                    # Standard text generation mode
                    model_answer = self.model.generate(
                        prompt,
                        # GPT-5 modellerinde sadece 1 destekleniyor; model wrapper bunu güvenli 1'e çevirir
                        temperature=0.3,
                        max_tokens=10240,
                        timeout=self.config.get('test_settings', {}).get('timeout_seconds', 60),
                    )
                
                response_time = time.time() - start_time
                
                # Create result
                result = TestResult(
                    question_id=idx,
                    category=question_data.get('Test Kategorisi', ''),
                    question=question_data['Soru'],
                    expected_answer=question_data['Cevap'],
                    model_answer=model_answer,
                    response_time=response_time
                )
                
            except Exception as e:
                self.logger.error(f"Soru {idx} hatası: {str(e)}")
                result = TestResult(
                    question_id=idx,
                    category=question_data.get('Test Kategorisi', ''),
                    question=question_data['Soru'],
                    expected_answer=question_data['Cevap'],
                    model_answer="",
                    error=str(e)
                )
            
            results.append(result)
            
            # Save intermediate results
            if self.save_intermediate and (idx + 1) % self.batch_size == 0:
                self._save_intermediate(results, test_type)
        
        # Final save
        if self.save_intermediate:
            self._save_intermediate(results, test_type)
        
        self.logger.info(f"{test_type.upper()} testi tamamlandı: {len(results)} soru")
        return results
    
    def _save_intermediate(self, results: List[TestResult], test_type: str) -> None:
        """Save intermediate results to file."""
        try:
            intermediate_file = self.intermediate_dir / f"{test_type}_intermediate.json"
            with open(intermediate_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Ara sonuç kaydetme hatası: {str(e)}")

