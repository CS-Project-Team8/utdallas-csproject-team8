from fastapi import Header, HTTPException
from app.firebase_admin_setup import firebase_auth, db

async def verify_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split("Bearer ")[1]

    try:
        decoded = firebase_auth.verify_id_token(token)
        # uid = decoded["uid"]
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def verify_admin(authorization: str = Header(...)):
    decoded = await verify_user(authorization)
    uid = decoded["uid"]

    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="User profile not found")

    user_data = user_doc.to_dict()
    studio_id = user_data.get("studioId")

    membership_doc = db.collection("studio_memberships").document(f"{studio_id}_{uid}").get()
    if not membership_doc.exists:
        raise HTTPException(status_code=403, detail="Studio membership not found")

    membership = membership_doc.to_dict()
    if membership.get("role") != "admin" or membership.get("status") != "active":
        raise HTTPException(status_code=403, detail="Not an admin")

    return {
        "uid": uid,
        "user": user_data,
        "membership": membership
    }