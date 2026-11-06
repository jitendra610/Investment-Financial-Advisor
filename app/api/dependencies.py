# JWT library used to handle JSON Web Token errors.
import jwt

# Depends: Injects dependencies into FastAPI endpoints.
# HTTPException: Returns HTTP errors to the client.
# status: Provides standard HTTP status codes.
from fastapi import Depends, HTTPException, status

# Extracts the Bearer token from the Authorization header.
from fastapi.security import OAuth2PasswordBearer

# Used to construct SQL SELECT queries.
from sqlalchemy import select

# Provides asynchronous database operations.
from sqlalchemy.ext.asyncio import AsyncSession

# Dependency that provides an authentication database session.
from app.auth.database import get_auth_session

# Custom function to decode and validate JWT access tokens.
from app.auth.security import decode_access_token

# APIUser: Stores application user information.
# CustomerAccess: Maps users to customers they can access.
from app.models.api_user import APIUser, CustomerAccess


# Configure OAuth2 Bearer authentication.
# FastAPI expects the token in the request header:
# Authorization: Bearer <access_token>
#
# tokenUrl specifies the login endpoint used by Swagger UI
# to obtain an access token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


# Helper function to create a standard 401 Unauthorized error.
def unauthorized():
    return HTTPException(
        # HTTP 401 means authentication failed.
        status_code=status.HTTP_401_UNAUTHORIZED,

        # Error message returned to the client.
        detail="Invalid or expired authentication token",

        # Indicates that Bearer authentication is required.
        headers={"WWW-Authenticate": "Bearer"},
    )


# Authenticate the user using the JWT access token.
# Returns the authenticated APIUser object.
async def get_current_user(
    # Automatically extract the Bearer token from the request.
    token: str = Depends(oauth2_scheme),

    # Automatically inject an asynchronous database session.
    session: AsyncSession = Depends(get_auth_session),
) -> APIUser:

    try:
        # Decode the JWT token and validate its signature/expiry
        # according to the decode_access_token implementation.
        payload = decode_access_token(token)

        # Verify that the JWT is an access token.
        # Reject refresh tokens or other token types.
        if payload.get("type") != "access":
            raise unauthorized()

        # Extract the user ID from the JWT subject (sub) claim.
        # Convert it to an integer for database lookup.
        user_id = int(payload["sub"])

    # Handle invalid JWT, missing user ID, or conversion errors.
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized()

    # Retrieve the user from the database using the user ID.
    user = await session.get(APIUser, user_id)

    # Reject the request if:
    # 1. The user does not exist.
    # 2. The user account is inactive.
    if user is None or not user.is_active:
        raise unauthorized()

    # Authentication successful.
    # Return the authenticated user object.
    return user


# Check whether the authenticated user is allowed
# to access a specific customer's information.
async def require_customer_access(
    # Customer ID requested by the API caller.
    customer_id: str,

    # Authenticated user returned by get_current_user.
    user: APIUser,

    # Asynchronous database session.
    session: AsyncSession,
) -> None:

    # Construct a query to check whether a mapping exists
    # between the authenticated user and requested customer.
    stmt = select(CustomerAccess.user_id).where(
        # Match the currently authenticated user's ID.
        CustomerAccess.user_id == user.id,

        # Match the requested customer ID.
        CustomerAccess.customer_id == customer_id,
    )

    # Execute the SQL query asynchronously.
    result = await session.execute(stmt)

    # Check whether an authorized user-customer mapping exists.
    if result.scalar_one_or_none() is None:

        # HTTP 403 means the user is authenticated
        # but does not have permission to access this customer.
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this customer",
        )

    # Access is permitted when the mapping exists.
    # No return value is required.
