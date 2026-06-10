import base64
import binascii
import json
import os
from datetime import datetime
from pathlib import Path
from html import escape
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import ExpenseAgent
from sheet import GoogleSheetsClient

BASE_DIR = Path(__file__).parent
MAX_FILE_SIZE = 5 * 1024 * 1024 
ALLOWED_TYPES = {"image/jpeg", "image/png"}

app = FastAPI(title="Gestionnaire de Notes de Frais Agentique")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

agent = ExpenseAgent()
google_sheets_client = GoogleSheetsClient()



def build_form_fragment(data: dict, image_data_url: str) -> str:
    fournisseur = escape(str(data.get("fournisseur", "") or ""))
    date = escape(str(data.get("date", "") or ""))
    montant_ttc = escape(str(data.get("montant_ttc", "") or ""))
    tva = escape(str(data.get("tva", "") or ""))
    devise = escape(str(data.get("devise", "EUR") or "EUR"))
    description = escape(str(data.get("description", "") or ""))
    category = data.get("type", "")


    options = ""
    for cat in ["Restaurant", "Transport", "Hébergement", "Fournitures", "Autre"]:
        selected = 'selected' if category == cat else ''
        options += f'<option value="{cat}" {selected}>{cat}</option>'


    return f"""
<form hx-post="/api/submit" hx-target="#result-zone" class="expense-form">
    <h3>Vérification des données de la note de frais</h3>
    
    <input type="hidden" name="image_data" value="{image_data_url}">

    <div class="form-group">
        <label>Fournisseur</label>
        <input type="text" name="fournisseur" value="{fournisseur}" required>
    </div>

    <div class="form-group">
        <label>Date (AAAA-MM-JJ)</label>
        <input type="date" name="date" value="{date}">
    </div>

    <div class="form-group">
        <label>Montant TTC</label>
        <input type="number" step="0.01" name="montant_ttc" value="{montant_ttc}" required>
    </div>

    <div class="form-group">
        <label>Montant TVA</label>
        <input type="number" step="0.01" name="tva" value="{tva}">
    </div>

    <div class="form-group">
        <label>Devise</label>
        <input type="text" name="devise" value="{devise}">
    </div>

    <div class="form-group">
        <label>Catégorie</label>
        <select name="type">
            {options}
        </select>
    </div>

    <div class="form-group">
        <label>Description</label>
        <textarea name="description">{description}</textarea>
    </div>

    <button type="submit" class="btn-submit">
        Valider et Enregistrer la dépense
    </button>
</form>
"""

@app.exception_handler(HTTPException)
async def htmx_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content=f'<p class="result-error">Erreur {exc.status_code} : {escape(str(exc.detail))}</p>',
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return HTMLResponse(
        content=f'<p class="result-error">Erreur interne : {escape(str(exc))}</p>',
        status_code=500,
    )


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze_image(file: UploadFile = File(...)):

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, detail="Type de fichier non supporté. Veuillez envoyer une image.")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, detail=f"Format non supporté. Formats acceptés : JPEG, PNG.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="Image trop volumineuse (maximum 5 Mo).")

    try:
        result = agent.extract_from_bytes(image_bytes, media_type=file.content_type)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur du modèle d'extraction : {str(e)}")


    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{file.content_type};base64,{image_base64}"

  
    return HTMLResponse(content=build_form_fragment(result, image_data_url))



def parse_data_url(image_data: str) -> bytes:
    if not image_data or not image_data.startswith("data:") or "," not in image_data:
        raise HTTPException(status_code=400, detail="Image encodée invalide.")

    _, encoded = image_data.split(",", 1)
    try:
        return base64.b64decode(encoded)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Image encodée invalide.")


@app.post("/api/submit", response_class=HTMLResponse)
async def submit_expense(
    fournisseur: str = Form(...),
    date: str = Form(None),
    montant_ttc: float = Form(...),
    tva: float = Form(None),
    devise: str = Form("EUR"),
    expense_type: str = Form(..., alias="type"),
    description: str = Form(""),
    image_data: str = Form(...),
):
    image_bytes = parse_data_url(image_data)
    extension = "jpg" if "image/jpeg" in image_data else "png" if "image/png" in image_data else "bin"
    filename = f"ticket-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{extension}"

    try:
        image_url = google_sheets_client.upload_image(image_bytes, filename)
        google_sheets_client.append_expense(
            {
                "fournisseur": fournisseur or None,
                "date": date or None,
                "montant_ttc": montant_ttc,
                "tva": tva if tva is not None else None,
                "devise": devise or "EUR",
                "type": expense_type,
                "description": description or None,
            },
            image_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return HTMLResponse(content="""
<div class="success-message">
    <strong>Enregistrement réussi !</strong> La dépense a bien été enregistrée.
</div>
""")