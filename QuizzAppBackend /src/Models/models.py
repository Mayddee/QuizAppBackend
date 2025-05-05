from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Annotated

from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, Table, Enum, JSON, Column
)
import enum

intpk = Annotated[int, mapped_column(primary_key=True)]
class Base(DeclarativeBase):
    pass



class QuestionType(enum.Enum):
    single = "single"
    multiple = "multiple"
    text = "text"


#
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    total_score: Mapped[int] = mapped_column(default=0)

    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="creator", lazy="selectin"
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user", lazy="selectin"
    )

# Квиз
class Quiz(Base):
    __tablename__ = 'quizzes'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    creator: Mapped["User"] = relationship(
        back_populates="quizzes", lazy="selectin"
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="quiz_tags", back_populates="quizzes", lazy="selectin"
    )

# Вопрос
class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    text: Mapped[str] = mapped_column(String)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    points: Mapped[int] = mapped_column()

    quiz: Mapped["Quiz"] = relationship(
        back_populates="questions", lazy="selectin"
    )
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", lazy="selectin"
    )

class Answer(Base):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String)
    is_correct: Mapped[bool] = mapped_column(Boolean)

    question: Mapped["Question"] = relationship(
        back_populates="answers", lazy="selectin"
    )

# Тег
class Tag(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    quizzes: Mapped[list["Quiz"]] = relationship(
        secondary="quiz_tags", back_populates="tags", lazy="selectin"
    )

# "quiz_tags"
quiz_tags = Table(
    "quiz_tags",
    Base.metadata,
    Column("quiz_id", ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

# Попытка прохождения квиза
class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    score: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(
        back_populates="attempts", lazy="selectin"
    )
    answers: Mapped[list["UserAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete", lazy="selectin"
    )

# Ответ пользователя на вопрос
class UserAnswer(Base):
    __tablename__ = 'user_answers'

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(String, nullable=True)  # только для текстовых
    selected_answer_ids: Mapped[list[int]] = mapped_column(JSON, nullable=True)  # для single/multiple

    attempt: Mapped["QuizAttempt"] = relationship(
        back_populates="answers", lazy="selectin"
    )

