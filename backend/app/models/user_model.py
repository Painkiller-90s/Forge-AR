from datetime import datetime, timezone


def user_document(
    name: str,
    email: str,
    password_hash: str,
    role: str,
    label_id: str | None = None
):
    return {
        "name": name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "role": role,
        "label_id": label_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }