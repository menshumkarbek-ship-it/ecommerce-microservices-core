import os
import re
from flask import Flask, request, jsonify
from fpdf import FPDF
from flasgger import Swagger  # 1. Import Flasgger

app = Flask(__name__)

# 2. Configure Flasgger metadata
app.config['SWAGGER'] = {
    'title': 'TechVault Invoice Generator API',
    'uiversion': 3
}
swagger = Swagger(app)

# Ensure a directory exists to save our generated PDF invoices
INVOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(79, 70, 229)  # TechVault Indigo Brand Color
        self.cell(0, 10, 'TECHVAULT ELECTRONICS INVOICE', 0, 1, 'C')
        self.ln(10)


@app.route('/api/v1/generate-invoice', methods=['POST'])
def generate_invoice():
    """
    Generate a Dynamic PDF Invoice
    ---
    tags:
      - Invoice Generation
    summary: "Receive purchase details and compile a physical invoice PDF"
    parameters:
      - name: body
        in: body
        required: true
        schema:
          required:
            - order_id
            - customer_name
            - product_name
            - price
          properties:
            order_id:
              type: string
              example: "1042"
              description: Unique identifier for the transaction
            customer_name:
              type: string
              example: "Alice Smith"
              description: Full name of the customer
            product_name:
              type: string
              example: "MacBook Pro 16 M3"
              description: Device purchased
            price:
              type: string
              example: "2499.99"
              description: Final transaction amount
    responses:
      201:
        description: Invoice compiled successfully
        schema:
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "Invoice PDF generated successfully for Order #1042"
            invoice_path:
              type: string
              example: "/path/to/invoice.pdf"
      400:
        description: Invalid request body
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid order payload"}), 400

    order_id = data.get("order_id", "0000")
    customer_name = data.get("customer_name", "Anonymous User")
    product_name = data.get("product_name", "Premium Tech Device")
    price = data.get("price", "0.00")

    # Initialize PDF builder
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Write Invoice Details
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Invoice Ref: #TV-{order_id}", 0, 1)
    pdf.cell(0, 10, f"Customer: {customer_name}", 0, 1)
    pdf.cell(0, 10, f"Purchased Item: {product_name}", 0, 1)
    pdf.cell(0, 10, f"Price Settled: ${price}", 0, 1)

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Thank you for shopping at TechVault!", 0, 1, 'C')

    # Save the file locally
    safe_order_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(order_id))[:80] or "0000"
    pdf_filename = f"invoice_order_{safe_order_id}.pdf"
    pdf_path = os.path.join(INVOICE_DIR, pdf_filename)
    pdf.output(pdf_path)

    return jsonify({
        "status": "success",
        "message": f"Invoice PDF generated successfully for Order #{order_id}",
        "invoice_path": pdf_path
    }), 201


if __name__ == '__main__':
    # Run Flask on Port 8002
    app.run(port=8002, debug=os.getenv('DEBUG', 'False').lower() == 'true')
