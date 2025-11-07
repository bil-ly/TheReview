from fastapi import FastAPI
from app.api.v1 import reviews

app = FastAPI()

app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
