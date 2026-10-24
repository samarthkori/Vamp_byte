from typing import List, Optional
from pydantic import BaseModel, Field

class TransactionCreate(BaseModel):
    tx_id: str
    sender_id: str
    receiver_id: str
    amount: float = Field(..., gt=0)
    device_id: Optional[str] = "DEV_01"

class RiskAuditOut(BaseModel):
    transaction_id: str
    risk_score: float
    decision: str
    trigger_signals: List[str]

    class Config:
        from_attributes = True

class GraphNode(BaseModel):
    id: str
    label: str

class GraphEdge(BaseModel):
    source: str
    target: str
    amount: float
    is_suspicious: bool

class GraphPayload(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]