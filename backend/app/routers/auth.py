from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_current_user
from app.firebase_admin_setup import db
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def get_postgres_studio_uuid(firebase_studio_id: int, postgres_db: Session) -> str:
    result = postgres_db.execute(
        text(
            """
            SELECT studioid
            FROM studios
            WHERE firebase_studio_id = :firebase_studio_id
                LIMIT 1
            """
        ),
        {"firebase_studio_id": firebase_studio_id},
    )

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No matching Postgres studio found for this Firebase studioId.",
        )

    return str(row.studioid)


@router.post("/admin-login-check")
async def admin_login_check(
        current_user=Depends(get_current_user),
        postgres_db: Session = Depends(get_db),
):
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
    firebase_studio_id = membership_data.get("studioId")

    if firebase_studio_id is None:
        raise HTTPException(status_code=400, detail="Membership is missing studioId.")

    postgres_studio_id = get_postgres_studio_uuid(firebase_studio_id, postgres_db)

    return {
        "ok": True,
        "uid": uid,
        "email": current_user.get("email"),
        "studioId": postgres_studio_id,
        "role": membership_data.get("role"),
        "firebaseStudioId": firebase_studio_id,
    }


@router.post("/user-login-check")
async def user_login_check(
        current_user=Depends(get_current_user),
        postgres_db: Session = Depends(get_db),
):
    uid = current_user["uid"]

    memberships = (
        db.collection("studio_memberships")
        .where("firebaseUid", "==", uid)
        .where("status", "==", "active")
        .limit(1)
        .stream()
    )

    membership_docs = list(memberships)

    if not membership_docs:
        raise HTTPException(status_code=403, detail="No active studio membership found.")

    membership_data = membership_docs[0].to_dict()
    firebase_studio_id = membership_data.get("studioId")

    if firebase_studio_id is None:
        raise HTTPException(status_code=400, detail="Membership is missing studioId.")

    postgres_studio_id = get_postgres_studio_uuid(firebase_studio_id, postgres_db)

    return {
        "ok": True,
        "uid": uid,
        "email": current_user.get("email"),
        "studioId": postgres_studio_id,
        "role": membership_data.get("role"),
        "firebaseStudioId": firebase_studio_id,
    }