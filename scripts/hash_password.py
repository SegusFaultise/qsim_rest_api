import bcrypt
bcrypt.__about__ = bcrypt

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
plain_password = "password456"
hashed_password = pwd_context.hash(plain_password)

print(f"Plain password: {plain_password}")
print(f"Hashed password: {hashed_password}")
