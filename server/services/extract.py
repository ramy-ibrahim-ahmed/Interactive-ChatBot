import fitz
import asyncio
import structlog
import google.generativeai as genai
from PIL import Image as PILImage
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_fixed
from ..store.nlp import PromptFactory
from ..core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.get_logger(__name__)


class MarkdownService:
    def __init__(self):
        self.gemini_api_keys = SETTINGS.GEMINI_API_KEYS

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def ocr(self, image_bytes: bytes, gemini_api_key: str, prompt: str, model: str):
        pil_img = PILImage.open(BytesIO(image_bytes))
        genai.configure(api_key=gemini_api_key, transport="rest")
        gemini = genai.GenerativeModel(
            model,
            generation_config={"response_mime_type": "application/json"},
        )
        try:
            response = gemini.generate_content([prompt, pil_img])
            return response.text
        except Exception as e:
            LOGGER.exception(f"Operation failed, will retry... Error: {e}")
            raise e

    async def process_pdf(self, pdf_bytes: bytes, output_path: str, zoom=2.0):
        api_idx = 0
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        mat = fitz.Matrix(zoom, zoom)
        total_pages = len(pdf_document)

        LOGGER.info(f"Extracted {total_pages} pages")

        with open(output_path, "w", encoding="utf-8") as f:
            for page_number in range(total_pages):
                if page_number % 50 == 0 and page_number > 0:
                    api_idx += 1
                    LOGGER.info("Gemini API key changed...")
                api_idx %= len(self.gemini_api_keys)

                page = pdf_document.load_page(page_number)
                pix = page.get_pixmap(matrix=mat)
                image_bytes = pix.tobytes("png")

                text_extracted = self.ocr(
                    image_bytes,
                    self.gemini_api_keys[api_idx],
                    PromptFactory().get_prompt("ocr"),
                    "gemini-2.5-flash",
                )

                f.write(text_extracted)
                f.write("\n\n\n---#---\n\n\n")
                f.flush()

                await asyncio.sleep(1)

        pdf_document.close()
        LOGGER.info(f"Conversion successful. Output: {output_path}")
