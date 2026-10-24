import datetime
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Account, RiskAudit, Transaction
from schemas import GraphEdge, GraphNode, GraphPayload, RiskAuditOut, TransactionCreate
from engine import FraudDetectionEngine

# Creates accounts, transactions, and risk_audits tables on boot
Base.metadata.create_all(bind=engine)

app = FastAPI(title="The Vampire's Ledger - AML Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_account(db: Session, account_id: str):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        acc = Account(id=account_id, owner_name=f"Entity_{account_id}")
        db.add(acc)
        db.commit()

@app.post("/api/transactions/process", response_model=RiskAuditOut)
def process_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    ensure_account(db, payload.sender_id)
    ensure_account(db, payload.receiver_id)

    recent_txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(500).all()

    risk_score, signals = FraudDetectionEngine.evaluate(
        sender_id=payload.sender_id,
        receiver_id=payload.receiver_id,
        amount=payload.amount,
        historical_transactions=recent_txs
    )

    if risk_score >= 0.70:
        decision = "BLOCK_AND_REPORT"
    elif risk_score >= 0.40:
        decision = "CHALLENGE_STEP_UP"
    else:
        decision = "APPROVE"

    tx = Transaction(
        id=payload.tx_id,
        sender_id=payload.sender_id,
        receiver_id=payload.receiver_id,
        amount=payload.amount,
        device_id=payload.device_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(tx)

    audit = RiskAudit(
        transaction_id=payload.tx_id,
        risk_score=risk_score,
        decision=decision,
        trigger_signals="; ".join(signals) if signals else "Clean baseline"
    )
    db.add(audit)
    db.commit()

    return RiskAuditOut(
        transaction_id=payload.tx_id,
        risk_score=risk_score,
        decision=decision,
        trigger_signals=signals
    )

@app.get("/api/graph/topology", response_model=GraphPayload)
def get_graph_topology(db: Session = Depends(get_db)):
    records = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(100).all()
    node_set = set()
    edges = []

    for r in records:
        node_set.add(r.sender_id)
        node_set.add(r.receiver_id)
        is_flagged = r.audit and r.audit.decision in ["BLOCK_AND_REPORT", "CHALLENGE_STEP_UP"]
        edges.append(GraphEdge(
            source=r.sender_id,
            target=r.receiver_id,
            amount=r.amount,
            is_suspicious=bool(is_flagged)
        ))

    nodes = [GraphNode(id=nid, label=nid) for nid in node_set]
    return GraphPayload(nodes=nodes, edges=edges)

@app.get("/api/audits/recent")
def get_recent_audits(db: Session = Depends(get_db)):
    audits = (
        db.query(RiskAudit, Transaction)
        .join(Transaction, RiskAudit.transaction_id == Transaction.id)
        .order_by(RiskAudit.created_at.desc())
        .limit(25)
        .all()
    )
    return [
        {
            "tx_id": tx.id,
            "sender": tx.sender_id,
            "receiver": tx.receiver_id,
            "amount": tx.amount,
            "risk_score": audit.risk_score,
            "decision": audit.decision,
            "signals": audit.trigger_signals,
            "timestamp": tx.timestamp.isoformat()
        }
        for audit, tx in audits
    ]