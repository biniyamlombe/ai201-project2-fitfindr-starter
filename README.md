# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Agent Documentation

### Tool Inventory

| Tool Name | Parameters | Return Type | Purpose |
|---|---|---|---|
| **`search_listings`** | `description` (str), `size` (str \| None), `max_price` (float \| None) | `list[dict]` | Scans database listings, filters by size (case-insensitive substring) and price (inclusive), scores by keyword overlap, and returns sorted lists. |
| **`suggest_outfit`** | `new_item` (dict), `wardrobe` (dict) | `str` (Markdown) | Employs an LLM to recommend 1–2 outfit combinations pairing the new item with pieces from the wardrobe, or provides general styling recommendations if the wardrobe is empty. |
| **`create_fit_card`** | `outfit` (str), `new_item` (dict) | `str` | Generates a casual, authentic OOTD-style social media caption referencing the item title, price, and platform exactly once. |
| **`compare_price`** | `item` (dict) | `str` | Compares the selected item's price against other listings in the same category, computing min/max/average price statistics, and uses the LLM to generate a style-conscious price assessment. |

---

### Planning Loop

FitFindr uses a sequential planning loop built on top of state management across a single session:
1. **Query Parsing**: A specialized `llama-3.3-70b-versatile` LLM parser processes raw natural language inputs to extract structured parameters (`description`, `size`, `max_price`) as JSON attributes.
2. **Search Execution & Fallback Retry**:
   * It executes `search_listings` using the parsed criteria.
   * **Fallback 1 (Size)**: If no results are found and a `size` constraint was parsed, the agent automatically drops the size filter and retries.
   * **Fallback 2 (Price)**: If the search is still empty and `max_price` was set, the agent raises the maximum price ceiling by 50% (and clears size constraints) before retrying.
   * Any adjustments made are logged in `session["adjustments"]` and displayed as warning headers in the Gradio UI.
3. **Branching/Guard Check**: If no relevant items are retrieved after all retry attempts, the agent halts early, records the reason in the session state, and reports it.
4. **Price Comparison**: For the selected top match, it invokes `compare_price` to fetch statistical metrics (min, max, average) for the category, compiling an LLM-powered style-conscious value opinion saved to `session["price_assessment"]`.
5. **Outfit Suggestions**: It selects the top search match and triggers `suggest_outfit` alongside the user's wardrobe details.
6. **Fit Card Generation**: Finally, it triggers `create_fit_card` using the styled outfit output and the selected item to generate a shareable social media OOTD caption.

---

### State Management Approach

Session state is centralized in a single `session` dictionary that flows throughout the lifecycle of the user interaction. This dictionary acts as the single source of truth:
* `query` (str): The raw string input from the user.
* `parsed` (dict): Extracted search parameters (`description`, `size`, `max_price`).
* `search_results` (list): The list of matched listings returned by `search_listings`.
* `selected_item` (dict): The top listing match from search, passed into both `suggest_outfit` and `create_fit_card`.
* `wardrobe` (dict): The user's active wardrobe dictionary.
* `price_assessment` (str | None): LLM-generated analysis of how the item's price compares to the category averages.
* `adjustments` (list[str]): Log messages describing search constraints that were loosened due to zero matches.
* `outfit_suggestion` (str): Styling recommendations from `suggest_outfit`, piped directly as the input for `create_fit_card`.
* `fit_card` (str): The final social media caption output.
* `error` (str | None): Tracks any early exit reasons (e.g. no search results) or tool failure details.

---

### Error Handling & Testing Examples

Each component handles its failure mode gracefully without throwing unhandled exceptions:

* **`search_listings`**: If no listings match, it returns an empty list `[]`. The planning loop catches this early-exit condition, sets `session["error"] = "No matching items found for your search."`, and terminates early.
  * *Example Test Output*:
    ```python
    # Running designer ballgown size XXS under $5
    "Error: No matching items found for your search."
    ```
* **`suggest_outfit`**: If the wardrobe is empty, it calls the LLM with a fallback prompt to output a guide on general color palettes, aesthetics, and building blocks to style the new item.
  * *Example Test Output*:
    ```text
    "The Y2K Baby Tee with a butterfly print is an adorable addition to any wardrobe. Since your wardrobe is currently empty, let's start building a foundation around this cute top..."
    ```
* **`create_fit_card`**: If the outfit string is empty, it returns a descriptive error message string: `"Error: Cannot generate fit card due to missing outfit details."` instead of crashing.
  * *Example Test Output*:
    ```python
    "Error: Cannot generate fit card due to missing outfit details."
    ```
* **`compare_price`**: If the LLM pricing analysis fails or the Groq client raises an error, it catches the exception and returns a pre-formatted fallback pricing message with category stats (min, max, average).
  * *Example Test Output*:
    ```text
    "This item is priced at $38.00. Comparable items in the category 'bottoms' range from $20.00 to $65.00 (average: $39.50)."
    ```
* **`run_agent` Retry Logic (Fallback)**: When an impossible query is run, the agent automatically retries search queries with loosened filters (removing size restriction, then increasing price limit by 50%). If still no match exists, it halts and reports the failure.
  * *Example Test Output*:
    ```python
    # Running "Demonia under $40" (normal price $55) triggers price loosening to $60.00.
    # UI outputs listing with fallback alert:
    "⚠️ [Fallback Retry Active] Loosened price limit from $40.00 to $60.00"
    ```

---

### Spec Reflection

Our final implementation maps closely to our initial designs in `planning.md`:
* **Accuracies**: The keyword scoring logic, empty wardrobe fallback prompts, and state passing dictionary worked exactly as planned.
* **Refinement (Query Parsing)**: During implementation, we replaced custom string splitting and regex rules with a structured JSON-mode LLM call. This was much more robust at handling complex user expressions (like `"under $30"` or `"size 8.5"`).

---

### AI Usage Section

We leveraged AI development tools to assist with coding and design in the following specific instances:

1. **Structured Query Parser (`agent.py`)**
   * *Input*: Provided the LLM with query string inputs and requested a JSON schema with keys `description` (str), `size` (str/null), and `max_price` (float/null).
   * *Production*: Generated a completion leveraging Groq's JSON-object mode.
   * *Override*: Wrapped the parsing in a `try/except` fallback block to ensure that if the API call ever errors, it defaults to placing the raw user query inside the `description` field, preserving agent stability.

2. **Mermaid Diagram (`planning.md`)**
   * *Input*: Labeled flowchart nodes containing brackets, spaces, and colons.
   * *Production*: Initial nodes were drawn as `Tool1[Tool 1: search_listings]`.
   * *Override*: Hand-edited the diagram to place double quotes around labels, e.g. `Tool1["Tool 1: search_listings"]`, correcting a syntax rendering bug on GitHub.


