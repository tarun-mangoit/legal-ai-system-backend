import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
from app.services.storage.provider import StorageProvider

class PDFService:
    def __init__(self, storage_provider: StorageProvider):
        self.storage = storage_provider
        
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        os.makedirs(template_dir, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(template_dir))

    async def generate_pdf(self, template_html: str, context: dict, file_name: str) -> str:
        # We can either use a template file or render raw HTML string
        # For this implementation, we will pass a jinja rendered string
        template = self.env.from_string(template_html)
        html_out = template.render(**context)
        
        pdf_bytes = HTML(string=html_out).write_pdf()
        
        # Save using storage provider
        path = f"{datetime.utcnow().strftime('%Y/%m')}/{file_name}"
        saved_path = await self.storage.save_file(pdf_bytes, path)
        return saved_path
