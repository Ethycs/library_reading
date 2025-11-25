"""
next_book_experiment.py

Simplest possible example of:
- Ingesting full checkout history
- Building a next-book recommendation model
- Running a tiny experiment over all users

Run:
    pip install pandas
    python next_book_experiment.py
"""

from collections import Counter
from typing import List
import pandas as pd


def load_checkout_history() -> pd.DataFrame:
    """
    In a real setting, you'd do:
        df = pd.read_csv("checkouts.csv")
    with columns: user_id, book_id, timestamp

    Here we just build a tiny synthetic example.
    """
    data = [
        # user_id, book_id, timestamp (any sortable value)
        ("u1", "b1", "2024-01-01"),
        ("u1", "b2", "2024-01-05"),
        ("u1", "b3", "2024-01-10"),
        ("u2", "b2", "2024-01-02"),
        ("u2", "b4", "2024-01-06"),
        ("u2", "b5", "2024-01-11"),
        ("u3", "b1", "2024-01-03"),
        ("u3", "b4", "2024-01-07"),
        ("u3", "b2", "2024-01-12"),
    ]
    df = pd.DataFrame(data, columns=["user_id", "book_id", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def build_transition_model(checkouts: pd.DataFrame) -> pd.DataFrame:
    """
    Build a simple next-book transition table.

    For each user:
        sort by time
        take (current_book -> next_book) pairs

    Returns a DataFrame with:
        current_book, next_book, count, prob
    """
    # sort checkouts
    df = checkouts.sort_values(["user_id", "timestamp"]).copy()

    # next_book is the next row's book_id within each user
    df["next_book"] = df.groupby("user_id")["book_id"].shift(-1)

    transitions = (
        df.dropna(subset=["next_book"])
          .groupby(["book_id", "next_book"])
          .size()
          .reset_index(name="count")
          .rename(columns={"book_id": "current_book"})
    )

    # compute probabilities per current_book
    totals = (
        transitions.groupby("current_book")["count"]
        .sum()
        .reset_index(name="total")
    )
    transitions = transitions.merge(totals, on="current_book")
    transitions["prob"] = transitions["count"] / transitions["total"]

    return transitions[["current_book", "next_book", "count", "prob"]]


def recommend_next_books_for_user(
    user_id: str,
    checkouts: pd.DataFrame,
    transitions: pd.DataFrame,
    k: int = 3,
) -> List[str]:
    """
    Recommend top-k next books for a user, based on the user's last book.

    Steps:
    - Find the user's last checked-out book.
    - Look up all next_book candidates for that current_book.
    - Rank by probability.
    - Return top-k book_ids.
    """
    user_hist = (
        checkouts[checkouts["user_id"] == user_id]
        .sort_values("timestamp")
    )
    if user_hist.empty:
        return []

    last_book = user_hist.iloc[-1]["book_id"]

    # all transitions from last_book
    candidates = transitions[transitions["current_book"] == last_book]

    if candidates.empty:
        return []

    # sort by prob, highest first, take top-k
    top = candidates.sort_values("prob", ascending=False).head(k)
    return top["next_book"].tolist()


def run_experiment():
    """
    Minimal 'experiment':
    - Ingest all checkout history
    - Build transition model
    - For each user, recommend next books based on their last book
    - Print results
    """
    checkouts = load_checkout_history()
    transitions = build_transition_model(checkouts)

    print("=== Full Checkout History ===")
    print(checkouts, "\n")

    print("=== Learned Transitions (current_book -> next_book) ===")
    print(transitions, "\n")

    print("=== Experiment: Recommendations per user ===")
    for user_id in checkouts["user_id"].unique():
        recs = recommend_next_books_for_user(user_id, checkouts, transitions, k=3)
        print(f"User {user_id}: last book = {checkouts[checkouts['user_id']==user_id].sort_values('timestamp').iloc[-1]['book_id']}")
        print(f"  Recommended next books: {recs}\n")


if __name__ == "__main__":
    run_experiment()
