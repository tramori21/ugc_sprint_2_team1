from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from services.kafka_producer import KafkaProducer

from api.deps import get_current_user_id, get_request_id
from models.schemas import UserActionIn, UserActionOut

router = APIRouter()


@router.post('', response_model=UserActionOut, status_code=status.HTTP_202_ACCEPTED)
async def create_event(
    payload: UserActionIn,
    user_id: str = Depends(get_current_user_id),
    request_id: str = Depends(get_request_id),
):
    event_id = str(uuid4())
    event_time = payload.event_time or datetime.now(timezone.utc)

    message = {
        'event_id': event_id,
        'user_id': user_id,
        'movie_id': payload.movie_id,
        'event_type': payload.event_type,
        'progress_seconds': payload.progress_seconds,
        'event_time': event_time.isoformat(),
        'request_id': request_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }

    await KafkaProducer.send(message)
    return UserActionOut(status='accepted', event_id=event_id)
