import os
import json
import base64

from dotenv import load_dotenv
from groq import Groq


class ExpenseAgent:

    def __init__(self):
        load_dotenv()

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))

        prompt_path = os.path.join(current_dir, "prompt.txt")
        context_path = os.path.join(current_dir, "context.txt")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt = f.read()

        with open(context_path, "r", encoding="utf-8") as f:
            self.context = f.read() 

    
    def extract_from_bytes(self, image_bytes: bytes, media_type: str) -> dict:
    
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{media_type};base64,{image_base64}"
        
        
        full_system_prompt = f"{self.prompt}\n\nContexte supplémentaire :\n{self.context}"

        
        response = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            response_format={"type": "json_object"},  # Force le retour en JSON
            messages=[
                {
                    "role": "system",
                    "content": full_system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyse cette note de frais et extrait les informations demandées."},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url}
                        }
                    ]
                }
            ]
        )
        
        # Étape 4 : On récupère la réponse textuelle de l'IA
        raw_json_text = response.choices[0].message.content
        
        # Étape 5 : On transforme ce texte en dictionnaire Python (Parsing)
        try:
            extracted_data = json.loads(raw_json_text)
        except json.JSONDecodeError:
            extracted_data = {}
            
        expected_fields = ["date", "type_document", "description", "fournisseur", "montant_ttc", "tva", "devise", "confidence"]
        validated_data = {}
        
        for field in expected_fields:
            # Si le champ n'existe pas ou est null, on lui donne la valeur None sans planter
            validated_data[field] = extracted_data.get(field, None)
            
        return validated_data

if __name__ == "__main__":

    agent = ExpenseAgent()

    # Assure-toi d'avoir une image nommée "test_ticket.jpg" dans ton dossier !
    image_path = "test_ticket.jpg"

    if not os.path.exists(image_path):
        print(f"Erreur : Crée ou dépose un fichier image nommé '{image_path}' ici pour tester.")
    else:
        print("Lecture du ticket et envoi à Groq...")
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        result = agent.extract_from_bytes(
            image_bytes=image_bytes,
            media_type="image/jpeg"
        )

        print("\n--- RÉSULTAT DU TICKET ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))