from fastapi import APIRouter, HTTPException, status, Depends

from dto.request.sheet.create_sheet_request import CreateSheetRequest
from dto.request.sheet.filter_sheet_request import FilterSheetRequest
from dto.request.sheet.add_user_to_sheet_request import AddUserToSheetRequest
from dto.request.sheet.remove_user_from_sheet_request import RemoveUserFromSheetRequest
from dto.request.sheet.update_sheet_access_request import UpdateSheetAccessRequest
from dto.response.success_response import SuccessResponse
from model.user import User
from utils.utils import get_current_user
from service.sheet_service import SheetService

sheet_router = APIRouter()

@sheet_router.post(
    "",
    summary="Create New Encrypted Sheet",
    description="""
    **Create a new end-to-end encrypted Google Sheet**
    
    This endpoint creates a new encrypted sheet with the following process:
    
    1. **Sheet Registration**: Links Google Sheet URL to encrypted container
    2. **Key Generation**: Creates unique AES encryption key for sheet data
    3. **Key Distribution**: Encrypts sheet key with each member's public RSA key
    4. **Access Control**: Sets up initial permissions (creator becomes owner)
    
    **Security Architecture:**
    - Each sheet has unique AES-256 encryption key
    - Sheet key encrypted individually for each member using RSA
    - Only authorized members can decrypt sheet content
    - Creator automatically becomes owner with full permissions
    
    **Member Management:**
    - Include member_ids to add users during creation
    - Provide encrypted_sheet_keys array (one per member)
    - Members must have completed PIN/key setup to be added
    """,
    response_description="Created sheet information with access details",
    responses={
        200: {
            "description": "Sheet created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "link": "https://docs.google.com/spreadsheets/d/abc123",
                            "creator_id": "user_123",
                            "created_at": "2024-01-15T10:30:00Z",
                            "member_count": 3
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid sheet URL or encryption keys"
        },
        401: {
            "description": "Authentication required"
        }
    }
)
async def create_sheet(
    create_sheet_request: CreateSheetRequest, 
    sheet_service: SheetService = Depends(SheetService), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new encrypted sheet with member access.
    
    Args:
        create_sheet_request: Sheet creation details including members and keys
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (becomes owner)
        
    Returns:
        SuccessResponse containing created sheet information
    """
    result = sheet_service.create_sheet(
        link=create_sheet_request.link,
        creator_id=current_user.user_id,
        member_ids=create_sheet_request.member_ids,
        encrypted_sheet_keys=create_sheet_request.encrypted_sheet_keys,
        encrypted_sheet_key=create_sheet_request.encrypted_sheet_key
    )
    return SuccessResponse(result=result)

@sheet_router.get(
    "",
    summary="Get Sheet Details",
    description="""
    **Retrieve detailed information about a specific sheet**
    
    Returns comprehensive sheet information including:
    - Basic sheet metadata (title, URL, creation date)
    - User's access level and permissions
    - Member list and their roles
    - Encryption key information for authorized users
    
    **Access Control:**
    - Only members with access can view sheet details
    - Information filtered based on user's permission level
    - Owners see full administrative details
    
    **Use Cases:**
    - Loading sheet information in client applications
    - Verifying user permissions before operations
    - Displaying member lists and roles
    """,
    response_description="Comprehensive sheet information and access details",
    responses={
        200: {
            "description": "Sheet details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "link": "https://docs.google.com/spreadsheets/d/abc123",
                            "creator_id": "user_123",
                            "user_role": "owner",
                            "is_favorite": False,
                            "last_accessed": "2024-01-15T14:20:00Z",
                            "member_count": 3
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied - not a member of this sheet"
        },
        404: {
            "description": "Sheet not found"
        }
    }
)
async def get_sheet_by_id(
    sheet_id: str, 
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific sheet.
    
    Args:
        sheet_id: Unique identifier of the sheet
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing sheet details and user's access info
    """
    result = sheet_service.get_sheet_by_id(sheet_id, current_user.user_id)
    return SuccessResponse(result=result)

@sheet_router.post(
    "/filter",
    summary="Filter User's Sheets",
    description="""
    **Get paginated and filtered list of user's accessible sheets**
    
    This endpoint provides advanced filtering and pagination for sheets
    that the current user has access to. Useful for building sheet
    dashboards and management interfaces.
    
    **Available Filters:**
    - **Role-based**: Filter by user's role (owner, editor, viewer)
    - **Favorites**: Show only favorited sheets
    - **Pagination**: Page-based results with configurable page size
    - **Sorting**: By creation date, last accessed, or alphabetical
    
    **Response includes:**
    - Sheet metadata and access information
    - User's role and permissions for each sheet
    - Favorite status and last access times
    - Total count for pagination
    
    **Performance Notes:**
    - Results are cached for frequently accessed filters
    - Large sheet lists are automatically paginated
    """,
    response_description="Paginated list of filtered sheets with access details",
    responses={
        200: {
            "description": "Filtered sheets retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheets": [
                                {
                                    "sheet_id": "sheet_789",
                                    "link": "https://docs.google.com/spreadsheets/d/abc123",
                                    "user_role": "owner",
                                    "is_favorite": True,
                                    "last_accessed": "2024-01-15T14:20:00Z"
                                }
                            ],
                            "total_count": 15,
                            "page": 1,
                            "page_size": 10
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid filter parameters"
        }
    }
)
async def get_sheets_filter(
    request: FilterSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get filtered and paginated list of user's sheets.
    
    Args:
        request: Filter criteria including role, favorites, pagination
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing filtered sheet list with pagination info
    """
    request.user_id = current_user.user_id
    result = sheet_service.get_sheets_by_filter(request)
    return SuccessResponse(result=result)

@sheet_router.post(
    "/add-users",
    summary="Add Users to Sheet",
    description="""
    **Add new users to an existing encrypted sheet**
    
    This endpoint allows sheet owners and editors to add new collaborators
    to encrypted sheets. The process involves:
    
    1. **Permission Check**: Verify current user can add members
    2. **User Validation**: Ensure target users exist and have encryption setup
    3. **Key Distribution**: Encrypt sheet key with each new user's public key
    4. **Access Grant**: Set initial role and permissions for new members
    
    **Security Requirements:**
    - Only owners and editors can add users
    - New users must have completed PIN/key setup
    - Sheet key must be encrypted for each new user
    - Roles can be assigned during addition
    
    **Supported Roles:**
    - `viewer`: Read-only access to decrypted data
    - `editor`: Can modify sheet content
    - `owner`: Full administrative control (transfer only)
    """,
    response_description="Confirmation of users added with their access details",
    responses={
        200: {
            "description": "Users added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "added_users": [
                                {
                                    "user_id": "user_456",
                                    "email": "newuser@example.com",
                                    "role": "editor",
                                    "added_at": "2024-01-15T15:30:00Z"
                                }
                            ],
                            "total_members": 4
                        }
                    }
                }
            }
        },
        403: {
            "description": "Insufficient permissions to add users"
        },
        400: {
            "description": "Invalid user IDs or encryption keys"
        }
    }
)
async def add_users_to_sheet(
    sheet_id: str,
    request: AddUserToSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Add new users to an encrypted sheet.
    
    Args:
        sheet_id: ID of the sheet to add users to
        request: User addition request with user IDs, roles, and encrypted keys
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (must have add permissions)
        
    Returns:
        SuccessResponse containing details of added users
    """
    result = sheet_service.add_users_to_sheet(current_user.user_id, sheet_id, request)
    return SuccessResponse(result=result)

@sheet_router.post(
    "/remove-users",
    summary="Remove Users from Sheet",
    description="""
    **Remove users from an encrypted sheet**
    
    This endpoint allows authorized users to revoke access to encrypted sheets.
    When users are removed:
    
    1. **Access Revocation**: Immediate loss of sheet access
    2. **Key Invalidation**: Their encrypted sheet keys become unusable
    3. **History Preservation**: Past contributions remain in sheet history
    4. **Notification**: Users may be notified of access removal
    
    **Permission Requirements:**
    - **Owners**: Can remove any user except themselves
    - **Editors**: Cannot remove other users (owner-only operation)
    - **Viewers**: Cannot remove any users
    
    **Important Notes:**
    - Removed users lose immediate access to encrypted data
    - Sheet keys are not re-encrypted (existing data remains accessible to remaining members)
    - Owners cannot remove themselves (use transfer ownership first)
    
    **Bulk Operations:**
    - Multiple users can be removed in a single request
    - Atomic operation - all succeed or all fail
    """,
    response_description="Confirmation of users removed and updated member count",
    responses={
        200: {
            "description": "Users removed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "removed_users": [
                                {
                                    "user_id": "user_789",
                                    "email": "removed@example.com",
                                    "removed_at": "2024-01-15T16:45:00Z"
                                }
                            ],
                            "remaining_members": 2
                        }
                    }
                }
            }
        },
        403: {
            "description": "Insufficient permissions to remove users"
        },
        400: {
            "description": "Cannot remove sheet owner or invalid user IDs"
        }
    }
)
async def remove_users_from_sheet(
    sheet_id: str,
    request: RemoveUserFromSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Remove users from an encrypted sheet.
    
    Args:
        sheet_id: ID of the sheet to remove users from
        request: User removal request with user IDs
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (must have remove permissions)
        
    Returns:
        SuccessResponse containing details of removed users
    """
    result = sheet_service.remove_users_from_sheet(current_user.user_id, sheet_id, request)
    return SuccessResponse(result=result)

@sheet_router.post(
    "/leave",
    summary="Leave Sheet",
    description="""
    **Leave an encrypted sheet (self-removal)**
    
    Allows users to voluntarily leave sheets they have access to.
    This is different from being removed by an owner/admin.
    
    **Process:**
    1. **Self-Removal**: User removes themselves from sheet access
    2. **Key Cleanup**: User's encrypted sheet key is invalidated
    3. **Access Loss**: Immediate loss of access to encrypted data
    4. **History Preservation**: Past contributions remain in sheet
    
    **Special Cases:**
    - **Sheet Owners**: Cannot leave their own sheets
    - **Last Member**: Cannot leave if only member remaining
    - **Transfer Required**: Owners must transfer ownership before leaving
    
    **Use Cases:**
    - No longer need access to shared sheet
    - Privacy concerns about continued access
    - Cleaning up sheet memberships
    
    **Recovery:**
    - Must be re-added by current members to regain access
    - New encrypted sheet key will be generated
    """,
    response_description="Confirmation of successful sheet departure",
    responses={
        200: {
            "description": "Successfully left the sheet",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "left_at": "2024-01-15T17:00:00Z",
                            "remaining_members": 2
                        }
                    }
                }
            }
        },
        400: {
            "description": "Cannot leave - you are the owner or last member"
        },
        404: {
            "description": "Sheet not found or you are not a member"
        }
    }
)
async def leave_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Leave a sheet (self-removal).
    
    Args:
        sheet_id: ID of the sheet to leave
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing confirmation of departure
    """
    result = sheet_service.leave_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.delete(
    "",
    summary="Delete Sheet (Owner Only)",
    description="""
    **Permanently delete an encrypted sheet**
    
    This is a destructive operation that completely removes a sheet
    and all associated access records. Only sheet owners can perform
    this operation.
    
    **Deletion Process:**
    1. **Ownership Verification**: Confirm user is sheet owner
    2. **Access Revocation**: Remove all member access immediately
    3. **Key Destruction**: Invalidate all encrypted sheet keys
    4. **Record Cleanup**: Remove sheet metadata and history
    
    **⚠️ WARNING: This operation is irreversible!**
    - All encrypted data becomes permanently inaccessible
    - Member access is immediately revoked
    - Sheet history and metadata are permanently deleted
    - Google Sheets document itself is NOT deleted (only encryption layer)
    
    **Permission Requirements:**
    - Must be the sheet owner
    - Cannot be delegated to editors or viewers
    
    **Alternative Actions:**
    - Consider transferring ownership instead of deletion
    - Remove specific users rather than deleting entire sheet
    """,
    response_description="Confirmation of successful sheet deletion",
    responses={
        200: {
            "description": "Sheet deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "deleted_at": "2024-01-15T18:00:00Z",
                            "affected_members": 3
                        }
                    }
                }
            }
        },
        403: {
            "description": "Only sheet owners can delete sheets"
        },
        404: {
            "description": "Sheet not found"
        }
    }
)
async def delete_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete a sheet (owner only).
    
    Args:
        sheet_id: ID of the sheet to delete
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (must be owner)
        
    Returns:
        SuccessResponse containing deletion confirmation
    """
    result = sheet_service.delete_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.put(
    "/access",
    summary="Update User Sheet Access",
    description="""
    **Update user's access permissions and settings for a sheet**
    
    This endpoint allows authorized users to modify access settings
    for sheet members, including roles, favorite status, and encryption keys.
    
    **Updatable Properties:**
    - **Role**: Change user's permission level (viewer, editor, owner)
    - **Favorite Status**: Mark/unmark sheet as favorite for user
    - **Encrypted Key**: Update user's encrypted sheet key
    - **Access Metadata**: Update last access time and preferences
    
    **Permission Matrix:**
    - **Owners**: Can update any user's access (including role changes)
    - **Editors**: Can only update their own favorite status
    - **Viewers**: Can only update their own favorite status
    
    **Role Change Rules:**
    - Only owners can promote/demote user roles
    - Cannot demote the last owner (must transfer ownership first)
    - Role changes take effect immediately
    
    **Security Notes:**
    - Encrypted key updates require proper RSA encryption
    - Role changes are logged for audit purposes
    """,
    response_description="Updated access information for the user",
    responses={
        200: {
            "description": "Access updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "user_id": "user_456",
                            "sheet_id": "sheet_789",
                            "role": "editor",
                            "is_favorite": True,
                            "updated_at": "2024-01-15T19:15:00Z"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Insufficient permissions to update access"
        },
        400: {
            "description": "Invalid role or access parameters"
        }
    }
)
async def update_sheet_access(
    sheet_id: str,
    target_user_id: str,
    request: UpdateSheetAccessRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's access permissions and settings for a sheet.
    
    Args:
        sheet_id: ID of the sheet to update access for
        target_user_id: ID of the user whose access to update
        request: Access update request with new settings
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (must have update permissions)
        
    Returns:
        SuccessResponse containing updated access information
    """
    result = sheet_service.update_user_sheet_access(
        current_user.user_id, 
        target_user_id, 
        sheet_id, 
        request
    )
    return SuccessResponse(result=result)

@sheet_router.put(
    "/favorite",
    summary="Toggle Sheet Favorite Status",
    description="""
    **Mark or unmark a sheet as favorite**
    
    This is a user-specific setting that helps organize and prioritize
    sheets in the user interface. Favorite sheets typically appear
    at the top of sheet lists and may have special visual indicators.
    
    **Features:**
    - **Personal Setting**: Only affects current user's view
    - **Quick Access**: Favorited sheets appear in priority lists
    - **Instant Update**: Changes take effect immediately
    - **No Permission Required**: Any member can favorite/unfavorite
    
    **Use Cases:**
    - Mark frequently accessed sheets for quick access
    - Organize large numbers of shared sheets
    - Create personal priority lists
    - Improve workflow efficiency
    
    **UI Integration:**
    - Favorite sheets often shown with star icons
    - May appear in separate "Favorites" section
    - Can be used for filtering in sheet lists
    """,
    response_description="Updated favorite status for the current user",
    responses={
        200: {
            "description": "Favorite status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "user_id": "user_123",
                            "is_favorite": True,
                            "updated_at": "2024-01-15T20:30:00Z"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Sheet not found or user not a member"
        }
    }
)
async def toggle_favorite(
    sheet_id: str,
    is_favorite: bool,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle favorite status for a sheet.
    
    Args:
        sheet_id: ID of the sheet to update favorite status for
        is_favorite: New favorite status (True to favorite, False to unfavorite)
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing updated favorite status
    """
    request = UpdateSheetAccessRequest(is_favorite=is_favorite)
    result = sheet_service.update_user_sheet_access(
        current_user.user_id, 
        current_user.user_id, 
        sheet_id, 
        request
    )
    return SuccessResponse(result=result)

@sheet_router.get(
    "/users",
    summary="Get Sheet Members",
    description="""
    **Retrieve list of all users with access to a sheet**
    
    Returns comprehensive information about all sheet members,
    including their roles, access levels, and activity status.
    
    **Returned Information:**
    - User profile information (name, email, avatar)
    - Access role (owner, editor, viewer)
    - Join date and last activity
    - Online/offline status (if available)
    - Permission details
    
    **Access Control:**
    - All sheet members can view the member list
    - Sensitive information filtered based on privacy settings
    - Owners see additional administrative details
    
    **Use Cases:**
    - Display member list in sheet interface
    - User management and role assignment
    - Activity monitoring and collaboration insights
    - Contact information for sheet communication
    """,
    response_description="List of all sheet members with their access details",
    responses={
        200: {
            "description": "Member list retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "members": [
                                {
                                    "user_id": "user_123",
                                    "email": "owner@example.com",
                                    "name": "Sheet Owner",
                                    "role": "owner",
                                    "joined_at": "2024-01-10T10:00:00Z",
                                    "last_accessed": "2024-01-15T14:30:00Z"
                                },
                                {
                                    "user_id": "user_456",
                                    "email": "editor@example.com",
                                    "name": "Sheet Editor",
                                    "role": "editor",
                                    "joined_at": "2024-01-12T15:20:00Z",
                                    "last_accessed": "2024-01-15T12:45:00Z"
                                }
                            ],
                            "total_members": 2
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied - not a member of this sheet"
        },
        404: {
            "description": "Sheet not found"
        }
    }
)
async def get_users_in_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all users with access to a sheet.
    
    Args:
        sheet_id: ID of the sheet to get members for
        sheet_service: Injected sheet service
        current_user: Currently authenticated user (must be a member)
        
    Returns:
        SuccessResponse containing list of sheet members
    """
    result = sheet_service.get_users_in_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get(
    "/sheet-key",
    summary="Get Encrypted Sheet Key",
    description="""
    **Retrieve user's encrypted sheet key for decryption**
    
    This endpoint returns the sheet's AES encryption key, encrypted
    specifically for the current user using their RSA public key.
    This key is required to decrypt sheet data client-side.
    
    **Security Process:**
    1. **Authentication**: Verify user has sheet access
    2. **Key Retrieval**: Get user's specific encrypted key
    3. **Validation**: Ensure key is properly encrypted for user
    4. **Delivery**: Return encrypted key for client-side decryption
    
    **Client-Side Usage:**
    1. Retrieve encrypted key from this endpoint
    2. Decrypt key using user's RSA private key (from PIN)
    3. Use decrypted AES key for sheet data encryption/decryption
    4. Never store decrypted key persistently
    
    **Security Notes:**
    - Key is encrypted specifically for requesting user
    - Cannot be used by other users
    - Requires user's private key for decryption
    - Should be used immediately and not cached
    """,
    response_description="User's encrypted sheet key for client-side decryption",
    responses={
        200: {
            "description": "Encrypted sheet key retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "encrypted_sheet_key": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
                            "key_version": 1,
                            "encryption_algorithm": "RSA-OAEP"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied - not a member of this sheet"
        },
        404: {
            "description": "Sheet not found or no key available"
        }
    }
)
async def get_encrypted_sheet_key(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's encrypted sheet key for decryption.
    
    Args:
        sheet_id: ID of the sheet to get key for
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing encrypted sheet key
    """
    result = sheet_service.get_encrypted_sheet_key(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get(
    "/role",
    summary="Get User's Sheet Role",
    description="""
    **Get current user's role and permissions in a sheet**
    
    Returns the user's access level and associated permissions
    for a specific sheet. This information is used to determine
    what actions the user can perform.
    
    **Role Types:**
    - **owner**: Full administrative control
      - Can add/remove users
      - Can change user roles
      - Can delete sheet
      - Can transfer ownership
    
    - **editor**: Content modification access
      - Can read and modify sheet data
      - Can add comments and suggestions
      - Cannot manage users or delete sheet
    
    - **viewer**: Read-only access
      - Can view decrypted sheet content
      - Can add comments (if enabled)
      - Cannot modify data or manage users
    
    **Use Cases:**
    - UI permission checks (show/hide buttons)
    - Client-side access control
    - Feature availability determination
    - Audit and compliance reporting
    """,
    response_description="User's role and permission details for the sheet",
    responses={
        200: {
            "description": "User role retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "role": "editor",
                            "permissions": {
                                "can_read": True,
                                "can_write": True,
                                "can_add_users": False,
                                "can_remove_users": False,
                                "can_delete_sheet": False
                            },
                            "granted_at": "2024-01-12T15:20:00Z"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied - not a member of this sheet"
        },
        404: {
            "description": "Sheet not found"
        }
    }
)
async def get_user_role(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's role in a sheet.
    
    Args:
        sheet_id: ID of the sheet to get role for
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing user's role and permissions
    """
    result = sheet_service.get_user_role_in_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get(
    "/permission",
    summary="Check User Permissions",
    description="""
    **Verify if user has required permission level for a sheet**
    
    This endpoint performs permission checks to determine if the current
    user has sufficient access level to perform specific operations.
    
    **Permission Hierarchy:**
    - **owner** > **editor** > **viewer**
    - Higher roles inherit permissions of lower roles
    - Permission checks are inclusive (editor passes viewer check)
    
    **Supported Permission Levels:**
    - `viewer`: Basic read access (default)
    - `editor`: Content modification access
    - `owner`: Full administrative access
    
    **Common Use Cases:**
    - Pre-flight permission checks before operations
    - UI element visibility control
    - API gateway authorization
    - Feature availability validation
    
    **Response:**
    - `true`: User has required permission or higher
    - `false`: User lacks required permission level
    
    **Security Notes:**
    - Always check permissions server-side for critical operations
    - Client-side checks are for UI optimization only
    - Permission changes take effect immediately
    """,
    response_description="Boolean result indicating if user has required permission",
    responses={
        200: {
            "description": "Permission check completed",
            "content": {
                "application/json": {
                    "examples": {
                        "has_permission": {
                            "summary": "User has required permission",
                            "value": {
                                "code": 0,
                                "message": "successfully",
                                "result": {
                                    "has_permission": True,
                                    "user_role": "editor",
                                    "required_role": "viewer"
                                }
                            }
                        },
                        "lacks_permission": {
                            "summary": "User lacks required permission",
                            "value": {
                                "code": 0,
                                "message": "successfully",
                                "result": {
                                    "has_permission": False,
                                    "user_role": "viewer",
                                    "required_role": "editor"
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Sheet not found or user not a member"
        },
        400: {
            "description": "Invalid permission level specified"
        }
    }
)
async def check_permission(
    sheet_id: str,
    required_role: str = "viewer",
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has required permission level.
    
    Args:
        sheet_id: ID of the sheet to check permissions for
        required_role: Minimum required role (viewer, editor, owner)
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing permission check result
    """
    result = sheet_service.check_user_permission(current_user.user_id, sheet_id, required_role)
    return SuccessResponse(result=result)

@sheet_router.put(
    "/access-time",
    summary="Update Last Access Time",
    description="""
    **Record user's last access time for a sheet**
    
    This endpoint updates the timestamp of when the user last accessed
    a specific sheet. This information is used for:
    
    **Analytics and Insights:**
    - Track user engagement with sheets
    - Identify frequently vs rarely accessed content
    - Generate usage reports and statistics
    - Determine sheet popularity and relevance
    
    **User Experience:**
    - Sort sheets by recent activity
    - Show "last viewed" information in UI
    - Highlight recently accessed sheets
    - Improve sheet discovery and organization
    
    **Administrative Features:**
    - Monitor team collaboration patterns
    - Identify inactive sheets for cleanup
    - Track user activity for compliance
    - Generate access audit trails
    
    **Automatic vs Manual Updates:**
    - Can be called automatically when sheet is opened
    - Manual calls for specific activity tracking
    - Batch updates for performance optimization
    
    **Privacy Notes:**
    - Access times are visible to sheet owners
    - Used for legitimate business purposes only
    - Complies with data privacy regulations
    """,
    response_description="Confirmation of updated access time",
    responses={
        200: {
            "description": "Access time updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "user_id": "user_123",
                            "last_accessed": "2024-01-15T21:45:00Z",
                            "access_count": 47
                        }
                    }
                }
            }
        },
        404: {
            "description": "Sheet not found or user not a member"
        }
    }
)
async def update_last_accessed(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's last accessed time for a sheet.
    
    Args:
        sheet_id: ID of the sheet to update access time for
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing updated access information
    """
    result = sheet_service.update_last_accessed(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get(
    "/by-link",
    summary="Get Sheet by Link",
    description="""
    **Retrieve sheet information using Google Sheets URL**
    
    This endpoint allows users to access sheet details by providing
    the Google Sheets URL instead of the internal sheet ID. This is
    useful for:
    
    **Use Cases:**
    - Direct access from Google Sheets interface
    - Sharing sheets via Google Sheets URLs
    - Integration with external systems using sheet URLs
    - Quick access without needing to remember sheet IDs
    
    **Process:**
    1. **URL Validation**: Verify the provided link is a valid Google Sheets URL
    2. **Sheet Lookup**: Find the corresponding encrypted sheet record
    3. **Access Check**: Verify current user has access to the sheet
    4. **Data Return**: Return sheet details with user's access information
    
    **Security:**
    - Only users with existing access can retrieve sheet information
    - Access permissions are enforced same as sheet ID access
    - Invalid or inaccessible sheets return 404 error
    
    **Response includes:**
    - Sheet metadata (ID, creation date, creator)
    - User's role and permissions
    - Encrypted sheet key for current user
    - Favorite status and last access time
    """,
    response_description="Sheet details retrieved using Google Sheets URL",
    responses={
        200: {
            "description": "Sheet details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "sheet_id": "sheet_789",
                            "link": "https://docs.google.com/spreadsheets/d/abc123",
                            "creator_id": "user_123",
                            "user_role": "editor",
                            "is_favorite": True,
                            "last_accessed": "2024-01-15T14:20:00Z",
                            "encrypted_sheet_key": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied - not a member of this sheet"
        },
        404: {
            "description": "Sheet not found or invalid Google Sheets URL"
        },
        400: {
            "description": "Invalid or malformed Google Sheets URL"
        }
    }
)
async def get_sheet_by_link(
    link: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """
    Get sheet details using Google Sheets URL.
    
    Args:
        link: Google Sheets URL to lookup
        sheet_service: Injected sheet service
        current_user: Currently authenticated user
        
    Returns:
        SuccessResponse containing sheet details for the provided URL
    """
    result = sheet_service.get_sheet_by_link(link, current_user.user_id)
    return SuccessResponse(result=result)
