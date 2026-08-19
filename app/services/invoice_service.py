import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.payment import Invoice, Payment
from app.models.case import Case
from app.repositories.payment_repository import PaymentRepository
from app.services.pdf_service import PDFService

class InvoiceService:
    def __init__(self, db: AsyncSession, pdf_service: PDFService):
        self.repository = PaymentRepository(db)
        self.pdf_service = pdf_service
        self.db = db

    async def generate_invoice(self, payment_id: uuid.UUID) -> Invoice:
        # 1. Fetch Payment and Case
        payment = await self.repository.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        case = await self.db.get(Case, payment.case_id)
        
        # 2. Check if invoice already exists
        existing = await self.repository.get_invoice_by_payment(payment_id)
        if existing:
            if existing.pdf_path:
                return existing
            else:
                invoice = existing
        else:
            # 3. Create Invoice Record
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
            
            tax_rate = 0.18 # Example 18% GST
            subtotal = payment.amount / (1 + tax_rate)
            tax = payment.amount - subtotal
    
            invoice_data = {
                "payment_id": payment.id,
                "invoice_number": invoice_number,
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "discount": 0.0,
                "total": payment.amount,
                "status": "GENERATED"
            }
            
            invoice = await self.repository.create_invoice(invoice_data)



        # 4. Generate PDF Document
        html_template = self._get_invoice_html()
        context = {
            "invoice": invoice,
            "payment": payment,
            "case": case,
            "date": datetime.utcnow().strftime("%B %d, %Y")
        }
        
        file_name = f"invoice_{invoice.invoice_number}.pdf"
        file_path = await self.pdf_service.generate_pdf(html_template, context, file_name)
        
        # 5. Update Invoice with PDF path
        updated_invoice = await self.repository.update_invoice(invoice.id, {"pdf_path": file_path})
        return updated_invoice

    def _get_invoice_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; color: #333; line-height: 1.6; }
                .header { border-bottom: 2px solid #1a365d; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #1a365d; margin: 0; }
                .details { margin-bottom: 30px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: left; }
                th { background-color: #f8fafc; }
                .totals { margin-top: 30px; float: right; width: 300px; }
                .totals table { margin-top: 0; }
                .totals td { border: none; padding: 5px; }
                .totals .grand-total { font-weight: bold; border-top: 2px solid #1a365d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TAX INVOICE</h1>
                <p>Legal AI System</p>
            </div>
            
            <div class="details">
                <p><strong>Invoice Number:</strong> {{ invoice.invoice_number }}</p>
                <p><strong>Date:</strong> {{ date }}</p>
                <p><strong>Case Reference:</strong> {{ case.case_number }} - {{ case.title }}</p>
                <p><strong>Payment Reference:</strong> {{ payment.gateway_payment_id }}</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Legal Services / Case Consultation</td>
                        <td>${{ "%.2f"|format(invoice.subtotal) }}</td>
                    </tr>
                </tbody>
            </table>

            <div class="totals">
                <table>
                    <tr>
                        <td>Subtotal:</td>
                        <td>${{ "%.2f"|format(invoice.subtotal) }}</td>
                    </tr>
                    <tr>
                        <td>Tax (18%):</td>
                        <td>${{ "%.2f"|format(invoice.tax) }}</td>
                    </tr>
                    <tr class="grand-total">
                        <td>Total Paid:</td>
                        <td>${{ "%.2f"|format(invoice.total) }}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
