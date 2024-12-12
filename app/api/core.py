from fastapi import APIRouter, HTTPException, Path

router = APIRouter()


@router.get("/")
async def evaluate():
    return {"status": "success"}
