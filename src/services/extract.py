import fitz
import google.generativeai as genai
from PIL import Image as PILImage
from io import BytesIO
from tqdm import tqdm
from ..store.nlp import PromptFactory
from ..store.nlp.interfaces import BaseGenerator
from ..core.enums import OpenAIRolesEnum


class MarkdownService:
    def __init__(self, openai_nlp, settings):
        self.openai_nlp: BaseGenerator = openai_nlp
        self.gemini_name = settings.GEMINI_NAME
        self.gemini_api_keys = settings.GEMINI_API_KEYS

    def ocr(self, image_bytes: bytes, gemini_api_key: str, prompt: str, model: str):
        pil_img = PILImage.open(BytesIO(image_bytes))
        genai.configure(api_key=gemini_api_key, transport="rest")
        gemini = genai.GenerativeModel(
            model,
            generation_config={"response_mime_type": "application/json"},
        )
        response = gemini.generate_content([prompt, pil_img])
        return response.text

    async def md_convert(self, page):
        markdown_rewrite_prompt = (
            "Produce markdown directly from the following text without additional tags."
        )
        response = await self.openai_nlp.chat(
            messages=[
                {
                    "role": OpenAIRolesEnum.SYSTEM.value,
                    "content": markdown_rewrite_prompt,
                },
                {"role": OpenAIRolesEnum.USER.value, "content": page},
            ],
            model_name="gpt-4.1-mini",
        )
        return response.strip()

    async def process_pdf(self, pdf_bytes: bytes, zoom=2.0):
        extracted = list()
        api_idx = 0
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        mat = fitz.Matrix(zoom, zoom)
        total_pages = len(pdf_document)

        for page_number in tqdm(range(total_pages), total=total_pages):
            if page_number % 50 == 0 and page_number > 0:
                api_idx += 1
            api_idx %= len(self.gemini_api_keys)

            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap(matrix=mat)
            image_bytes = pix.tobytes("png")

            text_extracted = self.ocr(
                image_bytes,
                self.gemini_api_keys[api_idx],
                PromptFactory().get_prompt("vlm_markdown"),
                self.gemini_name,
            )
            final_text = await self.md_convert(text_extracted)
            extracted.append(final_text)

        pdf_document.close()

        return "\n\n\n---#---\n\n\n".join(extracted)
