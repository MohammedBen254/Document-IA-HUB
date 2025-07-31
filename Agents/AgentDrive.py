from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import os.path

class GoogleDriveManager:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)
        
    def _authenticate(self):
        """Gère l'authentification OAuth avec Google"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
    
    def upload_file(self, file_path, file_name, folder_id=None):
        """Upload un fichier vers Google Drive"""
        file_metadata = {
            'name': file_name,
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()
        
        return file.get('id'), file.get('webViewLink')
    
    def create_folder(self, folder_name, parent_id=None):
        """Crée un dossier dans Google Drive"""
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    def get_or_create_folder(self, folder_name):
        """Récupère ou crée un dossier"""
        folders = self.service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute().get('files', [])
        
        if folders:
            return folders[0]['id']
        else:
            return self.create_folder(folder_name)