import firebase_admin
from firebase_admin import credentials, auth, firestore
from app.config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_PRIVATE_KEY,
)

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "client_email": FIREBASE_CLIENT_EMAIL,
        "private_key": FIREBASE_PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    })
    firebase_admin.initialize_app(cred)

firebase_auth = auth
db = firestore.client()