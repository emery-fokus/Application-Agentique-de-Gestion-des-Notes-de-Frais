import base64
from pathlib import Path
from html import escape
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# On importe ton agent de frais du fichier backend.py
from backend import ExpenseAgent

BASE_DIR = Path(__file__).parent
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo (spécifié dans ton sujet)
ALLOWED_TYPES = {"image/jpeg", "image/png"}

app = FastAPI(title="Gestionnaire de Notes de Frais Agentique")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

agent = ExpenseAgent()


# --- 1. FONCTION DE CONSTRUCTION DU FRAGMENT (Comme le mentor) ---
def build_form_fragment(data: dict, image_data_url: str) -> str:
    # On sécurise les chaînes de caractères contre les injections de script (XSS)
    fournisseur = escape(str(data.get("fournisseur", "") or ""))
    date = escape(str(data.get("date", "") or ""))
    montant_ttc = escape(str(data.get("montant_ttc", "") or ""))
    tva = escape(str(data.get("tva", "") or ""))
    devise = escape(str(data.get("devise", "EUR") or "EUR"))
    description = escape(str(data.get("description", "") or ""))
    category = data.get("type", "")

    # On prépare la logique pour cocher dynamiquement la bonne option du <select>
    options = ""
    for cat in ["Restaurant", "Transport", "Hébergement", "Fournitures", "Autre"]:
        selected = 'selected' if category == cat else ''
        options += f'<option value="{cat}" {selected}>{cat}</option>'

    # On génère le gros formulaire HTML demandé
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


# --- 2. GESTIONNAIRE D'EXCEPTIONS POUR HTMX (Identique au mentor) ---
@app.exception_handler(HTTPException)
async def htmx_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content=f'<p class="result-error">Erreur {exc.status_code} : {exc.detail}</p>',
        status_code=exc.status_code,
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



@app.post("/api/submit", response_class=HTMLResponse)
async def submit_expense(
    fournisseur: str = Form(...),
    date: str = Form(...),
    montant_ttc: float = Form(...),
    tva: float = Form(None),      
    devise: str = Form("EUR"),
    type: str = Form(...),
    description: str = Form(""),   
    image_data: str = Form(...)    
):
    return HTMLResponse(content="""
<div class="success-message">
    <strong>Enregistrement réussi !</strong> Les données vérifiées ont été envoyées.
</div>
""")