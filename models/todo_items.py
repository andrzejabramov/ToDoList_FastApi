from typing import List, Optional
from sqlalchemy import false, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .base import Base


class TodoItem(Base):
    __tablename__ = 'todo_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(50))
    done: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
    )

    def __str__(self):
        return self.text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, text={self.text!r})"