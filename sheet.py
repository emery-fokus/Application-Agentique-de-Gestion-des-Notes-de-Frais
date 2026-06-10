import io
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


class GoogleSheetsClient:
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/spreadsheets',
    ]

    def __init__(self, sheet_id: Optional[str] = None, service_account_json: Optional[str] = None, drive_folder_id: Optional[str] = None):
        load_dotenv()
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')
        self.service_account_json = service_account_json or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        self.drive_folder_id = drive_folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')

        if not self.sheet_id:
            raise ValueError('GOOGLE_SHEET_ID manquant.')
        if not self.service_account_json:
            raise ValueError('GOOGLE_SERVICE_ACCOUNT_JSON manquant.')

        self.service_account_json = self._resolve_json_path(self.service_account_json)
        credentials = service_account.Credentials.from_service_account_file(self.service_account_json, scopes=self.SCOPES)

        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)

    def _resolve_json_path(self, path: str) -> str:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            raise FileNotFoundError(f'Fichier de compte de service introuvable : {p}')
        return str(p)

    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=self._guess_mimetype(filename), resumable=False)
        metadata = {'name': filename}
        if self.drive_folder_id:
            metadata['parents'] = [self.drive_folder_id]

        created = self.drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink, webContentLink').execute()
        file_id = created.get('id')
        if not file_id:
            raise RuntimeError('Échec de l.upload du fichier sur Google Drive.')

        try:
            self.drive_service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
        except Exception:
            pass

        return created.get('webViewLink') or created.get('webContentLink') or f'https://drive.google.com/file/d/{file_id}/view'

    def append_expense(self, expense_data: dict, image_url: str) -> None:
        row = [
            expense_data.get('date', ''),
            expense_data.get('fournisseur', ''),
            expense_data.get('type', ''),
            expense_data.get('description', ''),
            expense_data.get('montant_ttc', ''),
            expense_data.get('tva', ''),
            expense_data.get('devise', ''),
            image_url,
            expense_data.get('confidence', ''),
            expense_data.get('recorded_at', ''),
        ]

        body = {'values': [row]}
        self.sheets_service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range='Sheet1!A1',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body,
        ).execute()

    @staticmethod
    def _guess_mimetype(filename: str) -> str:
        if filename.lower().endswith('.png'):
            return 'image/png'
        return 'image/jpeg'
