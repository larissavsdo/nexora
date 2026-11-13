from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=220)
    description: str = ""
    customer_id: int
    department_id: int
    agent_id: int | None = None
    priority: str = "normal"

class TicketStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|waiting|resolved|closed)$")

class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    status: str
    priority: str
    customer_id: int
    agent_id: int | None
    department_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    sender_type: str = Field(pattern="^(customer|agent|system)$")
    sender_id: int | None = None
    content: str = Field(min_length=1, max_length=10000)
    channel: str = "whatsapp"
