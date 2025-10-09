import os, random
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tqdm import tqdm

fake = Faker()

def generate_invoice(filename, num_pages=50):
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    for p in range(num_pages):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, h - 60, f"INVOICE - Page {p+1}")
        c.setFont("Helvetica", 11)
        c.drawString(50, h - 100, f"Invoice ID: {fake.uuid4()[:8].upper()}")
        c.drawString(50, h - 120, f"Date: {fake.date_this_year()}")
        c.drawString(50, h - 140, f"Customer Name: {fake.name()}")
        c.drawString(50, h - 160, f"Company: {fake.company()}")
        c.drawString(50, h - 180, "Address: " + fake.address().replace("\n", ", "))
        c.drawString(50, h - 220, f"Phone: {fake.phone_number()}")

        total = 0
        y = h - 260
        for _ in range(random.randint(3, 7)):
            item = fake.catch_phrase()
            qty = random.randint(1, 10)
            price = round(random.uniform(10, 200), 2)
            total += qty * price
            c.drawString(50, y, item[:35])
            y -= 20

        c.drawString(50, y - 10, f"Total: ${total:.2f}")
        c.showPage()
    c.save()


def generate_contract(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 60, "CONTRACT AGREEMENT")
    c.setFont("Helvetica", 11)
    c.drawString(50, h - 100, f"Contract ID: {fake.uuid4()[:8].upper()}")
    c.drawString(50, h - 120, f"Effective Date: {fake.date_this_year()}")
    c.drawString(50, h - 140, f"Client Name: {fake.name()}")
    c.drawString(50, h - 160, f"Client Company: {fake.company()}")
    c.drawString(50, h - 180, "Address: " + fake.address().replace("\n", ", "))

    c.setFont("Times-Roman", 11)
    clauses = [
        "The client agrees to pay the contractor within 30 days of receipt of invoice.",
        "Both parties shall maintain confidentiality of proprietary information.",
        "This agreement is governed by the laws of the State of New York.",
        "Either party may terminate this agreement with 30 days written notice."
    ]
    y = h - 230
    for i, cl in enumerate(clauses, 1):
        c.drawString(50, y, f"Clause {i}: {cl}")
        y -= 30

    c.drawString(50, y - 30, "Client Signature: ______________________")
    c.drawString(300, y - 30, "Date: __________")
    c.drawString(50, y - 60, "Contractor Signature: ______________________")
    c.drawString(300, y - 60, "Date: __________")
    c.showPage()
    c.save()


def generate_invoices_multi_page(filename, pages=50):
    """Create a single PDF containing `pages` invoice pages."""
    os.makedirs("output", exist_ok=True)
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    for p in range(pages):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, h - 60, f"INVOICE - Page {p+1}")
        c.setFont("Helvetica", 11)
        c.drawString(50, h - 100, f"Invoice ID: {fake.uuid4()[:8].upper()}")
        c.drawString(50, h - 120, f"Date: {fake.date_this_year()}")
        c.drawString(50, h - 140, f"Customer Name: {fake.name()}")
        c.drawString(50, h - 160, f"Company: {fake.company()}")
        c.drawString(50, h - 180, "Address: " + fake.address().replace("\n", ", "))
        c.drawString(50, h - 220, f"Phone: {fake.phone_number()}")

        total = 0
        y = h - 260
        for _ in range(random.randint(3, 7)):
            item = fake.catch_phrase()
            qty = random.randint(1, 10)
            price = round(random.uniform(10, 200), 2)
            total += qty * price
            c.drawString(50, y, item[:35])
            y -= 20

        c.drawString(50, y - 10, f"Total: ${total:.2f}")
        c.showPage()
    c.save()


def generate_contracts_multi_page(filename, pages=50):
    """Create a single PDF containing `pages` contract pages."""
    os.makedirs("output", exist_ok=True)
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    for p in range(pages):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, h - 60, f"CONTRACT AGREEMENT - Page {p+1}")
        c.setFont("Helvetica", 11)
        c.drawString(50, h - 100, f"Contract ID: {fake.uuid4()[:8].upper()}")
        c.drawString(50, h - 120, f"Effective Date: {fake.date_this_year()}")
        c.drawString(50, h - 140, f"Client Name: {fake.name()}")
        c.drawString(50, h - 160, f"Client Company: {fake.company()}")
        c.drawString(50, h - 180, "Address: " + fake.address().replace("\n", ", "))

        c.setFont("Times-Roman", 11)
        clauses = [
            "The client agrees to pay the contractor within 30 days of receipt of invoice.",
            "Both parties shall maintain confidentiality of proprietary information.",
            "This agreement is governed by the laws of the State of New York.",
            "Either party may terminate this agreement with 30 days written notice."
        ]
        y = h - 230
        for i, cl in enumerate(clauses, 1):
            c.drawString(50, y, f"Clause {i}: {cl}")
            y -= 30

        c.drawString(50, y - 30, "Client Signature: ______________________")
        c.drawString(300, y - 30, "Date: __________")
        c.drawString(50, y - 60, "Contractor Signature: ______________________")
        c.drawString(300, y - 60, "Date: __________")
        c.showPage()
    c.save()


def main():
    # Create folders for separate files
    os.makedirs("output/invoices", exist_ok=True)
    os.makedirs("output/contracts", exist_ok=True)

    print("Generating 50 invoice files (each 50 pages)...")
    for i in tqdm(range(1, 51)):
        generate_invoices_multi_page(f"output/invoices/invoice_{i:03d}.pdf", pages=50)

    print("Generating 50 contract files (each 50 pages)...")
    for i in tqdm(range(1, 51)):
        generate_contracts_multi_page(f"output/contracts/contract_{i:03d}.pdf", pages=50)

if __name__ == "__main__":
    main()
