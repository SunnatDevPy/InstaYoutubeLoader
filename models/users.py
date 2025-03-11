from sqlalchemy import BigInteger, Text, JSON, ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from models.database import BaseModel


class User(BaseModel):
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)

    def __str__(self):
        return super().__str__() + f" - {self.username}"
