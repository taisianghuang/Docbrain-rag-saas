from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from sqlalchemy.orm import relationship
from enum import Enum
from llama_index.core.callbacks.schema import CBEventType
from app.models.base import Base
from pgvector.sqlalchemy import Vector


class MessageRoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageStatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class MessageSubProcessStatusEnum(str, Enum):
    PENDING = "PENDING"
    FINISHED = "FINISHED"


additional_message_subprocess_fields = {
    "CONSTRUCTED_QUERY_ENGINE": "constructed_query_engine",
    "SUB_QUESTIONS": "sub_questions",
}

MessageSubProcessSourceEnum = Enum(
    "MessageSubProcessSourceEnum",
    [(event_type.name, event_type.value) for event_type in CBEventType]
    + list(additional_message_subprocess_fields.items()),
)


def to_pg_enum(enum_class) -> ENUM:
    return ENUM(enum_class, name=enum_class.__name__)


class Document(Base):
    """
    RAG 知識庫文件。
    """
    __tablename__ = "document"

    # 綁定租戶 (重要!)
    client_id = Column(UUID(as_uuid=True), ForeignKey(
        "client.id"), nullable=False, index=True)

    # 文件原始名稱
    name = Column(String, nullable=True)

    # 儲存路徑或 URL
    url = Column(String, nullable=False)

    # 檔案雜湊值 (避免重複上傳)
    content_hash = Column(String, nullable=True)

    # LlamaIndex 解析後的 Metadata
    metadata_map = Column(JSONB, nullable=True)

    # 狀態: processing, indexed, error
    status = Column(String, default="processing")

    # 定義向量欄位 (這會對應到資料庫的 VECTOR 型別)
    embedding = Column(Vector(1536), nullable=True)

    conversations = relationship(
        "ConversationDocument", back_populates="document")
    client = relationship("Client")  # Back ref


class Conversation(Base):
    """
    對話 Session。
    """
    __tablename__ = "conversation"

    # 綁定租戶
    client_id = Column(UUID(as_uuid=True), ForeignKey(
        "client.id"), nullable=False, index=True)

    # 終端使用者 ID (User ID from Tenant's system) - Optional
    end_user_id = Column(String, nullable=True, index=True)

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan")
    conversation_documents = relationship(
        "ConversationDocument", back_populates="conversation")
    client = relationship("Client")


class ConversationDocument(Base):
    """
    紀錄特定對話引用了哪些文件 (Citation)。
    """
    __tablename__ = "conversation_document"

    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversation.id"), index=True)
    document_id = Column(UUID(as_uuid=True),
                         ForeignKey("document.id"), index=True)

    conversation = relationship(
        "Conversation", back_populates="conversation_documents")
    document = relationship("Document", back_populates="conversations")


class Message(Base):
    """
    對話中的單條訊息。
    """
    __tablename__ = "message"

    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversation.id"), index=True)
    content = Column(String)
    role = Column(to_pg_enum(MessageRoleEnum))
    status = Column(to_pg_enum(MessageStatusEnum),
                    default=MessageStatusEnum.PENDING)

    # 評分 (Thumb up/down)
    rating = Column(String, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    sub_processes = relationship(
        "MessageSubProcess", back_populates="message", cascade="all, delete-orphan")


class MessageSubProcess(Base):
    """
    紀錄 LlamaIndex 思考過程 (Trace)。
    """
    __tablename__ = "message_sub_process"

    message_id = Column(UUID(as_uuid=True),
                        ForeignKey("message.id"), index=True)
    source = Column(to_pg_enum(MessageSubProcessSourceEnum))
    status = Column(to_pg_enum(MessageSubProcessStatusEnum),
                    default=MessageSubProcessStatusEnum.FINISHED, nullable=False)
    metadata_map = Column(JSONB, nullable=True)

    message = relationship("Message", back_populates="sub_processes")
