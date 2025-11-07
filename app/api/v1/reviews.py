from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

@router.get("/")
def read_reviews():
    return [{"review": "This is a great product!"}, {"review": "This is a terrible product!"}]
