"""
OCR Engine — Tesseract + advanced preprocessing
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pdf2image
from pathlib import Path
from typing import Union, Dict, Any
import io
import numpy as np
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OCREngine:
    def __init__(self):
        if settings.tesseract_path and settings.tesseract_path != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
        logger.info("OCR Engine initialized")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Multi-step preprocessing for blurry / handwritten prescriptions:
        grayscale → upscale → denoise → contrast → sharpen → binarize
        """
        try:
            image = image.convert('L')

            # Upscale to at least 1800px on the longer side
            w, h = image.size
            if max(w, h) < 1800:
                scale = 1800 / max(w, h)
                image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

            # Denoise
            image = image.filter(ImageFilter.MedianFilter(size=3))

            # Contrast + sharpness
            image = ImageEnhance.Contrast(image).enhance(2.5)
            image = ImageEnhance.Sharpness(image).enhance(2.5)

            # Binarize with Otsu-like threshold
            arr = np.array(image)
            threshold = arr.mean() * 0.85
            arr = np.where(arr > threshold, 255, 0).astype(np.uint8)
            image = Image.fromarray(arr)

            return image
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original: {e}")
            return image

    def extract_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Run Tesseract with multiple PSM modes, return best result"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            processed = self.preprocess_image(image)

            best_text, best_conf = "", 0.0
            for psm in [6, 4, 3, 11]:
                try:
                    text = pytesseract.image_to_string(
                        processed, lang=settings.tesseract_lang,
                        config=f'--psm {psm} --oem 3'
                    )
                    data = pytesseract.image_to_data(
                        processed, lang=settings.tesseract_lang,
                        output_type=pytesseract.Output.DICT,
                        config=f'--psm {psm} --oem 3'
                    )
                    confs = [int(c) for c in data['conf'] if str(c) != '-1' and int(c) >= 0]
                    avg = sum(confs) / len(confs) if confs else 0
                    if avg > best_conf:
                        best_conf, best_text = avg, text
                except Exception:
                    continue

            logger.info(f"Tesseract OCR done. Confidence: {best_conf:.1f}%")
            return {
                "text": best_text.strip(),
                "confidence": best_conf,
                "word_count": len(best_text.split()),
                "status": "success",
                "method": "tesseract"
            }
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {"text": "", "confidence": 0, "word_count": 0, "status": "error", "error": str(e)}

    def extract_from_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Convert PDF pages to images then OCR each page"""
        try:
            poppler_path = settings.poppler_path if settings.poppler_path else None
            images = pdf2image.convert_from_bytes(pdf_bytes, poppler_path=poppler_path, dpi=300)

            all_text, total_conf = [], 0
            for i, img in enumerate(images):
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                result = self.extract_from_image(buf.getvalue())
                if result["status"] == "success":
                    all_text.append(result["text"])
                    total_conf += result["confidence"]

            combined = "\n\n".join(all_text)
            return {
                "text": combined.strip(),
                "confidence": total_conf / len(images) if images else 0,
                "word_count": len(combined.split()),
                "page_count": len(images),
                "status": "success",
                "method": "tesseract_pdf"
            }
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return {"text": "", "confidence": 0, "word_count": 0, "status": "error", "error": str(e)}

    def extract(self, file_data: Union[str, Path, bytes], file_type: str = "image") -> Dict[str, Any]:
        if isinstance(file_data, (str, Path)):
            file_data = Path(file_data).read_bytes()
        return self.extract_from_pdf(file_data) if file_type == "pdf" else self.extract_from_image(file_data)


ocr_engine = OCREngine()
