"""
llm_agent.py

LLM-powered library agent that:
- Gets recommendations from the experiment harness
- Presents them to students in a friendly, engaging way
- Uses LiteLLM to generate personalized book suggestions

Run:
    pixi run python src/library_reading/llm_agent.py
"""

from typing import List, Dict, Any
import pandas as pd
from litellm import completion
import dotenv
dotenv.load_dotenv()

from experiment_harness import (
    load_catalog,
    load_checkout_history,
    build_transition_model,
    Strategy,
    ExperimentManager,
    next_book_recs,
    popularity_recs,
    librarian_picks_recs,
)


class LibraryAgent:
    """
    A friendly school library agent that uses LLM to present book recommendations.
    """
    
    def __init__(
        self,
        catalog: pd.DataFrame,
        experiment_manager: ExperimentManager,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ):
        self.catalog = catalog
        self.experiment_manager = experiment_manager
        self.model = model
        self.temperature = temperature
        
    def get_book_details(self, book_ids: List[str]) -> List[Dict[str, Any]]:
        """Get full book details from catalog."""
        books = []
        for book_id in book_ids:
            book_row = self.catalog[self.catalog["book_id"] == book_id]
            if not book_row.empty:
                books.append({
                    "book_id": book_id,
                    "title": book_row.iloc[0]["title"],
                    "librarian_pick": book_row.iloc[0]["librarian_pick"],
                })
        return books
    
    def get_user_reading_history(
        self,
        student_id: str,
        checkouts: pd.DataFrame
    ) -> List[str]:
        """Get list of book titles the user has already read."""
        user_checkouts = checkouts[checkouts["user_id"] == student_id]
        if user_checkouts.empty:
            return []
        
        book_ids = user_checkouts["book_id"].tolist()
        books = self.get_book_details(book_ids)
        return [book["title"] for book in books]
    
    def create_prompt(
        self,
        student_id: str,
        recommended_books: List[Dict[str, Any]],
        reading_history: List[str],
        strategy_name: str,
    ) -> str:
        """Create the prompt for the LLM agent."""
        
        system_prompt = """You are a friendly and enthusiastic school library agent. 
Your job is to recommend books to students in an engaging way that makes them excited to read.

Guidelines:
- Be warm and encouraging
- Highlight what makes each book interesting
- Keep your recommendations concise (2-3 sentences per book)
- Use age-appropriate language for elementary/middle school students
- Don't mention technical details like "recommendation strategy" or "algorithm"
- Make it feel personal and conversational
"""
        
        # Build the recommendation details
        book_list = []
        for i, book in enumerate(recommended_books, 1):
            librarian_note = " ⭐ (Librarian's Pick!)" if book["librarian_pick"] else ""
            book_list.append(f"{i}. {book['title']}{librarian_note}")
        
        books_text = "\n".join(book_list)
        
        history_text = ""
        if reading_history:
            history_text = f"\n\nBooks they've already read:\n" + "\n".join(f"- {title}" for title in reading_history)
        
        user_prompt = f"""Student ID: {student_id}

Here are some book recommendations for this student:

{books_text}{history_text}

Please write a brief, engaging message to the student introducing these book recommendations. 
Make them excited about reading these books!"""
        
        return system_prompt, user_prompt
    
    def present_recommendations(
        self,
        student_id: str,
        checkouts: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Get recommendations from the experiment harness and present them via LLM.
        
        Returns:
            Dict with keys: student_id, strategy_name, recommended_books, llm_message
        """
        # Get recommendations from the experiment harness
        recs_df = self.experiment_manager.recommend(student_id)
        
        if recs_df.empty:
            return {
                "student_id": student_id,
                "strategy_name": None,
                "recommended_books": [],
                "llm_message": "I don't have any new recommendations for you right now. Keep reading!",
            }
        
        # Get assignment info
        assignment = self.experiment_manager._assignments[student_id]
        strategy_name = assignment["strategy_name"]
        
        # Get book details
        book_ids = recs_df["book_id"].tolist()
        recommended_books = self.get_book_details(book_ids)
        
        # Get reading history
        reading_history = self.get_user_reading_history(student_id, checkouts)
        
        # Create prompt
        system_prompt, user_prompt = self.create_prompt(
            student_id,
            recommended_books,
            reading_history,
            strategy_name,
        )
        
        # Call LLM
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )
            llm_message = response.choices[0].message.content
        except Exception as e:
            # Fallback if LLM call fails
            llm_message = f"Hi! I have some great book recommendations for you: {', '.join([b['title'] for b in recommended_books])}. Check them out!"
            print(f"LLM call failed: {e}. Using fallback message.")
        
        return {
            "student_id": student_id,
            "strategy_name": strategy_name,
            "recommended_books": recommended_books,
            "llm_message": llm_message,
        }


def demo():
    """Demo of the LLM library agent."""
    
    # Set up data and experiment harness
    catalog = load_catalog()
    checkouts = load_checkout_history()
    transitions = build_transition_model(checkouts)
    
    # Register strategies
    strategies = [
        Strategy(
            name="next_book",
            bid=2.0,
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
    
    exp_manager = ExperimentManager(strategies, n_books_per_assignment=3)
    
    # Create library agent
    # Note: You'll need to set OPENAI_API_KEY or other provider credentials
    agent = LibraryAgent(
        catalog=catalog,
        experiment_manager=exp_manager,
        model="gpt-4o-mini",  # or "claude-3-5-sonnet-20241022", "gemini/gemini-pro", etc.
        temperature=0.7,
    )
    
    print("=== School Library Agent Demo ===\n")
    
    # Demo for each student
    for student_id in checkouts["user_id"].unique():
        print(f"\n{'='*60}")
        print(f"Student: {student_id}")
        print('='*60)
        
        result = agent.present_recommendations(student_id, checkouts)
        
        print(f"\n[Strategy used: {result['strategy_name']}]")
        print(f"\nRecommended books:")
        for book in result["recommended_books"]:
            librarian_note = " ⭐" if book["librarian_pick"] else ""
            print(f"  • {book['title']}{librarian_note}")
        
        print(f"\n📚 Agent's Message:")
        print("-" * 60)
        print(result["llm_message"])
        print("-" * 60)


if __name__ == "__main__":
    demo()
