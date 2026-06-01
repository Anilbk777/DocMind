import re
from pydantic import BaseModel, Field, EmailStr, field_validator
from app.core.llm_strategies import LLMProvider


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        description="The question or prompt you want the RAG system to answer.",
        min_length=1,
    )
    provider: LLMProvider = Field(
        ..., description="Select your preferred LLM engine from the dropdown menu."
    )


class DocumentResponse(BaseModel):
    file_name: str
    storage_uri: str


class UserRegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique display name for the user account",
    )

    email: EmailStr = Field(
        ...,
        description="Valid user email, auto-validated and cleaned",
        max_length=100,
    )

    password: str = Field(
        ...,
        description="Raw password string adhering to security constraints",
        max_length=255,
        min_length=8,
    )

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def pre_strip_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one numerical digit (0-9)."
            )

        # Regex scans for standard special punctuation symbols
        special_char_regex = re.compile(r"[!@#$%^&*(),.?\":{}|<>_+\-=~`[\]\\]")
        if not special_char_regex.search(value):
            raise ValueError("Password must contain at least one special character.")

        return value


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., strip_whitespace=True)

    @field_validator("email", mode="before")
    @classmethod
    def strip_login_email(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class Token(BaseModel):
    access_token:str
    token_type:str