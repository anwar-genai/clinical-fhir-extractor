from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ExtractionResponse, ExtractionListItem
from ..models import Extraction
from ..auth import get_current_active_user
from ..models import User

router = APIRouter(prefix="/extractions", tags=["extractions"])


@router.get("/", response_model=List[ExtractionListItem])
def list_extractions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items = (
        db.query(Extraction)
        .filter(Extraction.user_id == current_user.id)
        .order_by(Extraction.id.desc())
        .all()
    )
    return items


@router.get("/{extraction_id}", response_model=ExtractionResponse)
def get_extraction(
    extraction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    return item


@router.delete("/{extraction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_extraction(
    extraction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    db.delete(item)
    db.commit()
    return None


