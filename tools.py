"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Load all listings
    listings = load_listings()
    
    # 2. Filter by max_price and size (if provided)
    filtered_listings = []
    for listing in listings:
        # Check max_price
        if max_price is not None:
            if listing.get("price", 0.0) > max_price:
                continue
        
        # Check size
        if size is not None:
            listing_size = listing.get("size")
            if not listing_size or size.lower() not in listing_size.lower():
                continue
                
        filtered_listings.append(listing)
        
    # 3. Score each remaining listing by keyword overlap with `description`
    # Clean and split the query description into lowercase words
    query_words = [w.strip(".,!?\"'()").lower() for w in description.split()]
    query_words = [w for w in query_words if w]
    
    if not query_words:
        # If no keywords, everything has score 0, return empty list
        return []
        
    scored_listings = []
    for listing in filtered_listings:
        # Combine listing fields to check for keyword overlap
        brand = listing.get("brand") or ""
        tags = " ".join(listing.get("style_tags", []))
        title = listing.get("title") or ""
        desc = listing.get("description") or ""
        cat = listing.get("category") or ""
        
        combined_text = f"{title} {desc} {cat} {tags} {brand}".lower()
        
        # Compute overlap score
        score = sum(1 for word in set(query_words) if word in combined_text)
        
        if score > 0:
            scored_listings.append((score, listing))
            
    # 4. Sort by score, highest first
    scored_listings.sort(key=lambda x: x[0], reverse=True)
    
    # 5. Return the listing dicts
    return [listing for score, listing in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # 1. Check whether wardrobe['items'] is empty.
    items = wardrobe.get("items", [])
    client = _get_groq_client()
    
    item_details = (
        f"Title: {new_item.get('title')}\n"
        f"Description: {new_item.get('description')}\n"
        f"Category: {new_item.get('category')}\n"
        f"Price: ${new_item.get('price')}\n"
        f"Size: {new_item.get('size')}\n"
        f"Brand: {new_item.get('brand') or 'N/A'}\n"
        f"Style Tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}"
    )

    if not items:
        # 2. If empty: call the LLM with a prompt for general styling ideas
        prompt = (
            f"The user is considering buying the following thrifted item:\n"
            f"{item_details}\n\n"
            f"The user's wardrobe is currently empty. Please provide general styling advice, "
            f"suggesting what kinds of items pair well, what color palettes/vibes it suits, and how to style it."
        )
    else:
        # 3. If not empty: format the wardrobe items into a prompt
        wardrobe_list = []
        for idx, w_item in enumerate(items, 1):
            w_tags = ", ".join(w_item.get("style_tags", []))
            w_colors = ", ".join(w_item.get("colors", []))
            notes = f" (Notes: {w_item.get('notes')})" if w_item.get("notes") else ""
            wardrobe_list.append(
                f"- {w_item.get('name')} [Category: {w_item.get('category')}, Colors: {w_colors}, Tags: {w_tags}]{notes}"
            )
        wardrobe_details = "\n".join(wardrobe_list)
        
        prompt = (
            f"The user is considering buying the following thrifted item:\n"
            f"{item_details}\n\n"
            f"Here is the user's existing wardrobe:\n"
            f"{wardrobe_details}\n\n"
            f"Please suggest 1-2 complete outfit combinations pairing the new thrifted item with specific named "
            f"pieces from their wardrobe. Be clear, creative, and style-conscious."
        )

    # 4. Return the LLM's response as a string
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are FitFindr, an expert personal fashion stylist and thrifting assistant. Provide clear, inspiring, and concise outfit suggestions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # 1. Guard against an empty or whitespace-only outfit string.
    if not outfit or not outfit.strip():
        return "Error: Cannot generate fit card due to missing outfit details."

    client = _get_groq_client()

    # Extract item details
    title = new_item.get("title", "this piece")
    price = f"${new_item.get('price', 0.0):.2f}"
    platform = new_item.get("platform", "thrift platform")

    prompt = (
        f"Write a short, casual OOTD social media caption for a thrifted find.\n\n"
        f"Thrifted find details:\n"
        f"- Item: {title}\n"
        f"- Price: {price}\n"
        f"- Platform: {platform}\n\n"
        f"Styled outfit description:\n"
        f"{outfit}\n\n"
        f"Create a caption matching these guidelines:\n"
        f"- Length: 2 to 4 sentences.\n"
        f"- Tone: Casual, authentic OOTD post (no corporate sales pitch).\n"
        f"- References: Mention the item name, price, and platform naturally exactly once each."
    )

    # 3. Call the LLM and return the response.
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a fashion influencer sharing a styling tip. Write short, engaging social media captions (2-4 sentences max)."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.95,
    )
    return response.choices[0].message.content.strip()


# ── Stretch Tool: compare_price ───────────────────────────────────────────────

def compare_price(item: dict) -> str:
    """
    Given an item, estimates whether the price is fair based on comparable
    listings in the dataset of the same category, returning LLM price reasoning.
    """
    try:
        listings = load_listings()
        cat = item.get("category")
        if not cat:
            return "Unable to determine category for price comparison."

        # Filter items in the same category
        comp_listings = [lst for lst in listings if lst.get("category") == cat]
        if not comp_listings:
            comp_listings = [item]

        prices = [lst.get("price", 0.0) for lst in comp_listings if lst.get("price") is not None]
        if not prices:
            return f"No pricing data available for category '{cat}'."

        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        item_price = item.get("price", 0.0)
        item_title = item.get("title", "this item")
        item_brand = item.get("brand") or "N/A"

        # Build prompt for LLM price assessment
        prompt = (
            f"Compare the price of this thrifted item against statistics for the category '{cat}':\n"
            f"- Target Item: {item_title} (Brand: {item_brand})\n"
            f"- Target Price: ${item_price:.2f}\n\n"
            f"Category Statistics for '{cat}':\n"
            f"- Average Price: ${avg_price:.2f}\n"
            f"- Minimum Price: ${min_price:.2f}\n"
            f"- Maximum Price: ${max_price:.2f}\n\n"
            f"Write a 2-3 sentence price assessment for a shopper. Explain if the price is a bargain, "
            f"fair, or slightly expensive compared to the average, and include style-conscious brand value reasoning. "
            f"Keep it brief and helpful."
        )

        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are FitFindr, an expert thrift shopper and price analyst. Write a concise, style-aware price evaluation (2-3 sentences max)."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback string on failure
        return (
            f"This item is priced at ${item.get('price', 0.0):.2f}. Comparable items in the category "
            f"'{item.get('category')}' range from ${min(prices):.2f} to ${max(prices):.2f} "
            f"(average: ${sum(prices)/len(prices):.2f})."
        )
