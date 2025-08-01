import re
import json
import google.generativeai as genai
genai.configure(api_key="AIzaSyC8tjgTPhlkT8ujyK1JwG90dyLZ7F4VFRc")

class AgentGemini:
    def __init__(self, model='gemini-1.5-flash'):
        self.model = genai.GenerativeModel(model)
        self.chat = self.model.start_chat(history=[])
        self.labels = [
            "Facture", "Contrat", "Document bancaire", "Rapport", 
            "Lettre", "Article", "Devis", "Commande", "CV", "Autre"
        ]

    def generate_summary(self, text):
        """Génère un résumé du texte"""
        response = self.chat.send_message(
            f"Résumez ce texte en 100 mots maximum en français :\n\n{text}"
        )
        return response.text.strip() if response else "Aucun résumé généré."

    def extract_information(self, text):
        """Extrait l`es informations importantes du texte"""
        prompt = f"""Extrayez les informations suivantes du texte:
        - Noms de personnes (PER)
        - Organisations (ORG)
        - Dates (DATE au format dd/mm/yyyy)
        - Type de document (choisir parmi: {self.labels})
        - Un résumé simple
        
        Réponse en JSON valide avec les clés: 'PER', 'ORG', 'DATE', 'type', 'summary'
        Exemple :
        {{
            "PER": ["Jean Dupont"],
            "ORG": ["OpenAI"],
            "DATE": ["25/07/2025"],
            "type": "Facture",
            "summary": "Résumé du document ici."
        }}

        Texte : {text}"""

        try:
            response = self.chat.send_message(prompt)
            text_response = response.text.strip()

            # Try to extract JSON safely
            json_text = re.search(r'\{.*\}', text_response, re.DOTALL)
            if not json_text:
                raise ValueError("Réponse JSON introuvable dans :\n" + text_response)
            
            clean_json = json.loads(json_text.group())
            return clean_json
        except Exception as e:
            return {
                "PER": [],
                "ORG": [],
                "DATE": [],
                "type": "Autre",
                "summary": "Aucune information extraite.",
                "error": str(e)
            }

        