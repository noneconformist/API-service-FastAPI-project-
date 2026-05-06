from passlib.context import CryptContext

# Create a context for hashing passwords using bcrypt.
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
