from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, comment="主键ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新时间")
    company_id = Column(Integer, nullable=True, comment="公司ID")
    company_name = Column(String(100), nullable=True, comment="公司名称")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    user_name = Column(String(100), nullable=True, comment="用户名")
    events = Column(MySQLJSON, nullable=False, comment="事件内容")
    payload = Column(MySQLJSON, nullable=True, comment="附加数据")
    request_id = Column(String(50), nullable=False, comment="请求ID，前端生成并保存至localstorage")