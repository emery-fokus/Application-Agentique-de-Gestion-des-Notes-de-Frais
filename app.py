# import base64
# import os
# from datetime import datetime
# from pathlib import Path
# from html import escape
# from dotenv import load_dotenv
# import cloudinary
# import cloudinary.uploader

# from fastapi import FastAPI, File, UploadFile, HTTPException, Request
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from starlette.middleware.base import BaseHTTPMiddleware

# from backend import ExpenseAgent
# from sheet import GoogleSheetsClient

# load_dotenv()

# # Configuration Cloudinary
# cloudinary.config(
#     cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
#     api_key=os.getenv("CLOUDINARY_API_KEY"),
#     api_secret=os.getenv("CLOUDINARY_API_SECRET")
# )

# # Utilisation de Path pour définir le chemin absolu vers le projet
# BASE_DIR = Path(__file__).resolve().parent
# app = FastAPI(title="Gestionnaire de Notes de Frais")

# # Middleware pour limiter la taille (15 Mo)
# class MaxUploadSizeMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if request.method == 'POST':
#             content_length = int(request.headers.get('content-length', 0))
#             if content_length > 15 * 1024 * 1024:
#                 return HTMLResponse(content='Payload trop volumineux', status_code=413)
#         return await call_next(request)

# app.add_middleware(MaxUploadSizeMiddleware)

# # CORRECTION 404 : Montage sécurisé avec BASE_DIR
# # Assure-toi que le dossier 'static' existe bien à la racine du projet
# app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# agent = ExpenseAgent()

# def get_sheets():
#     return GoogleSheetsClient()

# def parse_data_url(image_data: str) -> bytes:
#     _, encoded = image_data.split(",", 1)
#     return base64.b64decode(encoded)

# def build_form_fragment(data: dict, image_data_url: str) -> str:
#     f = lambda key: escape(str(data.get(key, "") or ""))
#     confiance = data.get("confiance", "moyenne")
    
#     couleur = "green" if confiance == "haute" else ("orange" if confiance == "moyenne" else "red")
    
#     return f"""
#     <div style="border: 2px solid {couleur}; padding: 15px; border-radius: 8px; margin-top: 20px;">
#         <p>Confiance : <strong style="color: {couleur}">{confiance.upper()}</strong></p>
#         <p><small>{escape(str(data.get("raison_confiance", "")))}</small></p>
#         <form hx-post="/api/submit" hx-target="#analysis-result">
#             <input type="hidden" name="image_data" value="{image_data_url}">
#             <input type="hidden" name="confiance" value="{confiance}">
#             <div class="field"><label>Fournisseur</label><input type="text" name="fournisseur" value="{f('fournisseur')}"></div>
#             <div class="field"><label>Date</label><input type="date" name="date" value="{f('date')}"></div>
#             <div class="field"><label>Montant TTC</label><input type="number" step="0.01" name="montant_ttc" value="{f('montant_ttc')}"></div>
#             <div class="field"><label>Type</label><input type="text" name="type_document" value="{f('type')}"></div>
#             <button type="submit" style="margin-top: 10px;">Enregistrer</button>
#         </form>
#     </div>
#     """

# @app.get("/", response_class=HTMLResponse)
# async def read_index():
#     # Sert le fichier index.html situé à la racine
#     with open(BASE_DIR / "index.html", "r", encoding="utf-8") as f:
#         return f.read()

# @app.post("/api/analyze")
# async def analyze_image(file: UploadFile = File(...)):
#     if file.content_type not in ["image/jpeg", "image/png"]:
#         raise HTTPException(status_code=400, detail="Format non supporté.")
        
#     image_bytes = await file.read()
#     result = agent.extract_from_bytes(image_bytes, media_type=file.content_type)
    
#     image_base64 = base64.b64encode(image_bytes).decode("utf-8")
#     image_data_url = f"data:{file.content_type};base64,{image_base64}"
#     return HTMLResponse(content=build_form_fragment(result, image_data_url))

# @app.post("/api/submit")
# async def submit_expense(request: Request):
#     form_data = await request.form()
    
#     fournisseur = form_data.get("fournisseur", "").upper()
#     type_doc = form_data.get("type_document", "").lower()
#     if "SNCF" in fournisseur:
#         type_doc = "transport"
        
#     image_url = ""
#     image_data = form_data.get("image_data")
#     if image_data and image_data.startswith("data:"):
#         try:
#             image_bytes = parse_data_url(image_data)
#             upload_result = cloudinary.uploader.upload(image_bytes, folder="notes_de_frais")
#             image_url = upload_result.get("secure_url")
#         except Exception as e:
#             print(f"Erreur Cloudinary : {e}")

#     final_data = {
#         "recorded_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
#         "type_document": type_doc,
#         "fournisseur": fournisseur,
#         "date": form_data.get("date"),
#         "montant_ttc": form_data.get("montant_ttc"),
#         "tva": form_data.get("tva"),
#         "devise": form_data.get("devise", "EUR"),
#         "description": form_data.get("description", ""),
#         "confiance": form_data.get("confiance", "moyenne")
#     }
    
#     get_sheets().append_expense(final_data, image_url=image_url)
#     return "<div style='color:green; font-weight:bold;'>Succès ! Dépense enregistrée.</div>"



# import base64
# import io
# from datetime import datetime
# from html import escape
# from pathlib import Path

# from dotenv import load_dotenv
# from fastapi import FastAPI, File, UploadFile, Request, Form
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles

# from backend import ExpenseAgent
# from sheet import GoogleSheetsClient

# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent
# app = FastAPI(title="Gestionnaire de Notes de Frais")

# app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# agent = ExpenseAgent()

# # FIX 4 : instanciation lazy pour ne pas planter au démarrage si .env absent
# def get_sheets() -> GoogleSheetsClient:
#     return GoogleSheetsClient()


# # ------------------------------------------------------------------ helpers

# ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
# MAX_SIZE_MB = 15


# def build_form(data: dict, img_data_url: str) -> str:
#     """Retourne un fragment HTML avec le formulaire pré-rempli."""
#     f = lambda k: escape(str(data.get(k, "") or ""))
#     confiance = data.get("confiance", "basse")
#     couleur = {"haute": "#28a745", "moyen": "#fd7e14", "basse": "#dc3545"}.get(confiance, "#dc3545")

#     type_options = ""
#     for val in ["restaurant", "transport", "hôtel", "autre"]:
#         selected = "selected" if data.get("type_document", "") == val else ""
#         type_options += f'<option value="{val}" {selected}>{val.capitalize()}</option>'

#     return f"""
#     <div style="border:2px solid {couleur}; padding:16px; border-radius:8px; margin-top:20px;">
#       <p>Confiance : <strong style="color:{couleur}">{confiance.upper()}</strong></p>
#       <form hx-post="/api/submit" hx-target="#confirmation-container" hx-encoding="multipart/form-data">
#         <input type="hidden" name="image_data" value="{img_data_url}">

#         <div class="field">
#           <label>Type de document</label>
#           <select name="type_document">{type_options}</select>
#         </div>
#         <div class="field">
#           <label>Fournisseur</label>
#           <input type="text" name="fournisseur" value="{f('fournisseur')}">
#         </div>
#         <div class="field">
#           <label>Date</label>
#           <input type="date" name="date" value="{f('date')}">
#         </div>
#         <div class="field">
#           <label>Montant TTC (€)</label>
#           <input type="number" step="0.01" name="montant_ttc" value="{f('montant_ttc')}">
#         </div>
#         <div class="field">
#           <label>TVA (€)</label>
#           <input type="number" step="0.01" name="tva" value="{f('tva')}">
#         </div>
#         <div class="field">
#           <label>Devise</label>
#           <input type="text" name="devise" value="{f('devise') or 'EUR'}">
#         </div>
#         <div class="field">
#           <label>Description</label>
#           <input type="text" name="description" value="{f('description')}">
#         </div>
#         <input type="hidden" name="confiance" value="{confiance}">

#         <button type="submit" style="margin-top:12px;">Envoyer vers le Google Sheet</button>
#       </form>
#     </div>
#     """


# # ------------------------------------------------------------------ routes

# # FIX 5 : route GET / pour servir index.html
# @app.get("/", response_class=HTMLResponse)
# async def read_index():
#     # Cherche d'abord dans static/, sinon à la racine du projet
#     index_path = BASE_DIR / "static" / "index.html"
#     if not index_path.exists():
#         index_path = BASE_DIR / "index.html"
#     with open(index_path, "r", encoding="utf-8") as fh:
#         return fh.read()


# @app.post("/api/analyze", response_class=HTMLResponse)
# async def analyze(file: UploadFile = File(...)):
#     # Validation type MIME
#     if file.content_type not in ALLOWED_TYPES:
#         return HTMLResponse(
#             content=f'<div class="error">Format non supporté : {file.content_type}. Utilisez JPEG ou PNG.</div>',
#             status_code=400
#         )

#     image_bytes = await file.read()

#     # Validation taille
#     if len(image_bytes) > MAX_SIZE_MB * 1024 * 1024:
#         return HTMLResponse(
#             content=f'<div class="error">Image trop volumineuse (max {MAX_SIZE_MB} Mo).</div>',
#             status_code=400
#         )

#     try:
#         result = agent.extract_from_bytes(image_bytes, file.content_type)
#     except Exception as e:
#         return HTMLResponse(
#             content=f'<div class="error">Erreur IA : {escape(str(e))}</div>',
#             status_code=500
#         )

#     img_data_url = f"data:{file.content_type};base64,{base64.b64encode(image_bytes).decode()}"
#     return HTMLResponse(content=build_form(result, img_data_url))


# # FIX 6 : route /api/submit complète (manquait totalement)
# @app.post("/api/submit", response_class=HTMLResponse)
# async def submit(request: Request):
#     form_data = await request.form()

#     # Upload image sur Drive si disponible
#     image_url = ""
#     image_data = form_data.get("image_data", "")
#     if image_data and image_data.startswith("data:"):
#         try:
#             header, encoded = image_data.split(",", 1)
#             media_type = header.split(":")[1].split(";")[0]
#             image_bytes = base64.b64decode(encoded)
#             image_url = get_sheets().upload_image_to_drive(image_bytes, media_type)
#         except Exception as e:
#             print(f"[WARN] Upload Drive échoué : {e}")

#     final_data = {
#         "recorded_at":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
#         "type_document": form_data.get("type_document", "autre"),
#         "fournisseur":   form_data.get("fournisseur", "").strip(),
#         "date":          form_data.get("date", ""),
#         "montant_ttc":   form_data.get("montant_ttc", ""),
#         "tva":           form_data.get("tva", ""),
#         "devise":        form_data.get("devise", "EUR"),
#         "description":   form_data.get("description", ""),
#         "confiance":     form_data.get("confiance", "basse"),
#     }

#     try:
#         get_sheets().append_expense(final_data, image_url=image_url)
#     except Exception as e:
#         return HTMLResponse(
#             content=f'<div class="error">Erreur Google Sheets : {escape(str(e))}</div>',
#             status_code=500
#         )

#     return HTMLResponse(content="""
#         <div style="color:#28a745; font-weight:bold; padding:16px; border:2px solid #28a745; border-radius:8px;">
#             ✅ Dépense enregistrée avec succès dans le Google Sheet !
#         </div>
#     """)


import base64
from datetime import datetime
from html import escape
from pathlib import Path

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import ExpenseAgent
from sheet import GoogleSheetsClient

load_dotenv()
# CLOUDINARY_URL dans .env configure automatiquement le SDK — pas besoin de cloudinary.config()

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Gestionnaire de Notes de Frais")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

agent = ExpenseAgent()

def get_sheets() -> GoogleSheetsClient:
    return GoogleSheetsClient()

def upload_to_cloudinary(image_bytes: bytes, media_type: str) -> str:
    """Upload vers Cloudinary et retourne l'URL sécurisée."""
    result = cloudinary.uploader.upload(
        image_bytes,
        folder="notes_de_frais",
        resource_type="image"
    )
    return result.get("secure_url", "")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 15


def build_form(data: dict, img_data_url: str) -> str:
    f = lambda k: escape(str(data.get(k, "") or ""))
    confiance = data.get("confiance", "basse")
    couleur = {"haute": "#28a745", "moyen": "#fd7e14", "basse": "#dc3545"}.get(confiance, "#dc3545")

    type_options = ""
    for val in ["restaurant", "transport", "hôtel", "autre"]:
        selected = "selected" if data.get("type_document", "") == val else ""
        type_options += f'<option value="{val}" {selected}>{val.capitalize()}</option>'

    return f"""
    <div style="border:2px solid {couleur}; padding:16px; border-radius:8px; margin-top:20px;">
      <p>Confiance : <strong style="color:{couleur}">{confiance.upper()}</strong></p>
      <form hx-post="/api/submit" hx-target="#confirmation-container" hx-encoding="multipart/form-data">
        <input type="hidden" name="image_data" value="{img_data_url}">
        <div class="field">
          <label>Type de document</label>
          <select name="type_document">{type_options}</select>
        </div>
        <div class="field">
          <label>Fournisseur</label>
          <input type="text" name="fournisseur" value="{f('fournisseur')}">
        </div>
        <div class="field">
          <label>Date</label>
          <input type="date" name="date" value="{f('date')}">
        </div>
        <div class="field">
          <label>Montant TTC (€)</label>
          <input type="number" step="0.01" name="montant_ttc" value="{f('montant_ttc')}">
        </div>
        <div class="field">
          <label>TVA (€)</label>
          <input type="number" step="0.01" name="tva" value="{f('tva')}">
        </div>
        <div class="field">
          <label>Devise</label>
          <input type="text" name="devise" value="{f('devise') or 'EUR'}">
        </div>
        <div class="field">
          <label>Description</label>
          <input type="text" name="description" value="{f('description')}">
        </div>
        <input type="hidden" name="confiance" value="{confiance}">
        <button type="submit" style="margin-top:12px;">Envoyer vers le Google Sheet</button>
      </form>
    </div>
    """


@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = BASE_DIR / "static" / "index.html"
    if not index_path.exists():
        index_path = BASE_DIR / "index.html"
    with open(index_path, "r", encoding="utf-8") as fh:
        return fh.read()


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        return HTMLResponse(
            content=f'<div class="error">Format non supporté : {file.content_type}. Utilisez JPEG ou PNG.</div>',
            status_code=400
        )
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE_MB * 1024 * 1024:
        return HTMLResponse(
            content=f'<div class="error">Image trop volumineuse (max {MAX_SIZE_MB} Mo).</div>',
            status_code=400
        )
    try:
        result = agent.extract_from_bytes(image_bytes, file.content_type)
    except Exception as e:
        return HTMLResponse(
            content=f'<div class="error">Erreur IA : {escape(str(e))}</div>',
            status_code=500
        )
    img_data_url = f"data:{file.content_type};base64,{base64.b64encode(image_bytes).decode()}"
    return HTMLResponse(content=build_form(result, img_data_url))


@app.post("/api/submit", response_class=HTMLResponse)
async def submit(request: Request):
    form_data = await request.form()

    # Upload image sur Cloudinary
    image_url = ""
    image_data = form_data.get("image_data", "")
    if image_data and image_data.startswith("data:"):
        try:
            header, encoded = image_data.split(",", 1)
            media_type = header.split(":")[1].split(";")[0]
            image_bytes = base64.b64decode(encoded)
            image_url = upload_to_cloudinary(image_bytes, media_type)
        except Exception as e:
            print(f"[WARN] Upload Cloudinary échoué : {e}")
            # On continue sans URL — la ligne sera quand même insérée

    final_data = {
        "recorded_at":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "type_document": form_data.get("type_document", "autre"),
        "fournisseur":   form_data.get("fournisseur", "").strip(),
        "date":          form_data.get("date", ""),
        "montant_ttc":   form_data.get("montant_ttc", ""),
        "tva":           form_data.get("tva", ""),
        "devise":        form_data.get("devise", "EUR"),
        "description":   form_data.get("description", ""),
        "confiance":     form_data.get("confiance", "basse"),
    }

    try:
        get_sheets().append_expense(final_data, image_url=image_url)
    except Exception as e:
        return HTMLResponse(
            content=f'<div class="error">Erreur Google Sheets : {escape(str(e))}</div>',
            status_code=500
        )

    return HTMLResponse(content="""
        <div style="color:#28a745; font-weight:bold; padding:16px; border:2px solid #28a745; border-radius:8px;">
            ✅ Dépense enregistrée avec succès dans le Google Sheet !
        </div>
    """)
