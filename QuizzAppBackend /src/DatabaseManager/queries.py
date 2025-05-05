from fastapi import Depends, APIRouter

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated


from src.Models.models import Base, Quiz, QuestionType, Question, Answer

router = APIRouter()

engine = create_async_engine('sqlite+aiosqlite:///questions.db', echo=False)

new_session = async_sessionmaker(engine)

async def get_session() -> AsyncSession:
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def seed_data():
    async with new_session() as session:
        # Создание одного квиза
        quiz = Quiz(title="Science and Nature Quiz", description="Test your knowledge on science and nature.", creator_id=0)
        session.add(quiz)
        await session.flush()  # получить quiz.id

        # Список вопросов с данными ответов
        questions_data = [
            {
                "text": "What is the powerhouse of the cell?",
                "type": QuestionType.single,
                "points": 5,
                "answers": [
                    {"text": "Mitochondria", "is_correct": True},
                    {"text": "Nucleus", "is_correct": False},
                    {"text": "Ribosome", "is_correct": False},
                ]
            },
            {
                "text": "Which planet has the most moons?",
                "type": QuestionType.single,
                "points": 5,
                "answers": [
                    {"text": "Saturn", "is_correct": True},
                    {"text": "Jupiter", "is_correct": False},
                    {"text": "Jupiter", "is_correct": False},
                ]
            },
            {
                "text": "What gas do plants absorb from the atmosphere?",
                "type": QuestionType.single,
                "points": 5,
                "answers": [
                    {"text": "Carbon Dioxide", "is_correct": True},
                    {"text": "Oxygen", "is_correct": False},
                    {"text": "Nitrogen", "is_correct": False},
                ]
            },
            {
                "text": "What is H2O commonly known as?",
                "type": QuestionType.single,
                "points": 5,
                "answers": [
                    {"text": "Water", "is_correct": True},
                    {"text": "Salt", "is_correct": False},
                    {"text": "Sugar", "is_correct": False},
                ]
            },
            {
                "text": "How many bones are there in the adult human body?",
                "type": QuestionType.single,
                "points": 5,
                "answers": [
                    {"text": "206", "is_correct": True},
                    {"text": "201", "is_correct": False},
                    {"text": "210", "is_correct": False},
                ]
            },
        ]

        for q in questions_data:
            question = Question(
                text=q["text"],
                type=q["type"],
                points=q["points"],
                quiz_id=quiz.id
            )
            session.add(question)
            await session.flush()  # получить question.id

            for a in q["answers"]:
                answer = Answer(
                    text=a["text"],
                    is_correct=a["is_correct"],
                    question_id=question.id
                )
                session.add(answer)

        await session.commit()
        print("✔️ Seeded quiz, questions, and answers.")

# if __name__ == "__main__":
#     asyncio.run(seed_data())

@router.post("/setup_database")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"success": True}



