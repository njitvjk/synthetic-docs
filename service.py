import os
import random
import tempfile
import zipfile
import io
from pathlib import Path
from typing import Literal, Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from fastapi import UploadFile, File, Form
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from faker import Faker

fake = Faker()
app = FastAPI(title="PDF Generator Service", version="0.1")


class GenerateRequest(BaseModel):
    doc_type: Literal["invoices", "contracts"] = "invoices"
    count: int = 1  # number of files to produce (for "separate" mode)
    pages: int = 50  # pages per file
    mode: Literal["single", "separate", "zip"] = "zip"
    filename: Optional[str] = None  # desired filename for single output


class FeedbackItem(BaseModel):
    confidence: float
    overridden: int | bool = 0
    reviewer: Optional[str] = None


class FeedbackRequest(BaseModel):
    feedback: List[FeedbackItem]
    previous_threshold: float = 0.95


def generate_invoice_file(path: str, pages: int = 50) -> None:
    c = canvas.Canvas(path, pagesize=A4)
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


def generate_contract_file(path: str, pages: int = 50) -> None:
    c = canvas.Canvas(path, pagesize=A4)
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


@app.post("/generate")
def generate(req: GenerateRequest):
    # validate inputs
    if req.count < 1 or req.count > 500:
        raise HTTPException(status_code=400, detail="count must be between 1 and 500")
    if req.pages < 1 or req.pages > 1000:
        raise HTTPException(status_code=400, detail="pages must be between 1 and 1000")

    gen_fn = generate_invoice_file if req.doc_type == "invoices" else generate_contract_file

    tmpdir = tempfile.mkdtemp(prefix="pdfgen_")
    try:
        # MODE: single -> return a single multi-page PDF
        if req.mode == "single":
            out_name = req.filename or f"{req.doc_type}_single_{req.pages}pages.pdf"
            out_path = os.path.join(tmpdir, out_name)
            gen_fn(out_path, pages=req.pages)
            return FileResponse(path=out_path, filename=out_name, media_type="application/pdf")

        # MODE: separate -> return a zip of individual files
        if req.mode in ("separate", "zip"):
            # create files
            files = []
            for i in range(1, req.count + 1):
                fname = f"{req.doc_type[:-1]}_{i:03d}.pdf"  # invoice_001.pdf or contract_001.pdf
                fpath = os.path.join(tmpdir, fname)
                gen_fn(fpath, pages=req.pages)
                files.append((fname, fpath))

            # if user specifically asked for separate files but not zipped, return first file (rare)
            if req.mode == "separate" and req.count == 1:
                return FileResponse(path=files[0][1], filename=files[0][0], media_type="application/pdf")

            # pack into zip
            zip_name = f"{req.doc_type}_{req.count}x{req.pages}pages.zip"
            zip_path = os.path.join(tmpdir, zip_name)
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, fpath in files:
                    zf.write(fpath, arcname=fname)

            return FileResponse(path=zip_path, filename=zip_name, media_type="application/zip")

        raise HTTPException(status_code=400, detail="invalid mode")

    finally:
        # NOTE: keep tmpdir for a short while so FileResponse can be consumed by client.
        # We won't remove it here because Starlette will stream the file; the system
        # tmp cleanup will reclaim it later. For production, add background cleanup.
        pass


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    max_pages: int = Form(0),
    max_words: int = Form(200),
):
    """Extract text from an uploaded PDF. Returns JSON with per-page text and full_text.

    - file: uploaded PDF file (multipart/form-data)
    - max_pages: optional form field to limit pages (0 = all)
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    # read into memory (small PDFs expected). If large files are expected, stream to temp file.
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")

    num_pages = len(reader.pages)
    limit = num_pages if (max_pages <= 0 or max_pages > num_pages) else max_pages

    pages_text = []
    for i in range(limit):
        try:
            page = reader.pages[i]
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages_text.append(text)

    full_text = "\n\n".join(pages_text)

    # Truncate to first N words if requested
    truncated = full_text
    if max_words and max_words > 0:
        words = full_text.split()
        if len(words) > max_words:
            truncated = " ".join(words[:max_words])

    return {
        "filename": file.filename,
        "num_pages": num_pages,
        "extracted_pages": limit,
        "word_limit": max_words,
        "text": truncated,
        "pages": pages_text,
        "full_text": full_text,
    }


@app.post("/feedback")
def receive_feedback(req: FeedbackRequest):
    """Accepts feedback with confidence scores and a previous threshold.

    Decision logic:
    - If any item has overridden truthy => accepted (override wins)
    - Else if any item has confidence >= previous_threshold => accepted
    - Else => rejected
    Returns a summary including per-item evaluation.
    """
    if not req.feedback:
        raise HTTPException(status_code=400, detail="feedback cannot be empty")

    try:
        override_used = any(bool(item.overridden) for item in req.feedback)
        max_conf = max(float(item.confidence) for item in req.feedback)
        meets_threshold = any(float(item.confidence) >= float(req.previous_threshold) for item in req.feedback)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    accepted = bool(override_used or meets_threshold)
    reason = "override" if override_used else ("meets_threshold" if meets_threshold else "below_threshold")

    details = [
        {
            "reviewer": item.reviewer,
            "confidence": float(item.confidence),
            "overridden": bool(item.overridden),
            "meets_threshold": float(item.confidence) >= float(req.previous_threshold),
        }
        for item in req.feedback
    ]

    return {
        "accepted": accepted,
        "reason": reason,
        "used_override": override_used,
        "previous_threshold": float(req.previous_threshold),
        "max_confidence": round(max_conf, 4),
        "meets_threshold": meets_threshold,
        "details": details,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("service:app", host="0.0.0.0", port=8000, log_level="info")
