"""
Image Scanner Tool - OCR and image analysis for extracting code and text from images.
Uses Tesseract OCR and optional vision models for advanced analysis.
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING, Any
from dataclasses import dataclass

if TYPE_CHECKING:
    from PIL import Image as PILImage

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from langchain_ollama.llms import OllamaLLM


@dataclass
class ImageScanResult:
    """Result from scanning an image."""
    raw_text: str
    code_blocks: list[str]
    description: str
    file_type_hints: list[str]
    confidence: float


class ImageScanner:
    """
    Scans images to extract text, code, and understand visual content.
    
    Features:
    - OCR text extraction using Tesseract
    - Code block detection and formatting
    - Vision model integration for diagram understanding
    - Screenshot analysis for UI/UX feedback
    """

    def __init__(
        self,
        vision_model: str = "llava:7b",  # Ollama vision model
        use_vision_model: bool = True,
    ):
        self.vision_model = vision_model
        self.use_vision_model = use_vision_model
        
        if use_vision_model:
            try:
                self.llm = OllamaLLM(model=vision_model)
            except Exception:
                self.llm = None
                self.use_vision_model = False

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for image processing. "
                "Install with: pip install Pillow"
            )

    def _load_image(self, image_source: Union[str, Path, bytes]) -> Any:
        """Load image from various sources."""
        self._check_dependencies()
        
        if isinstance(image_source, bytes):
            return Image.open(io.BytesIO(image_source))
        elif isinstance(image_source, (str, Path)):
            path = Path(image_source)
            if path.exists():
                return Image.open(path)
            # Check if it's base64
            elif isinstance(image_source, str) and len(image_source) > 100:
                try:
                    decoded = base64.b64decode(image_source)
                    return Image.open(io.BytesIO(decoded))
                except Exception:
                    pass
            raise FileNotFoundError(f"Image not found: {image_source}")
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")

    def _image_to_base64(self, image: Any) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def extract_text_ocr(self, image_source: Union[str, Path, bytes]) -> str:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image_source: Path to image, bytes, or base64 string
            
        Returns:
            Extracted text
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "pytesseract is required for OCR. "
                "Install with: pip install pytesseract\n"
                "Also install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
        
        image = self._load_image(image_source)
        
        # Preprocess for better OCR
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        return text.strip()

    def extract_code_blocks(self, text: str) -> list[str]:
        """
        Extract code blocks from OCR text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            List of detected code blocks
        """
        code_blocks = []
        
        # Pattern 1: Markdown code blocks
        markdown_pattern = r"```[\w]*\n?(.*?)```"
        matches = re.findall(markdown_pattern, text, re.DOTALL)
        code_blocks.extend(matches)
        
        # Pattern 2: Indented code (4+ spaces or tabs)
        lines = text.split("\n")
        current_block = []
        in_code_block = False
        
        for line in lines:
            is_code_line = (
                line.startswith("    ") or 
                line.startswith("\t") or
                re.match(r"^\s*(def |class |import |from |if |for |while |return |async )", line) or
                re.match(r"^\s*(function |const |let |var |import |export |async )", line) or
                re.match(r"^\s*[{}\[\]();]", line)
            )
            
            if is_code_line:
                in_code_block = True
                current_block.append(line)
            elif in_code_block and line.strip() == "":
                current_block.append(line)
            elif in_code_block:
                if len(current_block) >= 2:
                    code_blocks.append("\n".join(current_block))
                current_block = []
                in_code_block = False
        
        if current_block and len(current_block) >= 2:
            code_blocks.append("\n".join(current_block))
        
        return code_blocks

    def detect_file_types(self, text: str) -> list[str]:
        """
        Detect likely programming languages/file types from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected file type hints
        """
        hints = []
        
        patterns = {
            "python": [r"\bdef \w+\(", r"\bimport \w+", r"\bclass \w+:", r"\.py\b"],
            "javascript": [r"\bfunction\s+\w+", r"\bconst\s+\w+", r"\blet\s+\w+", r"\.js\b"],
            "typescript": [r":\s*(string|number|boolean)", r"\binterface\s+\w+", r"\.ts\b"],
            "html": [r"<html", r"<div", r"<body", r"</\w+>", r"\.html\b"],
            "css": [r"\{[^}]*:\s*[^}]+\}", r"\.css\b", r"@media", r"@import"],
            "json": [r'"\w+":\s*[{\["0-9]', r"\.json\b"],
            "sql": [r"\bSELECT\b", r"\bFROM\b", r"\bWHERE\b", r"\bINSERT\b"],
            "bash": [r"#!/bin/bash", r"\$\w+", r"\.sh\b"],
            "yaml": [r"^\s*\w+:\s*$", r"\.ya?ml\b"],
            "dockerfile": [r"\bFROM\s+\w+", r"\bRUN\s+", r"\bCOPY\s+"],
        }
        
        text_lower = text.lower()
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    if lang not in hints:
                        hints.append(lang)
                    break
        
        return hints

    def analyze_with_vision(
        self,
        image_source: Union[str, Path, bytes],
        prompt: str = "Describe this image in detail, focusing on any code, UI elements, or technical content.",
    ) -> str:
        """
        Analyze image using a vision-capable LLM.
        
        Args:
            image_source: Image to analyze
            prompt: Analysis prompt
            
        Returns:
            Vision model's analysis
        """
        if not self.use_vision_model or not self.llm:
            return "Vision model not available. Install llava or similar vision model."
        
        image = self._load_image(image_source)
        image_b64 = self._image_to_base64(image)
        
        # Note: This requires Ollama vision model support
        # The actual implementation depends on langchain-ollama version
        try:
            response = self.llm.invoke(
                prompt,
                images=[image_b64],
            )
            return response
        except Exception as e:
            return f"Vision analysis failed: {e}"

    def scan(
        self,
        image_source: Union[str, Path, bytes],
        use_ocr: bool = True,
        use_vision: bool = True,
    ) -> ImageScanResult:
        """
        Comprehensive image scan combining OCR and vision analysis.
        
        Args:
            image_source: Image to scan
            use_ocr: Whether to use OCR for text extraction
            use_vision: Whether to use vision model for analysis
            
        Returns:
            ImageScanResult with extracted data
        """
        raw_text = ""
        description = ""
        confidence = 0.5
        
        # OCR extraction
        if use_ocr:
            try:
                raw_text = self.extract_text_ocr(image_source)
                if raw_text:
                    confidence += 0.25
            except ImportError as e:
                raw_text = f"OCR unavailable: {e}"
            except Exception as e:
                raw_text = f"OCR failed: {e}"
        
        # Vision analysis
        if use_vision and self.use_vision_model:
            try:
                description = self.analyze_with_vision(image_source)
                if description and "failed" not in description.lower():
                    confidence += 0.25
            except Exception as e:
                description = f"Vision analysis failed: {e}"
        
        # Extract code blocks
        code_blocks = self.extract_code_blocks(raw_text) if raw_text else []
        
        # Detect file types
        file_type_hints = self.detect_file_types(raw_text) if raw_text else []
        
        return ImageScanResult(
            raw_text=raw_text,
            code_blocks=code_blocks,
            description=description,
            file_type_hints=file_type_hints,
            confidence=min(confidence, 1.0),
        )

    def scan_screenshot_for_ui_feedback(
        self,
        image_source: Union[str, Path, bytes],
    ) -> str:
        """
        Analyze a UI screenshot and provide feedback.
        
        Args:
            image_source: Screenshot image
            
        Returns:
            UI/UX feedback
        """
        prompt = """Analyze this UI screenshot and provide:
1. Overall UI/UX assessment
2. Layout and spacing issues
3. Color and contrast concerns
4. Accessibility issues
5. Suggestions for improvement
6. Comparison to modern design principles

Be specific and actionable."""

        return self.analyze_with_vision(image_source, prompt)

    def scan_architecture_diagram(
        self,
        image_source: Union[str, Path, bytes],
    ) -> str:
        """
        Analyze an architecture diagram and extract structure.
        
        Args:
            image_source: Diagram image
            
        Returns:
            Structured description of the architecture
        """
        prompt = """Analyze this architecture/system diagram and provide:
1. List of components/services identified
2. Data flow and connections
3. Technologies suggested by the diagram
4. Potential implementation approach
5. Any concerns or improvements

Format the output as a structured specification."""

        return self.analyze_with_vision(image_source, prompt)


# Convenience function for quick scanning
def scan_image(image_path: str) -> ImageScanResult:
    """Quick scan of an image file."""
    scanner = ImageScanner(use_vision_model=False)  # OCR only for speed
    return scanner.scan(image_path)
