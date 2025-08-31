import bcrypt
bcrypt.__about__ = bcrypt

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .schemas import TokenData, User
from .data import get_user

# --- Configuration ---
"""
<summary>
Defines security-related configuration constants for JWT (JSON Web Token) creation and validation.
IMPORTANT: In a real production application, the SECRET_KEY should be loaded securely from an
environment variable or a secrets management service, not hardcoded.
</summary>
"""
SECRET_KEY = "a_very_secret_key_that_should_be_long_and_random"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Dependencies & Helpers ---
"""
<summary>
Initializes the password hashing context using passlib and the OAuth2 password flow scheme.
</summary>
"""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password):
    """
    <summary>
    Verifies a plain-text password against a stored bcrypt hash.
    </summary>
    <param name="plain_password" type="str">The plain-text password to verify.</param>
    <param name="hashed_password" type="str">The securely hashed password from the database.</param>
    <returns type="bool">True if the password matches the hash, False otherwise.</returns>
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """
    <summary>
    Creates a new JWT access token.
    </summary>
    <param name="data" type="dict">The data (payload) to encode in the token, typically containing the user identifier ('sub').</param>
    <returns type="str">The encoded JWT as a string.</returns>
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- The Main Security Dependency ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    <summary>
    A FastAPI dependency that validates a JWT token from the request's Authorization header
    and returns the corresponding user object. This is the primary mechanism for protecting API endpoints.
    </summary>
    <param name="token" type="str">The bearer token extracted from the request, injected by FastAPI's dependency system.</param>
    <returns type="User">
    A Pydantic User model instance for the authenticated user. This model excludes sensitive
    data like the hashed password.
    </returns>
    <exception cref="HTTPException">
    Raises a 401 Unauthorized exception if the token is missing, malformed, expired,
    or does not correspond to a valid user.
    </exception>
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    # Return a User model, not UserInDB (don't expose the hashed password)
    return User(username=user.username, max_qubits=user.max_qubits)
