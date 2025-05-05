from fastapi import HTTPException, Depends, APIRouter, Request, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from src.DatabaseManager.queries import get_session
from src.Schemas.QuizShema import QuizCreate, QuestionCreate, AnswerCreate, QuizRead, QuestionRead, AnswerRead, \
    QuestionBase, TagRead, TagCreate, AnswerBase
from src.Models.models import Quiz, Question, Answer, Tag
from src.CRUD.userCRUD import get_current_user_from_cookie, get_current_user_id_from_cookie

router = APIRouter()


def get_current_uid(request: Request):
    return Depends(lambda: get_current_user_from_cookie(request))



@router.post("/quiz/create")
async def create_quiz(
    data: QuizCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    quiz = Quiz(
        title=data.title,
        description=data.description,
        creator_id=user_id,
    )
    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)
    return {"quiz_id": quiz.id}

@router.get("/quizzes")
async def get_quizzes(
    search: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Quiz)

    if search:
        stmt = stmt.where(Quiz.title.ilike(f"%{search}%"))

    if tag:
        stmt = stmt.join(Quiz.tags).where(Tag.name == tag)

    # Фикс: считаем уникальные Quiz.id
    total_stmt = select(func.count(distinct(Quiz.id)))
    if search or tag:
        total_stmt = total_stmt.select_from(stmt.subquery())

    total = await session.scalar(total_stmt)

    # Пагинация
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    quizzes = result.scalars().all()

    return {"quizzes": quizzes, "total": total}

@router.get("/quiz/{quiz_id}", response_model=QuizRead)
async def get_quiz(
    quiz_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.patch("/quiz/{quiz_id}")
async def update_quiz(
    quiz_id: int,
    data: QuizCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)  # ✅ use correct dependency
):
    result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in data.dict().items():
        setattr(quiz, key, value)

    await session.commit()
    return {"message": "Quiz updated"}


@router.delete("/quiz/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await session.delete(quiz)
    await session.commit()
    return {"message": "Quiz deleted"}

@router.post("/question", response_model=QuestionRead)
async def create_question(
    data: QuestionCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Quiz).where(Quiz.id == data.quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    question = Question(**data.dict())
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return question


@router.get("/question/{question_id}", response_model=QuestionRead)
async def get_question(
    question_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.patch("/question/{question_id}")
async def update_question(
    question_id: int,
    data: QuestionBase,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    quiz_result = await session.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in data.dict().items():
        setattr(question, key, value)

    await session.commit()
    return {"message": "Question updated"}


@router.delete("/question/{question_id}")
async def delete_question(
    question_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    quiz_result = await session.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await session.delete(question)
    await session.commit()
    return {"message": "Question deleted"}


@router.post("/answers", response_model=AnswerRead)
async def create_answer(
    data: AnswerCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    question_result = await session.execute(select(Question).where(Question.id == data.question_id))
    question = question_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    quiz_result = await session.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    answer = Answer(**data.dict())
    session.add(answer)
    await session.commit()
    await session.refresh(answer)
    return answer

@router.get("/answers/{answer_id}", response_model=AnswerRead)
async def get_answer(
    answer_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Answer).where(Answer.id == answer_id))
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer


@router.patch("/answers/{answer_id}", response_model=AnswerRead)
async def update_answer(
    answer_id: int,
    data: AnswerBase,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Answer).where(Answer.id == answer_id))
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    question_result = await session.execute(select(Question).where(Question.id == answer.question_id))
    question = question_result.scalar_one_or_none()

    quiz_result = await session.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in data.dict().items():
        setattr(answer, key, value)

    await session.commit()
    await session.refresh(answer)
    return answer

@router.delete("/answers/{answer_id}")
async def delete_answer(
    answer_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Answer).where(Answer.id == answer_id))
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    question_result = await session.execute(select(Question).where(Question.id == answer.question_id))
    question = question_result.scalar_one_or_none()
    quiz_result = await session.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if not quiz or quiz.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await session.delete(answer)
    await session.commit()
    return {"message": "Answer deleted successfully"}

@router.post("/tags", response_model=TagRead)
async def create_tag(
    data: TagCreate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Tag).where(Tag.name == data.name))
    existing_tag = result.scalar_one_or_none()

    if existing_tag:
        return existing_tag

    tag = Tag(name=data.name)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag

@router.get("/tags", response_model=list[TagRead])
async def get_all_tags(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Tag))
    return result.scalars().all()


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
        tag_id: int,
        data: TagCreate,
        session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag.name = data.name
    await session.commit()
    await session.refresh(tag)
    return tag


@router.post("/quiz/{quiz_id}/add-tag", response_model=TagRead)
async def add_tag_to_quiz(
    quiz_id: int,
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_session)
):
    tag_result = await session.execute(select(Tag).where(Tag.name == tag_data.name))
    tag = tag_result.scalar_one_or_none()

    if not tag:
        tag = Tag(name=tag_data.name)
        session.add(tag)
        await session.flush()  # нужен до commit'а

    quiz_result = await session.execute(
        select(Quiz).options(selectinload(Quiz.tags)).where(Quiz.id == quiz_id)
    )
    quiz = quiz_result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if all(existing_tag.id != tag.id for existing_tag in quiz.tags):
        quiz.tags.append(tag)

    await session.commit()
    await session.refresh(tag)

    return TagRead.model_validate(tag)


@router.get("/quiz/{quiz_id}/tags", response_model=list[TagRead])
async def get_tags_by_quiz_id(
    quiz_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Quiz).options(selectinload(Quiz.tags)).where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz.tags

@router.get("/tags/search", response_model=list[QuizRead])
async def search_quizzes_by_tag_name(
    query: str,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Quiz)
        .join(Quiz.tags)
        .options(selectinload(Quiz.tags))
        .where(Tag.name.ilike(f"{query}%"))
        .distinct()
    )
    quizzes = result.scalars().all()
    return quizzes

@router.get("/quiz/{quiz_id}/questions", response_model=list[QuestionRead])
async def get_questions_by_quiz_id(
    quiz_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)  # проверка авторизации
):
    result = await session.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = result.scalars().all()
    return questions


@router.get("/question/{question_id}/answers", response_model=list[AnswerRead])
async def get_answers_by_question_id(
    question_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)  # проверка авторизации
):
    result = await session.execute(select(Answer).where(Answer.question_id == question_id))
    answers = result.scalars().all()
    return answers
