from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_reviews():
    return [{"review": "This is a great product!"}, {"review": "This is a terrible product!"}]
