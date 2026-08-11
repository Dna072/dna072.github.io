from fastapi import APIRouter, Depends
from renderflow_common.models import Worker
from renderflow_common.schemas import WorkerList
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


@router.get("", response_model=WorkerList)
def list_workers(db: Session = Depends(get_db)):
    """Worker registry, kept fresh by each worker's heartbeat thread writing
    directly to the `workers` table (see `worker/worker/heartbeat.py`)."""
    items = list(db.scalars(select(Worker).order_by(Worker.last_heartbeat.desc())).all())
    return WorkerList(items=items, total=len(items))
