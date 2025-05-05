from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.CRUD.userCRUD import router as user_router
from src.DatabaseManager.queries import  router as db_router
from src.CRUD.quizCRUD import router as quiz_router
from src.CRUD.userAttemptsCRUD import router as user_attempts_router
app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(db_router)
app.include_router(user_router)
app.include_router(quiz_router)

app.include_router(user_attempts_router)


@app.get("/")
def root():
    return {"message": "It works!"}

