# Library Reading Recommendation System

A Python-based book recommendation system with multiple strategies, experiment harness, and LLM-powered presentation. This project demonstrates production-ready recommendation approaches for school libraries, including transition-based (Markov) models, popularity-based recommendations, and intelligent fallback strategies.

## Features

- 📚 **Multiple Recommendation Strategies**
  - Transition-based (Markov model): Next-book recommendations based on reading sequences
  - Popularity-based: Most checked-out books
  - Librarian picks: Curated recommendations
  - Hybrid fallback: Multi-level strategy with graceful degradation

- 🧪 **Experiment Harness**
  - A/B testing framework with traffic allocation (bids)
  - Sticky user assignments for consistent experiences
  - Impression and outcome logging
  - Support for multiple competing strategies

- 🤖 **LLM-Powered Agent**
  - Friendly library agent that presents recommendations
  - Uses LiteLLM for multi-provider LLM support
  - Personalized, engaging messages for students
  - Context-aware presentation with reading history

## Project Components

### 1. `basic_demo.py`
Simple standalone demonstration of the transition-based recommendation model with intelligent fallback strategies.

**Run:**
```powershell
pixi run python src/library_reading/basic_demo.py
```

**What it demonstrates:**
- Building transition models from checkout history
- Handling sparse data with multi-level fallbacks
- Strategy transparency (shows which approach was used)

### 2. `experiment_harness.py`
Production-ready A/B testing framework for competing recommendation strategies.

**Run:**
```powershell
pixi run python src/library_reading/experiment_harness.py
```

**What it demonstrates:**
- Multiple strategies competing for traffic
- Bid-based traffic allocation
- Sticky user assignments (users stay with same strategy)
- Comprehensive logging for analysis

### 3. `llm_agent.py`
LLM-powered library agent that presents recommendations in a friendly, engaging way.

**Setup:**
1. Create a `.env` file with your API key:
   ```
   OPENAI_API_KEY=your-key-here
   # Or use other providers: ANTHROPIC_API_KEY, GOOGLE_API_KEY, etc.
   ```

2. Run:
   ```powershell
   pixi run python src/library_reading/llm_agent.py
   ```

**What it demonstrates:**
- Integration of recommendation engine with LLM presentation
- Context-aware, personalized messaging
- Maintains experiment integrity while improving UX

## Prerequisites

- [pixi](https://pixi.sh) - A fast, cross-platform package manager
- Python 3.11 or higher (managed by pixi)
- API key for LLM provider (for `llm_agent.py` only)

### Installing pixi

On Windows (PowerShell):
```powershell
iwr -useb https://pixi.sh/install.ps1 | iex
```

For other platforms, visit [pixi.sh](https://pixi.sh).

## Getting Started

### 1. Install Dependencies

Clone the repository and install all dependencies:

```powershell
pixi install
```

This will:
- Create a virtual environment in `.pixi/`
- Install all dependencies defined in `pyproject.toml`
- Install the `library_reading` package in editable mode

### 2. Run Commands in the pixi Environment

To run any command within the pixi environment:

```powershell
pixi run <command>
```

Or start a shell with the environment activated:

```powershell
pixi shell
```

### 3. Running Python Scripts

Execute Python scripts using the pixi environment:

```powershell
pixi run python your_script.py
```

## Project Structure

```
library_reading/
├── src/
│   └── library_reading/
│       ├── __init__.py
│       ├── basic_demo.py           # Standalone demo with fallback strategies
│       ├── experiment_harness.py   # A/B testing framework
│       └── llm_agent.py            # LLM-powered presentation layer
├── pyproject.toml                  # Project metadata and pixi configuration
├── pixi.lock                       # Lock file for reproducible environments
├── INTEGRATION_NOTES.md            # Technical integration documentation
└── README.md
```

## Recommendation Strategies

### 1. Transition-Based (Markov Model)
Uses reading sequence patterns to predict what users read next.
- **Pros**: Highly personalized, captures reading patterns
- **Cons**: Requires sufficient data, fails on cold start

### 2. Popularity-Based
Recommends the most checked-out books.
- **Pros**: Simple, works for everyone, handles cold start
- **Cons**: Not personalized, filter bubble risk

### 3. Librarian Picks
Curated recommendations from librarians.
- **Pros**: Editorial quality, diversity
- **Cons**: Static, requires curation effort

### 4. Hybrid Fallback
Multi-level strategy with graceful degradation:
1. Try transition-based first
2. Fall back to popularity if no transitions
3. Fall back to librarian picks if already read popular books
4. Random exploration as last resort

- **Pros**: Robust to sparse data, always returns recommendations
- **Cons**: More complex logic

## Configuration

The project is configured in `pyproject.toml` with the following pixi settings:

- **Channels**: `conda-forge`
- **Platforms**: `win-64` (Windows 64-bit)
- **Dependencies**: 
  - pandas (>=2.3.3, <3)
  - numpy
  - litellm
  - python-dotenv
- **Python Version**: >=3.11

## Adding Dependencies

### Adding Conda Dependencies

To add a new conda package:

```powershell
pixi add <package-name>
```

Example:
```powershell
pixi add numpy
```

### Adding PyPI Dependencies

To add a PyPI package:

```powershell
pixi add --pypi <package-name>
```

Example:
```powershell
pixi add --pypi requests
```

## Custom Tasks

You can define custom tasks in `pyproject.toml` under `[tool.pixi.tasks]`. Run them with:

```powershell
pixi run <task-name>
```

Example task configuration:
```toml
[tool.pixi.tasks]
test = "pytest tests/"
lint = "ruff check src/"
format = "ruff format src/"
```

## Updating Dependencies

To update all dependencies to their latest compatible versions:

```powershell
pixi update
```

## Cleaning Up

To remove the pixi environment and start fresh:

```powershell
Remove-Item -Recurse -Force .pixi
pixi install
```

## Key Concepts

### Experiment Harness
The experiment harness enables A/B testing of recommendation strategies:

- **Bid-based allocation**: Strategies compete for traffic with weighted bids
- **Sticky assignments**: Users stay with the same strategy for N recommendations
- **Logging**: Tracks impressions and outcomes for analysis
- **Strategy interface**: Unified interface for all recommendation approaches

### Multi-Level Fallback
Handles data sparsity gracefully:

```
User's last book
    ↓
Has transitions? → Yes → Return transition-based recs
    ↓ No
Popular unread books? → Yes → Return popularity recs
    ↓ No
Librarian picks unread? → Yes → Return librarian recs
    ↓ No
Any unread books? → Yes → Return random recs
    ↓ No
Return empty (user has read everything!)
```

## Example Output

### Basic Demo
Shows how recommendations adapt when transitions are missing:

```
User u1: last book = b3, read books = ['b1', 'b2', 'b3']
  Strategy: popularity
  Recommended next books: ['b4', 'b5', 'b6']
  → No transitions learned from 'b3' (no user read a book after it)
```

### Experiment Harness
Shows traffic allocation and logging:

```
Student u4 -> strategy=hybrid_fallback
  book_id  score
2      b3    0.5
3      b4    0.5
```

### LLM Agent
Presents recommendations in a friendly way:

```
📚 Agent's Message:
------------------------------------------------------------
Hi there! I've got some exciting books picked out just for you!

"The Hidden Garden" is a wonderful choice - it's one of our 
librarian's favorites! ⭐ Following that, "Pirates of the Bay" 
is an action-packed adventure that I think you'll love.

Happy reading! 📖
------------------------------------------------------------
```

## Troubleshooting

### Environment Issues

If you encounter environment issues, try:

1. Clean and reinstall:
   ```powershell
   Remove-Item -Recurse -Force .pixi
   pixi install
   ```

2. Check pixi version:
   ```powershell
   pixi --version
   ```

### Lock File Conflicts

If `pixi.lock` has conflicts after a merge, regenerate it:

```powershell
pixi install --locked=false
```

### LLM Agent Issues

1. Make sure your `.env` file exists with a valid API key
2. Check supported models: [LiteLLM Providers](https://docs.litellm.ai/docs/providers)
3. Try a different model if one is rate-limited or unavailable

## Architecture Notes

This project demonstrates several production recommender system patterns:

- **Separation of concerns**: Recommendation logic, experimentation, and presentation are decoupled
- **Graceful degradation**: Multiple fallback strategies ensure robustness
- **Explainability**: Logs show which strategy was used and why
- **A/B testing**: Built-in experimentation framework for data-driven decisions
- **User experience**: LLM layer adds personality without compromising integrity

For technical details on the integration, see [`INTEGRATION_NOTES.md`](INTEGRATION_NOTES.md).

## More Information

- [pixi Documentation](https://pixi.sh/latest/)
- [pixi GitHub Repository](https://github.com/prefix-dev/pixi)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [pandas Documentation](https://pandas.pydata.org/)

## Future Enhancements

Potential improvements:
- Add content-based filtering (book metadata, genres)
- Implement collaborative filtering (user-user similarity)
- Add temporal features (time of year, reading velocity)
- Build evaluation metrics (precision@k, diversity)
- Add real database integration (PostgreSQL, MongoDB)
- Implement caching for production performance
- Add user feedback loop (ratings, reviews)

## License

MIT License

## Contributing

[Add contribution guidelines here]
