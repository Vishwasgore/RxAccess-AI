"""
Tests for prescription extraction
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.ocr_engine import OCREngine
from src.extraction.llm_extractor import LLMExtractor


class TestOCREngine:
    """Test OCR engine"""
    
    def test_ocr_engine_initialization(self):
        """Test OCR engine can be initialized"""
        engine = OCREngine()
        assert engine is not None
    
    def test_preprocess_image(self):
        """Test image preprocessing"""
        from PIL import Image
        import numpy as np
        
        # Create test image
        img_array = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        engine = OCREngine()
        processed = engine.preprocess_image(img)
        
        assert processed is not None
        assert processed.mode == 'L'  # Grayscale


class TestLLMExtractor:
    """Test LLM extractor"""
    
    def test_extractor_initialization(self):
        """Test LLM extractor can be initialized"""
        try:
            extractor = LLMExtractor()
            assert extractor is not None
        except Exception as e:
            pytest.skip(f"LLM not available: {e}")
    
    def test_fallback_extraction(self):
        """Test fallback extraction"""
        extractor = LLMExtractor()
        
        test_text = """
        Patient Name: John Doe
        Dr. Jane Smith
        Medication: Lisinopril 10mg
        """
        
        result = extractor._extract_fallback(test_text)
        
        assert result is not None
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
