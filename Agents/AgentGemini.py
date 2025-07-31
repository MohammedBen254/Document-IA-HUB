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
        """Extrait les informations importantes du texte"""
        prompt = f"""Extrayez les informations suivantes du texte:
        - Noms de personnes (PER)
        - Organisations (ORG)
        - Dates (DATE au format dd/mm/yyyy)
        - Type de document (choisir parmi: {self.labels})
        - Un résumé simple
        
        Réponse en JSON avec les clés: 'PER', 'ORG', 'DATE', 'type', 'summary'
        Texte: {text}"""
        
        response = self.chat.send_message(prompt)
        clean = re.sub(r'```json\n(.*?)\n```', r'\1', response.text, flags=re.DOTALL).strip()
        return json.loads(clean) if clean else {"error": "Aucune information extraite."}
    