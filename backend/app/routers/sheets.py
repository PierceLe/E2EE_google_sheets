from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Sheet, EncryptionKey
from ..schemas import (
    SheetCreate, Sheet as SheetSchema, SheetUpdate,
    ShareSheetRequest, SheetDataRequest, SheetDataResponse,
    EncryptionKeyCreate
)
from ..auth import get_current_active_user
from ..crypto import CryptoManager
from ..google_sheets import google_sheets_service

router = APIRouter(prefix="/sheets", tags=["sheets"])


@router.post("/", response_model=SheetSchema)
async def create_sheet(
    sheet: SheetCreate,
    google_credentials: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new E2EE sheet"""
    try:
        # Create Google Sheet
        service = google_sheets_service.get_service(google_credentials)
        google_sheet_id = google_sheets_service.create_spreadsheet(service, sheet.name)
        
        # Generate encryption key for this sheet
        sheet_key = CryptoManager.generate_sheet_key()
        
        # Create sheet record
        db_sheet = Sheet(
            name=sheet.name,
            google_sheet_id=google_sheet_id,
            owner_id=current_user.id,
            encrypted_title=sheet.encrypted_title
        )
        
        db.add(db_sheet)
        db.commit()
        db.refresh(db_sheet)
        
        # Create encryption key for owner
        encrypted_key = CryptoManager.encrypt_with_public_key(sheet_key, current_user.public_key)
        
        db_encryption_key = EncryptionKey(
            sheet_id=db_sheet.id,
            user_id=current_user.id,
            encrypted_key=encrypted_key
        )
        
        db.add(db_encryption_key)
        db.commit()
        
        return db_sheet
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create sheet: {str(e)}"
        )


@router.get("/", response_model=List[SheetSchema])
async def get_user_sheets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all sheets accessible to current user"""
    # Get owned sheets
    owned_sheets = db.query(Sheet).filter(
        Sheet.owner_id == current_user.id,
        Sheet.is_active == True
    ).all()
    
    # Get shared sheets
    shared_sheets = db.query(Sheet).join(
        EncryptionKey, Sheet.id == EncryptionKey.sheet_id
    ).filter(
        EncryptionKey.user_id == current_user.id,
        Sheet.owner_id != current_user.id,
        Sheet.is_active == True
    ).all()
    
    return owned_sheets + shared_sheets


@router.get("/{sheet_id}", response_model=SheetSchema)
async def get_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific sheet"""
    # Check if user has access to this sheet
    encryption_key = db.query(EncryptionKey).filter(
        EncryptionKey.sheet_id == sheet_id,
        EncryptionKey.user_id == current_user.id
    ).first()
    
    if not encryption_key:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found or access denied"
        )
    
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    return sheet


@router.get("/{sheet_id}/data")
async def get_sheet_data(
    sheet_id: int,
    google_credentials: Dict[str, Any],
    range_name: str = "A1:Z1000",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get decrypted sheet data"""
    # Check access and get encryption key
    encryption_key_record = db.query(EncryptionKey).filter(
        EncryptionKey.sheet_id == sheet_id,
        EncryptionKey.user_id == current_user.id
    ).first()
    
    if not encryption_key_record:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found or access denied"
        )
    
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    
    try:
        # Get user's private key (would need password from client)
        # For now, assuming client decrypts the sheet key
        
        # Get encrypted data from Google Sheets
        service = google_sheets_service.get_service(google_credentials)
        encrypted_values = google_sheets_service.get_spreadsheet_data(
            service, sheet.google_sheet_id, range_name
        )
        
        return {
            "sheet_id": sheet_id,
            "encrypted_data": encrypted_values,
            "range_name": range_name,
            "encryption_key_encrypted": encryption_key_record.encrypted_key
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sheet data: {str(e)}"
        )


@router.post("/{sheet_id}/data")
async def update_sheet_data(
    sheet_id: int,
    request: SheetDataRequest,
    google_credentials: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update sheet data with encrypted values"""
    # Check access
    encryption_key_record = db.query(EncryptionKey).filter(
        EncryptionKey.sheet_id == sheet_id,
        EncryptionKey.user_id == current_user.id
    ).first()
    
    if not encryption_key_record:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found or access denied"
        )
    
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    
    try:
        # The encrypted_data should already be encrypted by client
        # Convert JSON string back to 2D array format for Google Sheets
        import json
        values = json.loads(request.encrypted_data)
        
        # Update Google Sheet with encrypted data
        service = google_sheets_service.get_service(google_credentials)
        success = google_sheets_service.update_spreadsheet_data(
            service, 
            sheet.google_sheet_id, 
            request.range_name or "A1:Z1000", 
            values
        )
        
        if success:
            return {"message": "Sheet updated successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update sheet"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update sheet data: {str(e)}"
        )


@router.post("/{sheet_id}/share")
async def share_sheet(
    sheet_id: int,
    request: ShareSheetRequest,
    google_credentials: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Share sheet with another user"""
    # Check if current user owns the sheet
    sheet = db.query(Sheet).filter(
        Sheet.id == sheet_id,
        Sheet.owner_id == current_user.id
    ).first()
    
    if not sheet:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found or you don't have permission to share"
        )
    
    # Find the user to share with
    from ..auth import get_user_by_email
    target_user = get_user_by_email(db, request.user_email)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check if already shared
    existing_key = db.query(EncryptionKey).filter(
        EncryptionKey.sheet_id == sheet_id,
        EncryptionKey.user_id == target_user.id
    ).first()
    
    if existing_key:
        raise HTTPException(
            status_code=400,
            detail="Sheet already shared with this user"
        )
    
    try:
        # Create encryption key record for the new user
        db_encryption_key = EncryptionKey(
            sheet_id=sheet_id,
            user_id=target_user.id,
            encrypted_key=request.encrypted_key  # Already encrypted with target user's public key
        )
        
        db.add(db_encryption_key)
        db.commit()
        
        # Share the Google Sheet
        service = google_sheets_service.get_service(google_credentials)
        google_role = "reader" if request.permission == "read" else "writer"
        google_sheets_service.share_spreadsheet(
            service, sheet.google_sheet_id, request.user_email, google_role
        )
        
        return {"message": "Sheet shared successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share sheet: {str(e)}"
        )


@router.delete("/{sheet_id}")
async def delete_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete sheet (soft delete)"""
    sheet = db.query(Sheet).filter(
        Sheet.id == sheet_id,
        Sheet.owner_id == current_user.id
    ).first()
    
    if not sheet:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found or you don't have permission to delete"
        )
    
    sheet.is_active = False
    db.commit()
    
    return {"message": "Sheet deleted successfully"}
