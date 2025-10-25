from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List

from app.db_utils import create_seat_hold, release_seat_hold
from app.core.security import decode_token

router = APIRouter()


def get_current_user(authorization: str = Header(None)):
    """Extract and validate user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload


class SeatHoldRequest(BaseModel):
    train_run_id: int
    seat_ids: List[int]
    hold_seconds: int = 120


@router.post("/")
def create_hold(req: SeatHoldRequest, user = Depends(get_current_user)):
    """Create a temporary hold on seats."""
    user_id = user.get("user_id")
    try:
        result = create_seat_hold(user_id, req.train_run_id, req.seat_ids, req.hold_seconds)
        return result
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{hold_id}")
def delete_hold(hold_id: int, user = Depends(get_current_user)):
    """Release a seat hold."""
    # In production, should validate ownership
    release_seat_hold(hold_id)
    return {"status": "released"}
