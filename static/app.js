/**
 * Application Gestionnaire de Notes de Frais
 * Gestion du dépôt d'images et intégration HTMX
 */

const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('image-input');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const previewInfo = document.getElementById('previewInfo');
const analysisResult = document.getElementById('analysis-result');

// Configuration
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];

/**
 * Initialise les événements pour la zone de dépôt
 */
function initDropZone() {
    dropZone.addEventListener('click', () => imageInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    imageInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

/**
 * Traite les fichiers sélectionnés
 */
function handleFiles(files) {
    if (files.length === 0) return;

    const file = files[0];

    // Validation
    if (!validateFile(file)) {
        showErrorMessage('Fichier invalide. Utilisez une image JPEG ou PNG (max 5 MB).');
        return;
    }

    // Afficher la prévisualisation
    showPreview(file);

    // Envoyer pour analyse
    sendForAnalysis(file);
}

/**
 * Valide le fichier
 */
function validateFile(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
        return false;
    }
    if (file.size > MAX_FILE_SIZE) {
        return false;
    }
    return true;
}

/**
 * Affiche la prévisualisation de l'image
 */
function showPreview(file) {
    const reader = new FileReader();

    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewInfo.textContent = `📁 ${file.name} • ${(file.size / 1024).toFixed(2)} KB`;
        previewContainer.classList.add('active');
    };

    reader.readAsDataURL(file);
}

/**
 * Envoie le fichier pour analyse
 */
function sendForAnalysis(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Afficher le spinner
    analysisResult.innerHTML = `
        <div class="loading">
            <span class="spinner"></span>
            <span>Analyse en cours...</span>
        </div>
    `;

    // Fetch API avec HTMX
    fetch('/api/analyze', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(text || 'Erreur lors de l\'analyse');
                });
            }
            return response.text();
        })
        .then(html => {
            analysisResult.innerHTML = html;
        })
        .catch(error => {
            console.error('Erreur:', error);
            analysisResult.innerHTML = `
            <div class="result-error">
                ⚠️ Erreur : ${error.message || 'Impossible d\'analyser le ticket'}
            </div>
        `;
        });
}

/**
 * Affiche un message d'erreur
 */
function showErrorMessage(message) {
    analysisResult.innerHTML = `
        <div class="result-error">
            ⚠️ ${message}
        </div>
    `;
}

/**
 * Initialise l'application au chargement du DOM
 */
document.addEventListener('DOMContentLoaded', () => {
    initDropZone();
});

/**
 * Permet à HTMX de mettre à jour la page sans rechargement
 */
document.addEventListener('htmx:load', () => {
    // Optionnel : déclencher des actions après chaque update HTMX
});
