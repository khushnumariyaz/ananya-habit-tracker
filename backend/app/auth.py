from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_user_id(
    user_id: int = Header(default=1, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> int:
    if user_id < 1:
        raise HTTPException(status_code=400, detail="X-User-ID must be a positive integer")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id
