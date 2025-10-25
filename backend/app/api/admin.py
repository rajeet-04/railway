from fastapi import APIRouter, HTTPException, Depends

from app.core.security import decode_token

router = APIRouter()


@router.post("/import")
def run_import(payload: dict, token: str = Depends(decode_token)):
    # In a full implementation verify token is admin; here we assume decode_token returns claims
    if not token or not token.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin required")
    # Trigger import process (implementer should wire to scripts/import_data.py)
    return {"status": "started", "detail": "Import kicked off (stub)"}
