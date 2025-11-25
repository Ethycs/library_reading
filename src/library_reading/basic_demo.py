"""
basic_demo.py

Simplest possible example of:
- Ingesting full checkout history
- Building a next-book recommendation model
- Running a tiny experiment over all users

Run:
    python basic_demo.py
"""

from collections import Counter
from typing import List
import pandas as pd
import random


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


def load_librarian_recommendations() -> List[str]:
    """
    Load librarian's curated recommendations.
    In a real setting, this would come from a database or file.
    """
    return ["b6", "b7", "b8", "b9", "b10"]


def get_all_books(checkouts: pd.DataFrame) -> List[str]:
    """
    Get all unique books from checkout history.
    In a real setting, this would include the full catalog.
    """
    # Combine books from checkout history and librarian recommendations
    checkout_books = checkouts["book_id"].unique().tolist()
    librarian_books = load_librarian_recommendations()
    return list(set(checkout_books + librarian_books))


def recommend_popular_books_for_user(
    user_id: str,
    checkouts: pd.DataFrame,
    k: int = 3,
) -> List[str]:
    """
    Recommend most popular books that the user hasn't read yet.
    
    Popularity = checkout count across all users.
    """
    user_hist = checkouts[checkouts["user_id"] == user_id]
    user_read_books = set(user_hist["book_id"].tolist())
    
    # Count popularity of all books
    popularity = (
        checkouts.groupby("book_id")
        .size()
        .reset_index(name="checkout_count")
        .sort_values("checkout_count", ascending=False)
    )
    
    # Filter out books the user has already read
    unread_popular = popularity[~popularity["book_id"].isin(user_read_books)]
    
    return unread_popular["book_id"].head(k).tolist()


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
) -> tuple[List[str], str]:
    """
    Recommend top-k next books for a user, based on the user's last book.

    Steps:
    - Find the user's last checked-out book.
    - Look up all next_book candidates for that current_book.
    - Rank by probability.
    - Return top-k book_ids.
    - If no recommendations, fall back to:
      1. Popularity-based recommendations
      2. Librarian recommendations
      3. Random unread books
    
    Returns:
        tuple: (recommended_books, strategy_used)
    """
    user_hist = (
        checkouts[checkouts["user_id"] == user_id]
        .sort_values("timestamp")
    )
    if user_hist.empty:
        return [], "no_history"

    last_book = user_hist.iloc[-1]["book_id"]
    user_read_books = set(user_hist["book_id"].tolist())

    # all transitions from last_book
    candidates = transitions[transitions["current_book"] == last_book]

    if not candidates.empty:
        # Primary strategy: transition-based
        top = candidates.sort_values("prob", ascending=False).head(k)
        return top["next_book"].tolist(), "transition"

    # Fallback 1: Use popularity-based recommendations
    popular_recs = recommend_popular_books_for_user(user_id, checkouts, k=k)
    if popular_recs:
        return popular_recs, "popularity"
    
    # Fallback 2: Use librarian recommendations
    librarian_recs = load_librarian_recommendations()
    unread_librarian_recs = [book for book in librarian_recs if book not in user_read_books]
    
    if unread_librarian_recs:
        return unread_librarian_recs[:k], "librarian"
    
    # Fallback 3: Choose randomly from all unread books
    all_books = get_all_books(checkouts)
    unread_books = [book for book in all_books if book not in user_read_books]
    
    if unread_books:
        random.shuffle(unread_books)
        return unread_books[:k], "random"
    
    return [], "all_read"


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

    print("=== Book Popularity (Overall Checkout Counts) ===")
    popularity = (
        checkouts.groupby("book_id")
        .size()
        .reset_index(name="checkout_count")
        .sort_values("checkout_count", ascending=False)
    )
    print(popularity, "\n")

    print("=== Librarian Recommendations ===")
    print(load_librarian_recommendations(), "\n")

    print("=== Experiment: Recommendations per user ===")
    for user_id in checkouts["user_id"].unique():
        recs, strategy = recommend_next_books_for_user(user_id, checkouts, transitions, k=3)
        user_hist = checkouts[checkouts['user_id']==user_id].sort_values('timestamp')
        last_book = user_hist.iloc[-1]['book_id']
        read_books = user_hist['book_id'].tolist()
        
        print(f"User {user_id}: last book = {last_book}, read books = {read_books}")
        print(f"  Strategy: {strategy}")
        print(f"  Recommended next books: {recs}")
        
        # Show why transition might be empty
        if strategy != "transition":
            has_transitions = not transitions[transitions["current_book"] == last_book].empty
            if not has_transitions:
                print(f"  → No transitions learned from '{last_book}' (no user read a book after it)")
        print()


if __name__ == "__main__":
    run_experiment()
