import bcrypt
bcrypt.__about__ = bcrypt

# hash_password.py
from passlib.context import CryptContext

# This context must match the one in app/data.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The password you want to hash
plain_password = "password456"

hashed_password = pwd_context.hash(plain_password)

print(f"Plain password: {plain_password}")
print(f"Hashed password: {hashed_password}")
