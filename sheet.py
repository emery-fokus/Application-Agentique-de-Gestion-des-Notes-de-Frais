# import os
# from typing import Optional, Dict, Any
# from pathlib import Path
# from dotenv import load_dotenv
# from google.oauth2 import service_account
# from googleapiclient.discovery import build

# class GoogleSheetsClient:
#     SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

#     def __init__(self, sheet_id: Optional[str] = None, service_account_json: Optional[str] = None):
#         load_dotenv()
#         self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')
#         self.service_account_json = service_account_json or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

#         if not self.sheet_id:
#             raise ValueError('GOOGLE_SHEET_ID manquant.')
#         if not self.service_account_json:
#             raise ValueError('GOOGLE_SERVICE_ACCOUNT_JSON manquant.')

#         self.service_account_json = self._resolve_json_path(self.service_account_json)
#         credentials = service_account.Credentials.from_service_account_file(self.service_account_json, scopes=self.SCOPES)

#         self.sheets_service = build('sheets', 'v4', credentials=credentials)
#         self.sheet_name = self._get_default_sheet_name()

#     def _resolve_json_path(self, path: str) -> str:
#         p = Path(path)
#         if not p.is_absolute():
#             p = Path.cwd() / p
#         if not p.exists():
#             candidates = list(Path.cwd().glob('*credential*.json'))
#             if candidates: return str(candidates[0])
#             raise FileNotFoundError(f'Fichier de compte de service introuvable : {p}')
#         return str(p)

#     def _get_default_sheet_name(self) -> str:
#         spreadsheet = self.sheets_service.spreadsheets().get(
#             spreadsheetId=self.sheet_id, fields='sheets.properties.title'
#         ).execute()
#         sheets = spreadsheet.get('sheets', [])
#         for s in sheets:
#             title = s.get('properties', {}).get('title', '')
#             if title.strip().lower() == 'notes de frais':
#                 return title.replace("'", "''")
#         return sheets[0]['properties']['title'].replace("'", "''")

#     # --- CETTE MÉTHODE DOIT ÊTRE DANS LA CLASSE (INDENTÉE) ---
# # ... (le début de ta classe reste inchangé) ...

#     def append_expense(self, data: Dict[str, Any], image_url: Optional[str] = None) -> None:
#         """Ajoute la ligne dans Google Sheets en respectant l'ordre A à J."""
#         row = [
#             data.get('recorded_at', ''),      # A - Horodatage
#             data.get('type_document', ''),    # B - Type
#             data.get('fournisseur', ''),      # C - Fournisseur
#             data.get('date', ''),             # D - Date
#             data.get('montant_ttc', ''),      # E - Montant TTC
#             data.get('tva', ''),              # F - TVA
#             data.get('devise', 'EUR'),        # G - Devise
#             data.get('description', ''),      # H - Description
#             data.get('confiance', 'moyenne'), # I - Confiance
#             image_url if image_url and image_url.startswith("http") else '' # J - Image
#         ]
        
#         body = {'values': [row]}
        
#         try:
#             self.sheets_service.spreadsheets().values().append(
#                 spreadsheetId=self.sheet_id,
#                 range=f"'{self.sheet_name}'!A1",
#                 valueInputOption='USER_ENTERED',
#                 insertDataOption='INSERT_ROWS',
#                 body=body,
#             ).execute()
#         except Exception as e:
#             raise RuntimeError(f"Échec de l'insertion Google Sheets : {str(e)}")


import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io


class GoogleSheetsClient:
    # FIX 3 : scope Drive ajouté pour pouvoir uploader les images
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, sheet_id: Optional[str] = None, service_account_json: Optional[str] = None):
        load_dotenv()
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
        sa_path = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID manquant.")
        if not sa_path:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON manquant.")

        sa_path = self._resolve_json_path(sa_path)
        credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=self.SCOPES)

        self.sheets_service = build("sheets", "v4", credentials=credentials)
        self.drive_service  = build("drive",  "v3", credentials=credentials)
        self.sheet_name     = self._get_default_sheet_name()

    # ------------------------------------------------------------------ helpers

    def _resolve_json_path(self, path: str) -> str:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            candidates = list(Path.cwd().glob("*credential*.json"))
            if candidates:
                return str(candidates[0])
            raise FileNotFoundError(f"Fichier de compte de service introuvable : {p}")
        return str(p)

    def _get_default_sheet_name(self) -> str:
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.sheet_id, fields="sheets.properties.title"
        ).execute()
        sheets = spreadsheet.get("sheets", [])
        for s in sheets:
            title = s.get("properties", {}).get("title", "")
            if title.strip().lower() == "notes de frais":
                return title.replace("'", "''")
        return sheets[0]["properties"]["title"].replace("'", "''")

    # ------------------------------------------------------------------ public API

    # def upload_image_to_drive(self, image_bytes: bytes, media_type: str, filename: str = "note_de_frais.jpg") -> str:
    #     """Upload une image sur Drive et retourne son URL publique."""
    #     file_metadata = {"name": filename, "parents": []}
    #     media = build(
    #         "drive", "v3",
    #         credentials=self.drive_service._http.credentials
    #     )  # on réutilise les credentials déjà chargés

    #     # Utilisation directe de l'API via googleapiclient
    #     from googleapiclient.http import MediaIoBaseUpload
    #     fh = io.BytesIO(image_bytes)
    #     media_upload = MediaIoBaseUpload(fh, mimetype=media_type, resumable=False)

    #     file = self.drive_service.files().create(
    #         body={"name": filename},
    #         media_body=media_upload,
    #         fields="id"
    #     ).execute()

    #     file_id = file.get("id")

    #     # Rendre le fichier public en lecture
    #     self.drive_service.permissions().create(
    #         fileId=file_id,
    #         body={"type": "anyone", "role": "reader"}
    #     ).execute()

    #     return f"https://drive.google.com/uc?id={file_id}"

    def append_expense(self, data: Dict[str, Any], image_url: Optional[str] = None) -> None:
        """Ajoute une ligne dans Google Sheets (colonnes A à J)."""
        row = [
            data.get("recorded_at", ""),       # A - Horodatage
            data.get("type_document", ""),     # B - Type
            data.get("fournisseur", ""),       # C - Fournisseur
            data.get("date", ""),              # D - Date
            data.get("montant_ttc", ""),       # E - Montant TTC
            data.get("tva", ""),               # F - TVA
            data.get("devise", "EUR"),         # G - Devise
            data.get("description", ""),       # H - Description
            data.get("confiance", "basse"),    # I - Confiance
            image_url if image_url and image_url.startswith("http") else "",  # J - Image
        ]

        try:
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"'{self.sheet_name}'!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()
        except Exception as e:
            raise RuntimeError(f"Échec de l'insertion Google Sheets : {e}")