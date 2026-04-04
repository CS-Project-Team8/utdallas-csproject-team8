from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.firebase_admin_setup import firebase_auth, db
from app.db.session import get_db


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


async def verify_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split("Bearer ")[1]

    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def verify_admin(
    authorization: str = Header(...),
    postgres_db: Session = Depends(get_db),
):
    decoded = await verify_user(authorization)
    uid = decoded["uid"]

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

    membership = membership_docs[0].to_dict()
    postgres_studio_id = membership.get("postgresStudioId")

    if not postgres_studio_id:
        raise HTTPException(
            status_code=400,
            detail="Membership is missing postgresStudioId.",
        )

    verified_studio_id = verify_postgres_studio_exists(postgres_studio_id, postgres_db)

    return {
        "uid": uid,
        "email": decoded.get("email"),
        "studioId": verified_studio_id,
        "membership": membership,
    }