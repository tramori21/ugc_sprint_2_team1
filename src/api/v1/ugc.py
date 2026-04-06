from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from db.mongo import get_database
from models.schemas import (
    BookmarkCreate,
    BookmarkOut,
    LikeCreate,
    LikeOut,
    ReviewCreate,
    ReviewOut,
    ReviewUpdate,
)
from models.user import User
from services.ugc_service import UGCService

router = APIRouter()


@router.post('/bookmarks', response_model=BookmarkOut, status_code=HTTPStatus.CREATED)
async def create_bookmark(
    payload: BookmarkCreate,
    user: User = Depends(get_current_user),
):
    document = await UGCService.upsert_bookmark(get_database(), str(user.id), payload.movie_id)
    return BookmarkOut(**document)


@router.get('/bookmarks', response_model=list[BookmarkOut])
async def list_bookmarks(
    user: User = Depends(get_current_user),
):
    items = await UGCService.list_bookmarks(get_database(), str(user.id))
    return [BookmarkOut(**item) for item in items]


@router.get('/bookmarks/{movie_id}', response_model=BookmarkOut)
async def get_bookmark(
    movie_id: str,
    user: User = Depends(get_current_user),
):
    document = await UGCService.get_bookmark(get_database(), str(user.id), movie_id)
    if not document:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='bookmark not found')
    return BookmarkOut(**document)


@router.delete('/bookmarks/{movie_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_bookmark(
    movie_id: str,
    user: User = Depends(get_current_user),
):
    deleted = await UGCService.delete_bookmark(get_database(), str(user.id), movie_id)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='bookmark not found')
    return


@router.post('/likes', response_model=LikeOut, status_code=HTTPStatus.CREATED)
async def create_like(
    payload: LikeCreate,
    user: User = Depends(get_current_user),
):
    document = await UGCService.upsert_like(get_database(), str(user.id), payload.movie_id)
    return LikeOut(**document)


@router.get('/likes', response_model=list[LikeOut])
async def list_likes(
    user: User = Depends(get_current_user),
):
    items = await UGCService.list_likes(get_database(), str(user.id))
    return [LikeOut(**item) for item in items]


@router.get('/likes/{movie_id}', response_model=LikeOut)
async def get_like(
    movie_id: str,
    user: User = Depends(get_current_user),
):
    document = await UGCService.get_like(get_database(), str(user.id), movie_id)
    if not document:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='like not found')
    return LikeOut(**document)


@router.put('/likes/{movie_id}', response_model=LikeOut)
async def update_like(
    movie_id: str,
    user: User = Depends(get_current_user),
):
    document = await UGCService.upsert_like(get_database(), str(user.id), movie_id)
    return LikeOut(**document)


@router.delete('/likes/{movie_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_like(
    movie_id: str,
    user: User = Depends(get_current_user),
):
    deleted = await UGCService.delete_like(get_database(), str(user.id), movie_id)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='like not found')
    return


@router.post('/reviews', response_model=ReviewOut, status_code=HTTPStatus.CREATED)
async def create_review(
    payload: ReviewCreate,
    user: User = Depends(get_current_user),
):
    document = await UGCService.create_review(
        get_database(),
        str(user.id),
        payload.movie_id,
        payload.text,
        payload.rating,
    )
    return ReviewOut(**document)


@router.get('/reviews', response_model=list[ReviewOut])
async def list_reviews(
    movie_id: str | None = Query(default=None),
    user: User = Depends(get_current_user),
):
    items = await UGCService.list_reviews(get_database(), str(user.id), movie_id)
    return [ReviewOut(**item) for item in items]


@router.get('/reviews/{review_id}', response_model=ReviewOut)
async def get_review(
    review_id: str,
    user: User = Depends(get_current_user),
):
    document = await UGCService.get_review(get_database(), str(user.id), review_id)
    if not document:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='review not found')
    return ReviewOut(**document)


@router.put('/reviews/{review_id}', response_model=ReviewOut)
async def update_review(
    review_id: str,
    payload: ReviewUpdate,
    user: User = Depends(get_current_user),
):
    document = await UGCService.update_review(
        get_database(),
        str(user.id),
        review_id,
        payload.text,
        payload.rating,
    )
    if not document:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='review not found')
    return ReviewOut(**document)


@router.delete('/reviews/{review_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_review(
    review_id: str,
    user: User = Depends(get_current_user),
):
    deleted = await UGCService.delete_review(get_database(), str(user.id), review_id)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='review not found')
    return
