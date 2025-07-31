import os

class Config:
    # Configuration Google Drive
    DRIVE_CREDENTIALS = 'credentials.json'
    DRIVE_TOKEN = 'token.pickle'
    
    # Configuration Flask
    SECRET_KEY = "12345678"
    UPLOAD_FOLDER = 'uploads'
    CLASS_FOLDERS = 'class_folders'
    DATABASE = 'documents.db'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    @classmethod
    def init_app(cls, app):
        # Créer les répertoires nécessaires
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.CLASS_FOLDERS, exist_ok=True)
        
        # Configurer Flask
        app.secret_key = cls.SECRET_KEY
        app.config['UPLOAD_FOLDER'] = cls.UPLOAD_FOLDER
        app.config['CLASS_FOLDERS'] = cls.CLASS_FOLDERS
        app.config['DATABASE'] = cls.DATABASE
        app.config['ALLOWED_EXTENSIONS'] = cls.ALLOWED_EXTENSIONS