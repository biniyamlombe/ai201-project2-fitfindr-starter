"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json
from tools import search_listings, suggest_outfit, create_fit_card, compare_price, _get_groq_client


def _parse_query(query: str) -> dict:
    """
    Use Groq LLM to parse raw query string into a structured JSON dict.
    Returns: {"description": str, "size": str or null, "max_price": float or null}
    """
    client = _get_groq_client()
    
    prompt = (
        f"You are a parser. Analyze this clothing shopping request: \"{query}\"\n"
        f"Extract key search fields into JSON. Return ONLY a valid JSON object with these exact keys:\n"
        f"- \"description\": search keywords representing the item (e.g. \"vintage graphic tee\").\n"
        f"- \"size\": the size mentioned, formatted as a string (e.g. \"M\", \"W30\"), or null if none mentioned.\n"
        f"- \"max_price\": maximum price mentioned as a number/float, or null if none mentioned.\n\n"
        f"Example: \"vintage graphic tee under $30, size M\"\n"
        f"Output:\n"
        f'{{"description": "vintage graphic tee", "size": "M", "max_price": 30.0}}'
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise JSON extractor. Output valid raw JSON only, with no formatting, markdown code blocks, or extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        data = json.loads(response.choices[0].message.content.strip())
        return {
            "description": data.get("description") or query,
            "size": data.get("size"),
            "max_price": data.get("max_price")
        }
    except Exception:
        return {
            "description": query,
            "size": None,
            "max_price": None
        }


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "price_assessment": None,    # price comparison assessment
        "adjustments": [],           # logs constraint loosening details
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    # Step 1: Initialize the session with _new_session().
    session = _new_session(query, wardrobe)

    # Step 2: Parse the user's query to extract parameters.
    parsed = _parse_query(query)
    session["parsed"] = parsed

    desc = parsed.get("description") or query
    size = parsed.get("size")
    max_p = parsed.get("max_price")

    try:
        max_price = float(max_p) if max_p is not None else None
    except ValueError:
        max_price = None

    # Step 3: Call search_listings() with the parsed parameters.
    results = search_listings(desc, size=size, max_price=max_price)
    adjustments = []

    # Retry with loosened constraints if no exact matches found
    if not results:
        if size is not None:
            adjustments.append(f"Loosened size filter '{size}' to show alternatives")
            results = search_listings(desc, size=None, max_price=max_price)
        
        if not results and max_price is not None:
            new_max = max_price * 1.5
            adjustments.append(f"Loosened price limit from ${max_price:.2f} to ${new_max:.2f}")
            results = search_listings(desc, size=None, max_price=new_max)

    session["search_results"] = results
    session["adjustments"] = adjustments

    # If no results: set session["error"] to a helpful message and return early.
    if not results:
        session["error"] = "No matching items found for your search."
        return session

    # Step 4: Select the item to use (e.g., the top result).
    selected = results[0]
    session["selected_item"] = selected

    # Step 4.5: Calculate price assessment
    try:
        session["price_assessment"] = compare_price(selected)
    except Exception as e:
        session["price_assessment"] = f"Price comparison failed: {str(e)}"

    # Step 5: Call suggest_outfit() with the selected item and wardrobe.
    try:
        outfit = suggest_outfit(selected, wardrobe)
        session["outfit_suggestion"] = outfit
    except Exception as e:
        session["error"] = f"Failed to suggest outfit: {str(e)}"
        return session

    # Step 6: Call create_fit_card() with the outfit suggestion and selected item.
    try:
        fit_card = create_fit_card(outfit, selected)
        session["fit_card"] = fit_card
    except Exception as e:
        session["error"] = f"Failed to create fit card: {str(e)}"
        return session

    # Step 7: Return the session.
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
