from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import auth as firebase_auth_module
from firebase_admin import firestore
from app.dependencies import get_current_user
from app.firebase_admin_setup import db, firebase_auth
from app.schemas.admin import InviteCreateRequest, InviteAcceptRequest
from app.utils import generate_invite_token, hash_token, utc_plus_hours, utc_now
from app.email_service import send_invite_email
from app.config import FRONTEND_URL

router = APIRouter(prefix="/invites", tags=["invites"])
@router.post("")
async def create_invite(payload: InviteCreateRequest, current_user=Depends(get_current_user)):
    uid = current_user["uid"]
    inviter_email = current_user.get("email")
    normalized_email = payload.email.strip().lower()

    memberships = (
        db.collection("studio_memberships")
        .where("firebaseUid", "==", uid)
        .where("role", "==", "admin")
        .where("status", "==", "active")
        .limit(1)
        .stream()
    )
    membership_docs = list(memberships)

    if not membership_docs:
        raise HTTPException(status_code=403, detail="Only admins can send invites")

    membership_data = membership_docs[0].to_dict()
    postgres_studio_id = membership_data["postgresStudioId"]

    existing_invites = (
        db.collection("invitations")
        .where("email", "==", normalized_email)
        .where("postgresStudioId", "==", postgres_studio_id)
        .where("status", "in", ["sent", "pending"])
        .limit(1)
        .stream()
    )
    existing_docs = list(existing_invites)

    if existing_docs:
        raise HTTPException(status_code=409, detail="An active invite already exists for this email")

    token = generate_invite_token()
    token_hash = hash_token(token)
    expires_at = utc_plus_hours(24)

    invite_ref = db.collection("invitations").document()

    invite_ref.set({
        "email": normalized_email,
        "postgresStudioId": postgres_studio_id,
        "role": payload.role,
        "invitedByUid": uid,
        "status": "sent",
        "tokenHash": token_hash,
        "expiresAt": expires_at,
        "acceptedAt": None,
        "acceptedByUid": None,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })

    invite_link = f"{FRONTEND_URL}/admin/acceptInvite?token={token}&email={normalized_email}"

    send_invite_email(
        to_email=normalized_email,
        invite_link=invite_link,
        role=payload.role,
        studio_id=postgres_studio_id
    )

    db.collection("audit_logs").document().set({
        "action": "invite_sent",
        "actorUid": uid,
        "actorEmail": inviter_email,
        "postgresStudioId": postgres_studio_id,
        "targetEmail": normalized_email,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })

    return {
        "ok": True,
        "detail": "Invite sent successfully"
    }
    
@router.get("/validate")
async def validate_invite(token: str = Query(...), email: str = Query(...)):
    normalized_email = email.strip().lower()
    token_hash = hash_token(token)

    invites = (
        db.collection("invitations")
        .where("email", "==", normalized_email)
        .where("tokenHash", "==", token_hash)
        .where("status", "==", "sent")
        .limit(1)
        .stream()
    )
    invite_docs = list(invites)

    if not invite_docs:
        raise HTTPException(status_code=404, detail="Invalid invite")

    invite_doc = invite_docs[0]
    invite_data = invite_doc.to_dict()

    expires_at = invite_data.get("expiresAt")
    if expires_at is None:
        raise HTTPException(status_code=400, detail="Invite is missing expiration")

    if expires_at < utc_now():
        raise HTTPException(status_code=410, detail="Invite has expired")

    return {
        "ok": True,
        "email": invite_data["email"],
        "role": invite_data["role"],
        "postgresStudioId": invite_data["postgresStudioId"],
    }
    
@router.post("/accept")
async def accept_invite(payload: InviteAcceptRequest):
    normalized_email = payload.email.strip().lower()
    token_hash = hash_token(payload.token)

    invites = (
        db.collection("invitations")
        .where("email", "==", normalized_email)
        .where("tokenHash", "==", token_hash)
        .where("status", "==", "sent")
        .limit(1)
        .stream()
    )
    invite_docs = list(invites)

    if not invite_docs:
        raise HTTPException(status_code=404, detail="Invite not found or already used")

    invite_doc = invite_docs[0]
    invite_data = invite_doc.to_dict()

    expires_at = invite_data.get("expiresAt")
    if expires_at is None or expires_at < utc_now():
        raise HTTPException(status_code=410, detail="Invite has expired")

    try:
        existing_user = firebase_auth.get_user_by_email(normalized_email)
        user_record = existing_user
    except firebase_auth_module.UserNotFoundError:
        user_record = firebase_auth.create_user(
            email=normalized_email,
            password=payload.password,
            display_name=payload.display_name
        )

    uid = user_record.uid

    db.collection("users").document(uid).set({
        "email": normalized_email,
        "displayName": payload.display_name,
        "status": "active",
        "createdAt": firestore.SERVER_TIMESTAMP,
        "lastLoginAt": None,
    }, merge=True)

    membership_doc_id = f"{invite_data['postgresStudioId']}_{uid}"

    db.collection("studio_memberships").document(membership_doc_id).set({
    "postgresStudioId": invite_data["postgresStudioId"],
        "firebaseUid": uid,
        "email": normalized_email,
        "role": invite_data["role"],
        "status": "active",
        "invitedByUid": invite_data["invitedByUid"],
        "joinedAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    invite_doc.reference.update({
        "status": "accepted",
        "acceptedAt": firestore.SERVER_TIMESTAMP,
        "acceptedByUid": uid,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })

    db.collection("audit_logs").document().set({
        "action": "invite_accepted",
        "actorUid": uid,
        "postgresStudioId": invite_data["postgresStudioId"],
        "targetEmail": normalized_email,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })

    return {
        "ok": True,
        "detail": "Invite accepted successfully",
        "uid": uid,
    }