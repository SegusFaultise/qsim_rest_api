from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import Token
from ..data import get_user
from ..security import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    <summary>
    Authenticates a user based on a username and password provided in a form.
    If the credentials are valid, it generates and returns a JWT access token.
    </summary>
    <param name="form_data" type="OAuth2PasswordRequestForm">
    An OAuth2-compliant form containing the user's username and password.
    FastAPI injects this dependency automatically from the request body.
    </param>
    <returns type="Token">
    A Pydantic schema object containing the generated access_token and its type ('bearer').
    </returns>
    <exception cref="HTTPException">
    Raises a 401 Unauthorized exception if the provided username does not exist
    or if the password does not match the stored hash.
    </exception>
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
