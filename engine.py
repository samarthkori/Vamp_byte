import networkx as nx
from typing import List, Tuple

class FraudDetectionEngine:
    @staticmethod
    def evaluate(sender_id: str, receiver_id: str, amount: float, historical_transactions: list) -> Tuple[float, List[str]]:
        signals = []
        score = 0.0

        G = nx.DiGraph()
        for tx in historical_transactions:
            G.add_edge(tx.sender_id, tx.receiver_id, amount=tx.amount)

        # Add candidate edge
        G.add_edge(sender_id, receiver_id, amount=amount)

        # 1. Circular routing check
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if sender_id in cycle and receiver_id in cycle:
                    score += 0.55
                    path = " -> ".join(cycle + [cycle[0]])
                    signals.append(f" Possible circular laundering ring detected: {path}")
                    break
        except Exception:
            pass

        # 2. Mule fan-in check
        in_deg = G.in_degree(receiver_id)
        if in_deg >= 3:
            score += 0.30
            signals.append(f"Mule aggregation alert: Node '{receiver_id}' pooled from {in_deg} sources")

        # 3. Micro-probing check
        if amount < 2.0:
            score += 0.20
            signals.append("Sub-dollar micro-probing card test")
        elif amount >= 10000.0:
            score += 0.20
            signals.append("High-ticket transfer threshold exceeded")

        return round(min(score, 1.0), 2), signals