"""
sticky_experiment_harness.py

Online experiment harness with:
- Multiple strategies (next_book, popularity, librarian picks)
- Traffic shares (bids)
- Sticky assignment per student for the next N recommendation calls
- Logging of impressions + outcome logger stub

Run:
    pip install pandas numpy
    python sticky_experiment_harness.py
"""

from dataclasses import dataclass
from typing import Callable, Any, Dict, List
from datetime import datetime
import uuid

import numpy as np
import pandas as pd


# --------------------------------------------------------------------
# 1. Synthetic data: catalog + full checkout history
# --------------------------------------------------------------------

def load_catalog() -> pd.DataFrame:
    data = [
        ("b1", "The Curious Robot", True),
        ("b2", "Mystery at Maple Street", True),
        ("b3", "Adventures in Space", False),
        ("b4", "The Hidden Garden", True),
        ("b5", "Journey to the Sea", False),
        ("b6", "Pirates of the Bay", True),
    ]
    return pd.DataFrame(data, columns=["book_id", "title", "librarian_pick"])


def load_checkout_history() -> pd.DataFrame:
    data = [
        ("u1", "b1", "2024-01-01"),
        ("u1", "b2", "2024-01-05"),
        ("u1", "b3", "2024-01-10"),

        ("u2", "b2", "2024-01-02"),
        ("u2", "b4", "2024-01-06"),
        ("u2", "b5", "2024-01-11"),

        ("u3", "b1", "2024-01-03"),
        ("u3", "b4", "2024-01-07"),
        ("u3", "b2", "2024-01-12"),

        ("u4", "b6", "2024-01-04"),
        ("u4", "b2", "2024-01-08"),
    ]
    df = pd.DataFrame(data, columns=["user_id", "book_id", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# --------------------------------------------------------------------
# 2. Next-book transition model
# --------------------------------------------------------------------

def build_transition_model(checkouts: pd.DataFrame) -> pd.DataFrame:
    df = checkouts.sort_values(["user_id", "timestamp"]).copy()
    df["next_book"] = df.groupby("user_id")["book_id"].shift(-1)

    transitions = (
        df.dropna(subset=["next_book"])
          .groupby(["book_id", "next_book"])
          .size()
          .reset_index(name="count")
          .rename(columns={"book_id": "current_book"})
    )

    totals = (
        transitions.groupby("current_book")["count"]
        .sum()
        .reset_index(name="total")
    )
    transitions = transitions.merge(totals, on="current_book")
    transitions["prob"] = transitions["count"] / transitions["total"]

    return transitions[["current_book", "next_book", "count", "prob"]]


def get_user_history(user_id: str, checkouts: pd.DataFrame) -> pd.DataFrame:
    return (
        checkouts[checkouts["user_id"] == user_id]
        .sort_values("timestamp")
        .copy()
    )


def next_book_recs(
    student_id: str,
    checkouts: pd.DataFrame,
    transitions: pd.DataFrame,
    k: int = 3,
) -> pd.DataFrame:
    """
    Strategy: next_book
    - Use last few books and transition probabilities.
    - Return DataFrame with book_id + score.
    """
    user_hist = get_user_history(student_id, checkouts)
    if user_hist.empty:
        return pd.DataFrame(columns=["book_id", "score"])

    recent_books = user_hist["book_id"].tail(3).tolist()
    scores: Dict[str, float] = {}

    for b in recent_books:
        subset = transitions[transitions["current_book"] == b]
        for _, row in subset.iterrows():
            nb = row["next_book"]
            scores[nb] = scores.get(nb, 0.0) + float(row["prob"])

    already = set(user_hist["book_id"])
    scores = {b: s for b, s in scores.items() if b not in already}

    if not scores:
        return pd.DataFrame(columns=["book_id", "score"])

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return pd.DataFrame(ranked, columns=["book_id", "score"])


# --------------------------------------------------------------------
# 3. Popularity & librarian strategies
# --------------------------------------------------------------------

def popularity_recs(
    student_id: str,
    checkouts: pd.DataFrame,
    k: int = 3,
) -> pd.DataFrame:
    """
    Strategy: popularity
    - Global most-read books, excluding already read.
    """
    if checkouts.empty:
        return pd.DataFrame(columns=["book_id", "score"])

    user_hist = get_user_history(student_id, checkouts)
    already = set(user_hist["book_id"])

    pop = (
        checkouts.groupby("book_id")
                 .size()
                 .reset_index(name="count")
                 .sort_values("count", ascending=False)
    )
    pop = pop[~pop["book_id"].isin(already)].head(k)
    pop = pop.rename(columns={"count": "score"})
    return pop[["book_id", "score"]]


def librarian_picks_recs(
    student_id: str,
    checkouts: pd.DataFrame,
    catalog: pd.DataFrame,
    k: int = 3,
) -> pd.DataFrame:
    """
    Strategy: librarian_picks
    - Books flagged as librarian_pick, ranked by popularity.
    """
    user_hist = get_user_history(student_id, checkouts)
    already = set(user_hist["book_id"])

    picks = catalog[catalog["librarian_pick"]]
    picks = picks[~picks["book_id"].isin(already)]

    if picks.empty:
        return pd.DataFrame(columns=["book_id", "score"])

    pop = (
        checkouts[checkouts["book_id"].isin(picks["book_id"])]
        .groupby("book_id")
        .size()
        .reset_index(name="count")
    )

    merged = picks.merge(pop, on="book_id", how="left").fillna({"count": 0})
    merged = merged.sort_values("count", ascending=False).head(k)
    merged = merged.rename(columns={"count": "score"})
    return merged[["book_id", "score"]]


# --------------------------------------------------------------------
# 4. Strategy wrapper (with bids)
# --------------------------------------------------------------------

@dataclass
class Strategy:
    name: str
    bid: float
    func: Callable[..., pd.DataFrame]
    default_kwargs: Dict[str, Any]

    def recommend(self, student_id: str, **override_kwargs) -> pd.DataFrame:
        kwargs = {**self.default_kwargs, **override_kwargs}
        return self.func(student_id=student_id, **kwargs)


# --------------------------------------------------------------------
# 5. ExperimentManager: bids + sticky assignment
# --------------------------------------------------------------------

class ExperimentManager:
    def __init__(self, strategies: List[Strategy], n_books_per_assignment: int = 5):
        self.strategies = strategies
        self.n_books_per_assignment = n_books_per_assignment

        bids = np.array([s.bid for s in strategies], dtype=float)
        if bids.sum() <= 0:
            bids = np.ones_like(bids)
        self.probs = bids / bids.sum()

        # student_id -> {strategy_name, remaining, assignment_id}
        self._assignments: Dict[str, Dict[str, Any]] = {}
        self.logs: List[Dict[str, Any]] = []

    def _choose_strategy(self) -> Strategy:
        idx = np.random.choice(len(self.strategies), p=self.probs)
        return self.strategies[idx]

    def _get_or_create_assignment(self, student_id: str) -> Dict[str, Any]:
        assignment = self._assignments.get(student_id)
        if assignment and assignment["remaining"] > 0:
            return assignment

        strategy = self._choose_strategy()
        assignment_id = str(uuid.uuid4())
        assignment = {
            "strategy_name": strategy.name,
            "remaining": self.n_books_per_assignment,
            "assignment_id": assignment_id,
        }
        self._assignments[student_id] = assignment
        return assignment

    def recommend(self, student_id: str, **override_kwargs) -> pd.DataFrame:
        assignment = self._get_or_create_assignment(student_id)
        strategy_name = assignment["strategy_name"]
        assignment_id = assignment["assignment_id"]

        strategy = next(s for s in self.strategies if s.name == strategy_name)

        recs = strategy.recommend(student_id, **override_kwargs)

        assignment["remaining"] -= 1

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "student_id": student_id,
            "strategy_name": strategy.name,
            "assignment_id": assignment_id,
            "n_shown": len(recs),
        }
        self.logs.append(log_entry)

        return recs

    def get_logs_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.logs)


# --------------------------------------------------------------------
# 6. Outcome logger (borrows/clicks)
# --------------------------------------------------------------------

class OutcomeLogger:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log_borrow(
        self,
        student_id: str,
        book_id: str,
        assignment_id: str | None,
        strategy_name: str | None,
    ):
        self.events.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "student_id": student_id,
                "book_id": book_id,
                "assignment_id": assignment_id,
                "strategy_name": strategy_name,
                "event_type": "borrow",
            }
        )

    def get_events_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.events)


# --------------------------------------------------------------------
# 7. Demo / main
# --------------------------------------------------------------------

def main():
    catalog = load_catalog()
    checkouts = load_checkout_history()
    transitions = build_transition_model(checkouts)

    print("=== Catalog ===")
    print(catalog, "\n")

    print("=== Checkouts ===")
    print(checkouts, "\n")

    print("=== Transitions ===")
    print(transitions, "\n")

    # Register strategies with bids
    strategies = [
        Strategy(
            name="next_book",
            bid=2.0,  # gets twice the traffic of others
            func=next_book_recs,
            default_kwargs=dict(checkouts=checkouts, transitions=transitions, k=3),
        ),
        Strategy(
            name="popularity",
            bid=1.0,
            func=popularity_recs,
            default_kwargs=dict(checkouts=checkouts, k=3),
        ),
        Strategy(
            name="librarian_picks",
            bid=1.0,
            func=librarian_picks_recs,
            default_kwargs=dict(checkouts=checkouts, catalog=catalog, k=3),
        ),
    ]

    exp = ExperimentManager(strategies, n_books_per_assignment=2)
    outcomes = OutcomeLogger()

    print("=== Online Experiment Demo (sticky per student) ===")
    for step in range(1, 6):  # simulate 5 recommendation events
        print(f"\n--- Recommendation step {step} ---")
        for student_id in checkouts["user_id"].unique():
            recs = exp.recommend(student_id)
            # get assignment info for logging outcomes
            assignment = exp._assignments[student_id]
            assignment_id = assignment["assignment_id"]
            strategy_name = assignment["strategy_name"]

            print(f"Student {student_id} -> strategy={strategy_name}")
            print(recs)

            # simulate: student borrows the first recommended book if any
            if not recs.empty:
                book_id = recs.iloc[0]["book_id"]
                outcomes.log_borrow(student_id, book_id, assignment_id, strategy_name)

    print("\n=== Impression Logs ===")
    print(exp.get_logs_df())

    print("\n=== Outcome (Borrow) Logs ===")
    print(outcomes.get_events_df())


if __name__ == "__main__":
    main()
