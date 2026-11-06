"""
Authentication API Router

Purpose:
1. Authenticate users using username and password.
2. Verify stored hashed passwords.
3. Generate JWT access tokens after successful login.
4. Protect endpoints using JWT authentication.
5. Retrieve information about the currently logged-in user.

Endpoint	Method	Purpose	                                Authentication
/auth/login	POST	Validate credentials and generate JWT	Username + password
/auth/me	GET	    Retrieve current logged-in user	JWT     Bearer token

"""

# Import FastAPI components.
# APIRouter: Groups authentication endpoints.
# Depends: Injects dependencies such as database sessions.
# HTTPException: Returns HTTP errors.
from fastapi import APIRouter, Depends, HTTPException
# Import OAuth2 form for receiving username and password.
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy import select # Import select to execute SQL SELECT queries.
from sqlalchemy.ext.asyncio import AsyncSession
# Import authentication database session dependency
from app.auth.database import get_auth_session
# Import security functions.
from app.auth.security import (
    verify_password,
    create_access_token,
)
from app.api.dependencies import get_current_user
from app.models.api_user import APIUser
# Response containing JWT access token and user information.
from app.schemas.auth import TokenResponse, UserResponse

# Create authentication router.
# prefix="/auth" means all endpoints start with /auth.
# tags are used to group endpoints in Swagger documentation.
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Define POST /auth/login endpoint.
# response_model validates and formats the token response.
@router.post("/login", response_model=TokenResponse)
async def login(
    # Read username and password from OAuth2 form data.
    # FastAPI automatically extracts these values.
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_auth_session),
):

    # Execute SQL query to find user by username.
    result = await session.execute(
        select(APIUser).where(
            APIUser.username == form.username
        )
    )

    # Retrieve matching user object.
    # Returns None if username does not exist
    user = result.scalar_one_or_none()

    # Validate login credentials.
    # Reject login if:
    # 1. User does not exist.
    # 2. Password does not match stored hash.
    # 3. User account is inactive.

    if user is None or not verify_password(
        form.password, user.hashed_password
    ) or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT access token using authenticated user ID.
    # Return token using TokenResponse schema.
    return TokenResponse(
        access_token=create_access_token(user.id)
    )

# Define GET /auth/me endpoint.
# This endpoint requires a valid JWT access token.
@router.get("/me", response_model=UserResponse)
async def get_me(
    # get_current_user validates the JWT token,
    # retrieves the associated user,
    # and rejects invalid or expired tokens.
    user: APIUser = Depends(get_current_user),
):

    # Return authenticated user's information.
    # UserResponse controls which fields are exposed.
    # Sensitive fields such as hashed_password
    # should never be included in UserResponse.
    return user