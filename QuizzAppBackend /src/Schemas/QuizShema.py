from enum import Enum

from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import Update
from typing import Union, List


# Enums
class QuestionType(str, Enum):
    single = "single"
    multiple = "multiple"
    text = "text"


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=15)


class UserRead(UserBase):
    id: int
    total_score: int

    class Config:
        from_attributes = True


# Quiz Schemas
class QuizBase(BaseModel):
    title: str
    description: str | None = None


class QuizCreate(QuizBase):
    # creator_id: int
    pass


class QuizRead(QuizBase):
    id: int
    creator_id: int

    class Config:
        from_attributes  = True


# Question Schemas
class QuestionBase(BaseModel):
    text: str
    type: QuestionType
    points: int


class QuestionCreate(QuestionBase):
    pass
    quiz_id: int


class QuestionRead(QuestionBase):
    id: int
    quiz_id: int

    class Config:
        from_attributes  = True


# Answer Schemas
class AnswerBase(BaseModel):
    text: str
    is_correct: bool


class AnswerCreate(AnswerBase):
    question_id: int


class AnswerRead(AnswerBase):
    id: int
    question_id: int

    class Config:
        from_attributes  = True


# Tag Schemas
class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int
    name: str
    class Config:
        from_attributes  = True


class UserAnswerCreate(BaseModel):
    question_id: int
    answer_text: str| None = None
    selected_answer_ids:  List[int] | None   = None

class QuizAttemptCreate(BaseModel):
    answers: List[UserAnswerCreate]

class UserAnswerRead(BaseModel):
    question_id: int
    answer_text: str | None
    selected_answer_ids: List[int] | None
    is_correct: bool
    points_awarded: int

class QuizAttemptResult(BaseModel):
    attempt_id: int
    score: int
    max_score: int
    answers: List[UserAnswerRead]