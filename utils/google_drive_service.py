"""
import os
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

class GoogleDriveService:
    def __init__(self):
        self._SCOPES=['https://www.googleapis.com/auth/drive']

        _credential_path=os.path.join('service_account.json')
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _credential_path

    def build_service(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), self._SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service"""