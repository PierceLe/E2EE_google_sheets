from typing import List, Optional
from dto.request.sheet.filter_sheet_request import FilterSheetRequest
from dto.request.sheet.add_user_to_sheet_request import AddUserToSheetRequest
from dto.request.sheet.remove_user_from_sheet_request import RemoveUserFromSheetRequest
from dto.request.sheet.update_sheet_access_request import UpdateSheetAccessRequest
from dto.response.base_page_response import BasePageResponse
from dto.response.sheet.sheet_response import SheetResponse
from dto.response.user_response import UserResponse
from model.sheet import Sheet
from model.user_sheet import UserSheet
from repository.sheet_repository import SheetRepository
from repository.user_sheet_repository import UserSheetRepository
from repository.user_repository import UserRepository
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from sqlalchemy import and_, or_, desc, asc
from database import SessionLocal


class SheetService:
    def __init__(self):
        self.sheet_repository = SheetRepository()
        self.user_sheet_repository = UserSheetRepository()
        self.user_repository = UserRepository()

    def create_sheet(self,
                    link: str,
                    creator_id: str,
                    member_ids: list[str],
                    encrypted_sheet_keys: list[str],
                    encrypted_sheet_key: str
                    ) -> SheetResponse:
        """Create a new sheet and add users to it"""
        # Create the sheet
        sheet = self.sheet_repository.create_sheet(link=link, creator_id=creator_id)
        
        # Add creator as owner
        self.user_sheet_repository.create_user_sheet(
            user_id=creator_id,
            sheet_id=sheet.sheet_id,
            encrypted_sheet_key=encrypted_sheet_key,
            role="owner"
        )
        
        # Add other members as viewers
        visited = set([creator_id])
        for member_id, member_encrypted_key in zip(member_ids, encrypted_sheet_keys):
            if member_id not in visited:
                self.user_sheet_repository.create_user_sheet(
                    user_id=member_id,
                    sheet_id=sheet.sheet_id,
                    encrypted_sheet_key=member_encrypted_key,
                    role="viewer"
                )
                visited.add(member_id)
        
        return SheetResponse(
            sheet_id=sheet.sheet_id,
            link=sheet.link,
            creator_id=sheet.creator_id,
            created_at=sheet.created_at,
            role="owner",
            encrypted_sheet_key=encrypted_sheet_key
        )

    def get_sheet_by_id(self, sheet_id: str, user_id: str) -> SheetResponse:
        """Get sheet details for a specific user"""
        # Check if user has access to the sheet
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        
        # Get sheet link
        sheet_link = self.sheet_repository.get_link_by_sheet_id(sheet_id)
        if not sheet_link:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)

        # Get creator info
        with SessionLocal() as db:
            sheet = db.query(Sheet).filter(Sheet.sheet_id == sheet_id).first()
            if not sheet:
                raise AppException(ErrorCode.SHEET_NOT_FOUND)

            creator = self.user_repository.get_user_by_user_id(sheet.creator_id)

            return SheetResponse(
                sheet_id=sheet_id,
                link=sheet_link,
                creator_id=sheet.creator_id,
                created_at=sheet.created_at,
                role=user_sheet.role,
                encrypted_sheet_key=user_sheet.encrypted_sheet_key,
                is_favorite=user_sheet.is_favorite,
                last_accessed_at=user_sheet.last_accessed_at,
                creator=UserResponse.fromUserModel(creator) if creator else None
            )

    def get_sheets_by_filter(self, request: FilterSheetRequest) -> BasePageResponse:
        """Get filtered and paginated list of sheets for a user"""
        if not request.user_id:
            raise AppException(ErrorCode.USER_NOT_FOUND)
        
        with SessionLocal() as db:
            # Base query joining UserSheet and Sheet
            query = db.query(UserSheet, Sheet).join(
                Sheet, UserSheet.sheet_id == Sheet.sheet_id
            ).filter(UserSheet.user_id == request.user_id)
            
            # Apply filters
            if request.is_favorite is not None:
                query = query.filter(UserSheet.is_favorite == request.is_favorite)
            
            if request.role:
                query = query.filter(UserSheet.role == request.role)
            
            # Apply sorting
            if request.sorts_by and request.sorts_dir:
                for sort_field, sort_dir in zip(request.sorts_by, request.sorts_dir):
                    if sort_field == "created_at":
                        order_field = Sheet.created_at
                    elif sort_field == "last_accessed_at":
                        order_field = UserSheet.last_accessed_at
                    elif sort_field == "is_favorite":
                        order_field = UserSheet.is_favorite
                    else:
                        continue
                    
                    if sort_dir.lower() == "desc":
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
            else:
                # Default sorting by created_at desc
                query = query.order_by(desc(Sheet.created_at))
            
            # Count total items
            total = query.count()
            
            # Apply pagination
            offset = (request.page - 1) * request.page_size
            items = query.offset(offset).limit(request.page_size).all()
            
            # Convert to response objects
            sheet_responses = []
            for user_sheet, sheet in items:
                # Get creator info
                creator = self.user_repository.get_user_by_user_id(sheet.creator_id)
                
                sheet_responses.append(SheetResponse(
                    sheet_id=sheet.sheet_id,
                    link=sheet.link,
                    creator_id=sheet.creator_id,
                    created_at=sheet.created_at,
                    role=user_sheet.role,
                    encrypted_sheet_key=user_sheet.encrypted_sheet_key,
                    is_favorite=user_sheet.is_favorite,
                    last_accessed_at=user_sheet.last_accessed_at,
                    creator=UserResponse.fromUserModel(creator) if creator else None
                ))
            
            total_pages = (total + request.page_size - 1) // request.page_size
            
            return BasePageResponse(
                items=sheet_responses,
                total=total,
                page=request.page,
                page_size=request.page_size,
                total_pages=total_pages
            )

    def add_users_to_sheet(self, current_user_id: str, sheet_id: str, request: AddUserToSheetRequest) -> bool:
        """Add users to a sheet (requires owner or editor permission)"""
        # Check if current user has permission
        current_user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(current_user_id, sheet_id)
        if not current_user_sheet or current_user_sheet.role not in ["owner", "editor"]:
            raise AppException(ErrorCode.EDIT_SHEET_NOT_PERMISSION)
        
        # Validate input lengths
        if len(request.user_ids) != len(request.encrypted_sheet_keys):
            raise ValueError("user_ids and encrypted_sheet_keys must have the same length")
        
        # Set default roles if not provided
        roles = request.roles if request.roles else ["viewer"] * len(request.user_ids)
        if len(roles) != len(request.user_ids):
            roles = ["viewer"] * len(request.user_ids)
        
        # Add users to sheet
        for user_id, encrypted_key, role in zip(request.user_ids, request.encrypted_sheet_keys, roles):
            if not self.user_sheet_repository.check_exist_by_user_id_and_sheet_id(user_id, sheet_id):
                self.user_sheet_repository.create_user_sheet(
                    user_id=user_id,
                    sheet_id=sheet_id,
                    encrypted_sheet_key=encrypted_key,
                    role=role
                )
        
        return True

    def remove_users_from_sheet(self, current_user_id: str, sheet_id: str, request: RemoveUserFromSheetRequest) -> bool:
        """Remove users from a sheet (requires owner permission)"""
        # Check if current user is owner
        current_user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(current_user_id, sheet_id)
        if not current_user_sheet or current_user_sheet.role != "owner":
            raise AppException(ErrorCode.EDIT_SHEET_NOT_PERMISSION)
        
        # Don't allow owner to remove themselves
        user_ids_to_remove = [uid for uid in request.user_ids if uid != current_user_id]
        
        # Remove users
        self.user_sheet_repository.delete_user_sheet_by_sheet_id_and_list_user_id(sheet_id, user_ids_to_remove)
        
        return True

    def leave_sheet(self, user_id: str, sheet_id: str) -> bool:
        """User leaves a sheet"""
        # Check if user has access
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        
        # If user is owner, they cannot leave unless they transfer ownership first
        if user_sheet.role == "owner":
            # Check if there are other users in the sheet
            users_in_sheet = self.user_sheet_repository.get_user_in_sheet(sheet_id)
            if len(users_in_sheet) > 1:
                raise AppException(ErrorCode.EDIT_SHEET_NOT_PERMISSION)  # Owner must transfer ownership first
        
        # Remove user from sheet
        self.user_sheet_repository.delete_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        
        return True

    def delete_sheet(self, user_id: str, sheet_id: str) -> bool:
        """Delete a sheet (requires owner permission)"""
        # Check if user is owner
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet or user_sheet.role != "owner":
            raise AppException(ErrorCode.EDIT_SHEET_NOT_PERMISSION)
        
        # Delete all user-sheet relationships
        self.user_sheet_repository.delete_user_sheet_by_sheet_id(sheet_id)
        
        # Delete the sheet itself would require adding delete method to SheetRepository
        # For now, we'll just remove all access
        
        return True

    def update_user_sheet_access(self, current_user_id: str, target_user_id: str, sheet_id: str, request: UpdateSheetAccessRequest) -> bool:
        """Update user's access to a sheet (role, favorite status, encrypted key)"""
        # If updating another user's access, check permission
        if current_user_id != target_user_id:
            current_user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(current_user_id, sheet_id)
            if not current_user_sheet or current_user_sheet.role != "owner":
                raise AppException(ErrorCode.EDIT_SHEET_NOT_PERMISSION)
        
        # Check if target user has access
        if not self.user_sheet_repository.check_exist_by_user_id_and_sheet_id(target_user_id, sheet_id):
            raise AppException(ErrorCode.USER_NOT_FOUND)
        
        # Update role
        if request.role:
            self.user_sheet_repository.update_role(target_user_id, sheet_id, request.role)
        
        # Update favorite status (users can only update their own)
        if request.is_favorite is not None and current_user_id == target_user_id:
            self.user_sheet_repository.mark_favorite(target_user_id, sheet_id, request.is_favorite)
        
        # Update encrypted key
        if request.encrypted_sheet_key:
            self.user_sheet_repository.update_encrypted_key(target_user_id, sheet_id, request.encrypted_sheet_key)
        
        return True

    def get_users_in_sheet(self, current_user_id: str, sheet_id: str) -> List[UserResponse]:
        """Get all users who have access to a sheet"""
        # Check if current user has access
        if not self.user_sheet_repository.check_exist_by_user_id_and_sheet_id(current_user_id, sheet_id):
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        
        users = self.user_sheet_repository.get_user_in_sheet(sheet_id)
        return [UserResponse.fromUserModel(user) for user in users]

    def get_encrypted_sheet_key(self, user_id: str, sheet_id: str) -> str:
        """Get user's encrypted sheet key"""
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        
        return user_sheet.encrypted_sheet_key

    def update_last_accessed(self, user_id: str, sheet_id: str) -> bool:
        """Update user's last accessed time for a sheet"""
        from datetime import datetime
        
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet:
            return False
        
        # Update last accessed time - would need to add this method to repository
        # For now, return True as placeholder
        return True

    def get_user_role_in_sheet(self, user_id: str, sheet_id: str) -> Optional[str]:
        """Get user's role in a specific sheet"""
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        return user_sheet.role if user_sheet else None

    def check_user_permission(self, user_id: str, sheet_id: str, required_role: str = "viewer") -> bool:
        """Check if user has required permission level for a sheet"""
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet_id)
        if not user_sheet:
            return False
        
        role_hierarchy = {"owner": 3, "editor": 2, "viewer": 1}
        user_level = role_hierarchy.get(user_sheet.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level

    def get_sheet_by_link(self, link: str, user_id: str) -> SheetResponse:
        """Get sheet details by link for a specific user"""
        # Find sheet by link
        sheet = self.sheet_repository.get_sheet_by_link(link)
        if not sheet:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        
        # Check if user has access to the sheet
        user_sheet = self.user_sheet_repository.get_user_sheet_by_user_id_and_sheet_id(user_id, sheet.sheet_id)
        if not user_sheet:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)

        # Get creator info
        creator = self.user_repository.get_user_by_id(sheet.creator_id)

        return SheetResponse(
            sheet_id=sheet.sheet_id,
            link=sheet.link,
            creator_id=sheet.creator_id,
            created_at=sheet.created_at,
            role=user_sheet.role,
            encrypted_sheet_key=user_sheet.encrypted_sheet_key,
            is_favorite=user_sheet.is_favorite,
            last_accessed_at=user_sheet.last_accessed_at,
            creator=UserResponse.fromUserModel(creator) if creator else None
        )
