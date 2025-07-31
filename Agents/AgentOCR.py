import fitz  # PyMuPDF
from transformers import pipeline
import easyocr

class AgentOCR:
    def __init__(self, language='fr'):
        self.reader = easyocr.Reader([language])
        self.classifier = pipeline("zero-shot-classification", 
                                 model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        self.labels = [
            "Facture", "Contrat", "Document bancaire", "Rapport", 
            "Lettre", "Devis", "Commande", "CV", "Autre"
        ]

    def extract_text_from_pdf(self, pdf_file):
        """Extrait le texte d'un fichier PDF"""
        doc = fitz.open(pdf_file)
        extracted_text = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            extracted_text.append(text)
        return ' '.join(extracted_text)
    
    def classify_document(self, text):
        """Classifie le document selon les catégories prédéfinies"""
        result = self.classifier(text, candidate_labels=self.labels)
        return result['labels'][result['scores'].index(max(result['scores']))]