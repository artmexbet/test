import datetime
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, orm
from .db_session import SqlAlchemyBase


class Friend(SqlAlchemyBase):
    __tablename__ = "friendship"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    proteins = Column(Float)
    fat = Column(Float)
    carbohydrates = Column(Float)
    fibers = Column(Float)
    calories = Column(Float)
    sugar = Column(Float)
    eat_time = Column(String)
    grams = Column(Integer)
    modified_date = Column(Date, default=datetime.datetime.now().date)
    user = orm.relation("User")
