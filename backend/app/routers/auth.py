from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.firebase_admin_setup import db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin-login-check")
async def admin_login_check(current_user=Depends(get_current_user)):
    uid = current_user["uid"]

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
        raise HTTPException(status_code=403, detail="You are not authorized as admin.")

    membership_data = membership_docs[0].to_dict()

    return {
        "ok": True,
        "uid": uid,
        "email": current_user.get("email"),
        "studioId": membership_data.get("studioId"),
        "role": membership_data.get("role"),
    }