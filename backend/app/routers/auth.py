from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, User as UserSchema, Token, GoogleAuthRequest
from ..auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_user_by_email,
    get_current_active_user
)
from ..crypto import CryptoManager
from ..google_sheets import google_sheets_service
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Generate RSA key pair for the user
    private_key_pem, public_key_pem = CryptoManager.generate_rsa_keypair()
    
    # Encrypt the private key with user's password
    encrypted_private_key, _ = CryptoManager.encrypt_private_key(private_key_pem, user.password)
    
    # Create user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        public_key=public_key_pem,
        encrypted_private_key=encrypted_private_key,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


@router.get("/google/auth-url")
async def get_google_auth_url():
    """Get Google OAuth2 authorization URL"""
    auth_url = google_sheets_service.get_auth_url()
    return {"auth_url": auth_url}


@router.post("/google/callback")
async def google_callback(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Handle Google OAuth2 callback"""
    try:
        # Exchange code for tokens
        tokens = google_sheets_service.exchange_code_for_tokens(request.code)
        
        # Store tokens securely (you might want to encrypt these)
        # For now, we'll return them to be stored client-side
        # In production, consider storing encrypted tokens in database
        
        return {
            "message": "Google authentication successful",
            "tokens": tokens
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to authenticate with Google: {str(e)}"
        )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
