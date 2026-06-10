// // app.js
// const dropZone = document.getElementById('dropZone');
// const imageInput = document.getElementById('image-input');
// const previewContainer = document.getElementById('previewContainer');
// const previewImage = document.getElementById('previewImage');

// function initDropZone() {
//     dropZone.addEventListener('click', () => imageInput.click());

//     ['dragover', 'dragleave'].forEach(evt => {
//         dropZone.addEventListener(evt, (e) => {
//             e.preventDefault();
//             dropZone.classList.toggle('dragover', evt === 'dragover');
//         });
//     });

//     dropZone.addEventListener('drop', (e) => {
//         e.preventDefault();
//         handleFiles(e.dataTransfer.files);
//     });

//     imageInput.addEventListener('change', (e) => handleFiles(e.target.files));
// }

// function handleFiles(files) {
//     if (files.length === 0) return;
//     const file = files[0];

//     const reader = new FileReader();
//     reader.onload = (e) => {
//         previewImage.src = e.target.result;
//         previewContainer.classList.add('active');

//         // --- LA CORRECTION EST ICI ---
//         // On déclenche manuellement la soumission du formulaire HTMX
//         // après que l'image soit prête.
//         htmx.trigger('#upload-form', 'submit');
//     };
//     reader.readAsDataURL(file);
// }

// document.addEventListener('DOMContentLoaded', initDropZone);




// app.js

document.addEventListener('DOMContentLoaded', () => {

    const fileInput = document.getElementById('image-input');
    const dropZone = document.getElementById('dropZone');
    const previewImage = document.getElementById('previewImage');
    const previewContainer = document.getElementById('previewContainer');
    const uploadForm = document.getElementById('upload-form');

    // --- Clic sur la dropzone → ouvre le sélecteur de fichier ---
    dropZone.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    // --- Drag & drop ---
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
        const file = e.dataTransfer.files[0];
        if (file) {
            // Injecte le fichier dans l'input pour que HTMX puisse l'envoyer
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            handleFile(file);
        }
    });

    // --- Sélection via input file ---
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });

    function handleFile(file) {
        // Prévisualisation
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImage.src = event.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Déclenche la soumission HTMX
        // Petit délai pour laisser le temps à l'input d'être mis à jour
        setTimeout(() => {
            htmx.trigger(uploadForm, 'submit');
        }, 50);
    }

    // --- Feedback pendant l'analyse ---
    document.body.addEventListener('htmx:beforeRequest', (event) => {
        if (event.target.id === 'upload-form') {
            document.getElementById('analysis-result').innerHTML =
                '<em style="opacity:0.7">⏳ Analyse en cours par l\'IA...</em>';
        }
    });

    // --- Erreurs 4xx/5xx (HTMX ne swape pas par défaut) ---
    document.body.addEventListener('htmx:responseError', (event) => {
        const target = event.detail.target;
        if (target) {
            target.innerHTML = `
                <div style="color:#fff; background:#dc3545; padding:14px; border-radius:6px; margin-top:10px;">
                    <strong>Erreur :</strong> ${event.detail.xhr.responseText || 'Impossible de traiter cette image.'}
                </div>`;
        }
    });

    // --- Réinitialisation après confirmation réussie ---
    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.target.id === 'confirmation-container') {
            setTimeout(() => {
                document.getElementById('analysis-result').innerHTML = '';
                document.getElementById('confirmation-container').innerHTML = '';
                previewContainer.style.display = 'none';
                previewImage.src = '';
                fileInput.value = '';
            }, 3000);
        }
    });

});
