import json
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .config import settings
from .crypto import CryptoManager


class GoogleSheetsService:
    """Service for interacting with Google Sheets API"""
    
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
    
    def get_auth_url(self, state: str = None) -> str:
        """Get Google OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = settings.google_redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        return auth_url
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = settings.google_redirect_uri
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
    
    def get_service(self, credentials_dict: Dict[str, Any]):
        """Get Google Sheets service with credentials"""
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        return build('sheets', 'v4', credentials=credentials)
    
    def create_spreadsheet(self, service, title: str) -> str:
        """Create a new Google Spreadsheet"""
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        try:
            result = service.spreadsheets().create(body=spreadsheet).execute()
            return result.get('spreadsheetId')
        except HttpError as error:
            raise Exception(f"Failed to create spreadsheet: {error}")
    
    def get_spreadsheet_data(self, service, spreadsheet_id: str, range_name: str = 'A1:Z1000') -> List[List[str]]:
        """Get data from Google Spreadsheet"""
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        except HttpError as error:
            raise Exception(f"Failed to get spreadsheet data: {error}")
    
    def update_spreadsheet_data(self, service, spreadsheet_id: str, range_name: str, values: List[List[str]]) -> bool:
        """Update data in Google Spreadsheet"""
        try:
            body = {
                'values': values
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return result.get('updatedCells', 0) > 0
        except HttpError as error:
            raise Exception(f"Failed to update spreadsheet data: {error}")
    
    def encrypt_sheet_values(self, values: List[List[str]], sheet_key: str) -> List[List[str]]:
        """Encrypt all values in the sheet data"""
        encrypted_values = []
        
        for row in values:
            encrypted_row = []
            for cell in row:
                if cell and cell.strip():  # Only encrypt non-empty cells
                    encrypted_cell = CryptoManager.encrypt_cell_value(cell, sheet_key)
                    encrypted_row.append(encrypted_cell)
                else:
                    encrypted_row.append(cell)
            encrypted_values.append(encrypted_row)
        
        return encrypted_values
    
    def decrypt_sheet_values(self, encrypted_values: List[List[str]], sheet_key: str) -> List[List[str]]:
        """Decrypt all values in the sheet data"""
        decrypted_values = []
        
        for row in encrypted_values:
            decrypted_row = []
            for cell in row:
                if cell and cell.strip():  # Only decrypt non-empty cells
                    try:
                        decrypted_cell = CryptoManager.decrypt_cell_value(cell, sheet_key)
                        decrypted_row.append(decrypted_cell)
                    except:
                        # If decryption fails, assume it's already plaintext
                        decrypted_row.append(cell)
                else:
                    decrypted_row.append(cell)
            decrypted_values.append(decrypted_row)
        
        return decrypted_values
    
    def get_spreadsheet_metadata(self, service, spreadsheet_id: str) -> Dict[str, Any]:
        """Get spreadsheet metadata"""
        try:
            result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return {
                'title': result['properties']['title'],
                'sheets': [
                    {
                        'title': sheet['properties']['title'],
                        'sheetId': sheet['properties']['sheetId'],
                        'gridProperties': sheet['properties'].get('gridProperties', {})
                    }
                    for sheet in result.get('sheets', [])
                ]
            }
        except HttpError as error:
            raise Exception(f"Failed to get spreadsheet metadata: {error}")
    
    def share_spreadsheet(self, service, spreadsheet_id: str, email: str, role: str = 'reader') -> bool:
        """Share spreadsheet with user"""
        try:
            # Build Drive service for sharing
            drive_service = build('drive', 'v3', credentials=service._http.credentials)
            
            permission = {
                'type': 'user',
                'role': role,  # reader, writer, owner
                'emailAddress': email
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            return True
        except HttpError as error:
            raise Exception(f"Failed to share spreadsheet: {error}")


# Global instance
google_sheets_service = GoogleSheetsService()
