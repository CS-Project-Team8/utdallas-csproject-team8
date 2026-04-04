from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_current_user
from app.firebase_admin_setup import db
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def verify_postgres_studio_exists(postgres_studio_id: str, postgres_db: Session) -> str:
    result = postgres_db.execute(
        text(
            """
            SELECT studioid
            FROM studios
            WHERE studioid = :studioid
            LIMIT 1
            """
        ),
        {"studioid": postgres_studio_id},
    )

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No matching Postgres studio found for this membership.",
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
    postgres_studio_id = membership_data.get("postgresStudioId")

    if not postgres_studio_id:
        raise HTTPException(
            status_code=400,
            detail="Membership is missing postgresStudioId.",
        )

    verified_studio_id = verify_postgres_studio_exists(postgres_studio_id, postgres_db)

    return {
        "ok": True,
        "uid": uid,
        "email": current_user.get("email"),
        "studioId": verified_studio_id,
        "role": membership_data.get("role"),
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
    postgres_studio_id = membership_data.get("postgresStudioId")

    if not postgres_studio_id:
        raise HTTPException(
            status_code=400,
            detail="Membership is missing postgresStudioId.",
        )

    verified_studio_id = verify_postgres_studio_exists(postgres_studio_id, postgres_db)

    return {
        "ok": True,
        "uid": uid,
        "email": current_user.get("email"),
        "studioId": verified_studio_id,
        "role": membership_data.get("role"),
    }