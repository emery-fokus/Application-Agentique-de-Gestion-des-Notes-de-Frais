# 💰 Application Agentique de Gestion des Notes de Frais

Application web permettant d'analyser automatiquement des photos de notes de frais grâce à l'IA, de corriger les informations extraites, puis de les enregistrer dans un Google Sheet partagé avec la comptabilité.

---

## 🎯 Contexte

Un salarié prend en photo un ticket (restaurant, transport, hôtel...). L'application extrait automatiquement les informations clés, les affiche dans un formulaire éditable, et les synchronise dans un Google Sheet. L'image est archivée sur Cloudinary.

---

## 🏗️ Architecture du projet

```
expense-tracker/
├── app.py               # Serveur FastAPI — routes et orchestration
├── backend.py           # Classe ExpenseAgent — extraction IA via Groq
├── sheet.py             # Classe GoogleSheetsClient — intégration Google Sheets
├── context.txt          # Prompt système du modèle
├── prompt.txt           # Prompt utilisateur envoyé avec l'image
├── requirement.txt      # Dépendances Python
├── credentials.json     # Clé de compte de service Google (non commité)
├── .env                 # Variables d'environnement (non commité)
├── .env.example         # Modèle de configuration
├── README.md
├── tests/
│   ├── e2e_test.py      # Tests bout en bout
│   ├── test_sheet.py    # Test Google Sheets isolé
│   └── test_ticket.jpg  # Image de test
└── static/
    ├── index.html       # Interface HTMX
    ├── style.css        # Feuille de style
    └── app.js           # JS Vanilla
```

---

## ⚙️ Stack technique

| Composant | Technologie |
|---|---|
| Modèle IA | `meta-llama/llama-4-scout-17b-16e-instruct` via Groq |
| Backend | Python · FastAPI |
| Frontend | HTML · HTMX · CSS · JS Vanilla |
| Intégration Sheets | Google Sheets API via `google-api-python-client` |
| Stockage images | Cloudinary |

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-user/expense-tracker.git
cd expense-tracker
```

### 2. Créer l'environnement virtuel

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

### 3. Installer les dépendances

```bash
pip install -r requirement.txt
```

### 4. Configurer les variables d'environnement

Copiez `.env.example` en `.env` et remplissez les valeurs :

```bash
cp .env.example .env
```

```dotenv
GROQ_API_KEY=votre_cle_groq
GOOGLE_SHEET_ID=identifiant_du_google_sheet
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 5. Lancer le serveur

```bash
uvicorn app:app --reload
```

Ouvrez ensuite [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ☁️ Configuration Google Cloud

### Créer le projet et activer les API

1. Rendez-vous sur [console.cloud.google.com](https://console.cloud.google.com)
2. Créez un projet (ex : `expense-tracker-tp`)
3. Activez **Google Sheets API** et **Google Drive API**

### Créer le compte de service

1. Dans **API et services > Identifiants**, créez un compte de service
2. Donnez-lui le rôle **Éditeur**
3. Téléchargez la clé JSON → renommez-la `credentials.json` à la racine du projet
4. Ajoutez `credentials.json` à votre `.gitignore`

### Préparer le Google Sheet

1. Créez un Google Sheet et renommez la feuille en `Notes de frais`
2. Créez ces en-têtes sur la première ligne (colonnes A à J) :
   `Horodatage`, `Type`, `Fournisseur`, `Date`, `Montant TTC (€)`, `TVA (€)`, `Devise`, `Description`, `Confiance`, `Image`
3. Partagez le Sheet avec l'email du compte de service (rôle **Éditeur**)
4. Copiez l'ID du Sheet depuis l'URL et collez-le dans `.env`

---

## 🧠 Exemple de JSON retourné par le modèle

```json
{
  "type_document": "restaurant",
  "fournisseur": "Bistrot Paul",
  "date": "10/06/2026",
  "montant_ttc": 24.50,
  "tva": 4.08,
  "devise": "EUR",
  "description": "Déjeuner client",
  "confiance": "haute"
}
```

---

## 🔄 Fonctionnement

1. L'utilisateur dépose ou photographie une note de frais
2. L'image est envoyée à `/api/analyze` → le modèle Llama extrait les 8 champs
3. Un formulaire pré-rempli et éditable apparaît
4. L'utilisateur corrige si besoin et clique **Envoyer**
5. `/api/submit` uploade l'image sur Cloudinary et insère la ligne dans le Google Sheet

---

## 🔒 Sécurité

Ne commitez jamais :
- `credentials.json`
- `.env`

Ces fichiers sont déjà dans le `.gitignore`.