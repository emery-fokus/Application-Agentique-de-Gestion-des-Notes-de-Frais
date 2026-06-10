import os
import json
import base64
from dotenv import load_dotenv
from groq import Groq


class ExpenseAgent:
    def __init__(self):
        load_dotenv()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "prompt.txt"), "r", encoding="utf-8") as f:
            self.prompt = f.read()
        with open(os.path.join(current_dir, "context.txt"), "r", encoding="utf-8") as f:
            self.context = f.read()

    def extract_from_bytes(self, image_bytes: bytes, media_type: str) -> dict:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{media_type};base64,{image_base64}"

        full_system_prompt = f"{self.context}\n\n{self.prompt}"

        response = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyse cette note de frais et extrait les informations demandées."},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ]
        )

        raw_json_text = response.choices[0].message.content
        try:
            extracted = json.loads(raw_json_text)
        except json.JSONDecodeError:
            extracted = {}

        return {
            "type_document":  extracted.get("type_document", "autre"),
            "fournisseur":    extracted.get("fournisseur", ""),
            "date":           extracted.get("date", ""),
            "montant_ttc":    extracted.get("montant_ttc", ""),
            "tva":            extracted.get("tva", None),
            "devise":         extracted.get("devise", "EUR"),
            "description":    extracted.get("description", ""),
            "confiance":      extracted.get("confiance", "basse"),
        }


if __name__ == "__main__":
    agent = ExpenseAgent()
    image_path = "test_ticket.jpg"
    if not os.path.exists(image_path):
        print(f"Dépose un fichier '{image_path}' ici pour tester.")
    else:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        result = agent.extract_from_bytes(image_bytes, "image/jpeg")
        print(json.dumps(result, indent=2, ensure_ascii=False))