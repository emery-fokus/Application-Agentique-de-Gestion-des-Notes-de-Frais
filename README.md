# Gestionnaire de Notes de Frais — Agentique

Petit projet FastAPI + Groq + Google Sheets pour extraire et enregistrer des notes de frais.

## But
- Uploader une photo de reçu
- Extraire automatiquement les champs (AI)
- Permettre la correction manuelle par l'utilisateur
- Enregistrer la dépense dans Google Sheets et l'image dans Google Drive

## Structure
- `app.py` — serveur FastAPI (routes `/`, `/api/analyze`, `/api/submit`)
- `backend.py` — `ExpenseAgent` : logique d'appel au modèle Groq et extraction
- `sheet.py` — `GoogleSheetsClient` : upload sur Drive et append dans Sheets
- `static/` — frontend : `index.html`, `app.js`, `style.css`
- `.env` — variables d'environnement (API keys, IDs, chemins)

## Installation
1. Cloner le dépôt
2. Créer un environnement virtuel Python 3.11+ et l'activer

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirement.txt
```

3. Configurer le fichier `.env` (voir ci-dessous)
4. Lancer le serveur :

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Puis ouvrir `http://127.0.0.1:8000`.

## .env requis
Exemple minimal :

```
GROQ_API_KEY="<votre_groq_key>"
GOOGLE_SHEET_ID="<sheet_id_pur>"
GOOGLE_SERVICE_ACCOUNT_JSON="credential.json"
GOOGLE_DRIVE_FOLDER_ID="<optional_drive_folder_id>"
```

- `GOOGLE_SHEET_ID` doit être l'ID pur (la chaîne entre `/d/` et `/edit`) — pas l'URL complète.
- `GOOGLE_SERVICE_ACCOUNT_JSON` doit pointer vers le fichier de compte de service JSON placé dans le projet.
- Partagez votre Google Sheet avec l'adresse `client_email` présente dans `credential.json` (édition).

## Google Cloud (compte de service)
1. Créez un projet Google Cloud.
2. Activez les APIs: Google Sheets API, Google Drive API.
3. Créez un compte de service, générez une clé JSON et téléchargez-la (placer dans le repo, ex: `credential.json`).
4. Partagez la feuille Google Sheets avec le `client_email` du compte de service (édition).

## Flux d'exécution
1. L'utilisateur droppe une image → `POST /api/analyze` → `ExpenseAgent.extract_from_bytes()` → rendu d'un formulaire HTML.
2. L'utilisateur corrige/valide le formulaire (select, nombres décimaux autorisés, champs vides acceptés).
3. Clic `Valider` → `POST /api/submit` :
	 - Si image présente → upload sur Drive
	 - `append_expense()` est appelé avec les valeurs (y compris `recorded_at` timestamp)
	 - Ligne ajoutée dans la feuille

Important : la ligne n'est écrite que lors du clic sur `Valider`.

## Tests de bout en bout recommandés
- Ticket lisible (restaurant) → tous les champs remplis, confiance haute
- Billet SNCF → `fournisseur=SNCF`, type=Transport
- Photo floue → certains champs nuls, confiance basse
- Fichier non supporté (PDF) → message d'erreur
- Champ incorrect → correction manuelle → vérifier que Google Sheet contient la valeur modifiée
- Soumission sans image → la ligne doit s'ajouter avec une image vide (pas d'erreur)

## Exemple JSON renvoyé par le modèle (structure attendue)

```json
{
	"fournisseur": "Le Bistrot",
	"date": "2026-06-10",
	"montant_ttc": 45.50,
	"tva": 7.60,
	"devise": "EUR",
	"type": "Restaurant",
	"description": "Déjeuner client",
	"confidence": 0.92
}
```

## Débogage / Logs
- Les erreurs HTMX sont renvoyées en HTML (pour affichage côté client).
- Voir la console du serveur (où `uvicorn` tourne) pour traces d'erreur complètes.

## Aide / contributions
Pour ajouter des tests automatisés, intégrer CI, ou améliorer l'UX, ouvre une issue ou propose une PR.

---

Fait par l'agent — si tu veux, j'ajoute un script de test qui exécute `append_expense()` automatiquement.