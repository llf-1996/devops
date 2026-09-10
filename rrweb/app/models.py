from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RrwebSession(Base):
    """录屏会话（一次录制一条记录）。"""

    __tablename__ = "rrweb_sessions"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "company_id",
            "user_id",
            name="uq_rrweb_sessions_request_company_user",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, comment="主键ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="创建时间")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新时间"
    )
    request_id = Column(
        String(50), nullable=False, comment="请求ID，前端生成并保存至 sessionStorage"
    )
    company_id = Column(Integer, nullable=True, comment="公司ID")
    company_name = Column(String(100), nullable=True, comment="公司名称")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    user_name = Column(String(100), nullable=True, comment="用户名")
    record_type = Column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="录屏类型：1=采购订单录屏",
    )
    is_locked = Column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="是否锁定：1=锁定，禁止删除与清理",
    )
    payload = Column(MySQLJSON, nullable=True, comment="附加数据（含 order_plan_id 等）")


class RrwebEventDetail(Base):
    """录屏事件分片详情。"""

    __tablename__ = "rrweb_event_details"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "seq",
            name="uq_rrweb_event_details_session_seq",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, comment="主键ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="创建时间")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新时间"
    )
    session_id = Column(Integer, nullable=False, index=True, comment="所属会话ID")
    seq = Column(
        Integer,
        nullable=True,
        comment="同一会话内分片序号（前端单调递增；空则回放按 id）",
    )
    events = Column(MySQLJSON, nullable=False, comment="事件内容")
