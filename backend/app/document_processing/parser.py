import io
import re
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Indicators of brand governance rules, policies, and constraints
RULE_INDICATOR_PATTERN = re.compile(
    r'\b(must|must not|shall|shall not|should|should not|always|never|prohibited|forbidden|required|mandatory|strictly|cannot|do not|don\'t)\b',
    re.IGNORECASE
)


class DocumentParser:
    @staticmethod
    def validate_file(file: UploadFile) -> str:
        filename = file.filename or ""
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Only text-based PDF (.pdf) and Microsoft Word (.docx) files are supported."
            )
        return ext

    @staticmethod
    def extract_text(file_bytes: bytes, ext: str) -> str:
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        text_content = []
        if ext == ".pdf":
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                for idx, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted and extracted.strip():
                        text_content.append(extracted.strip())
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to parse PDF document: {str(e)}"
                )
        elif ext == ".docx":
            try:
                doc = Document(io.BytesIO(file_bytes))
                for paragraph in doc.paragraphs:
                    p_text = paragraph.text.strip()
                    if p_text:
                        text_content.append(p_text)
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            text_content.append(row_text)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to parse DOCX document: {str(e)}"
                )

        full_text = "\n\n".join(text_content)
        if not full_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text found in the document. Scanned or image-only documents are not supported in MVP."
            )
        return full_text

    @staticmethod
    def extract_candidate_rules(text: str, source_filename: str) -> List[Dict[str, Any]]:
        """Parses extracted text into candidate brand guidelines.
        Filters for normative language (must, prohibited, required, etc.).
        """
        # Split text into candidate blocks (paragraphs and bulleted lines)
        raw_lines = re.split(r'[\r\n]+', text)
        candidates = []
        seen_texts = set()

        for line in raw_lines:
            cleaned = line.strip()
            # Clean bullet marks and numbers
            cleaned = re.sub(r'^[\*\-\•\–\—\d+\.]+\s*', '', cleaned).strip()

            if len(cleaned) < 15 or len(cleaned) > 500:
                continue

            # Must contain normative policy indicators
            if RULE_INDICATOR_PATTERN.search(cleaned):
                if cleaned in seen_texts:
                    continue
                seen_texts.add(cleaned)

                # Heuristics for category
                lower = cleaned.lower()
                if any(w in lower for w in ["energy", "saving", "efficiency", "performance", "speed", "test"]):
                    category = "performance"
                elif any(w in lower for w in ["warranty", "guarantee", "refund", "return", "replacement"]):
                    category = "warranty"
                elif any(w in lower for w in ["logo", "color", "font", "typography", "palette", "brand"]):
                    category = "visual"
                elif any(w in lower for w in ["prohibited", "banned", "never use", "forbidden", "term"]):
                    category = "terminology"
                else:
                    category = "compliance"

                # Extract title from first 6 words
                words = cleaned.split()
                title = " ".join(words[:min(6, len(words))]).capitalize()
                if not title.endswith(('.', ':', '-')):
                    title = title.rstrip(',')

                # Extract simple prohibited / required phrases if explicitly quoted
                quoted_terms = re.findall(r'["\']([^"\']+)["\']', cleaned)
                prohibited_phrases = []
                required_phrases = []

                if any(w in lower for w in ["never", "prohibited", "forbidden", "do not", "don't"]):
                    prohibited_phrases.extend(quoted_terms)
                if any(w in lower for w in ["always", "required", "mandatory", "must include"]):
                    required_phrases.extend(quoted_terms)

                candidates.append({
                    "title": title[:200],
                    "category": category,
                    "rule_text": cleaned,
                    "prohibited_phrases": prohibited_phrases,
                    "required_phrases": required_phrases,
                    "source": source_filename
                })

        return candidates

