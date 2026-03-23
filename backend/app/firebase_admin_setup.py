import firebase_admin
from firebase_admin import credentials, auth, firestore
from app.config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_PRIVATE_KEY,
)

_firestore_client = None


def _build_credential():
    private_key = FIREBASE_PRIVATE_KEY
    if private_key:
        private_key = private_key.replace("\\n", "\n")

    if not FIREBASE_PROJECT_ID or not FIREBASE_CLIENT_EMAIL or not private_key:
        raise RuntimeError("Firebase Admin credentials are not fully configured")

    return credentials.Certificate({
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "client_email": FIREBASE_CLIENT_EMAIL,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    })


def _ensure_initialized():
    global _firestore_client

    if not firebase_admin._apps:
        cred = _build_credential()
        firebase_admin.initialize_app(cred)

    if _firestore_client is None:
        _firestore_client = firestore.client()


class _LazyFirebaseAuth:
    def __getattr__(self, name):
        _ensure_initialized()
        return getattr(auth, name)


class _LazyFirestoreClient:
    def __getattr__(self, name):
        _ensure_initialized()
        return getattr(_firestore_client, name)


firebase_auth = _LazyFirebaseAuth()
db = _LazyFirestoreClient()