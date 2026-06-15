import pytest
from tools import search_listings, suggest_outfit, create_fit_card

def test_search_listings_basic():
    # Test keyword matching
    results = search_listings("vintage graphic tee")
    assert len(results) > 0
    # The top result should contain relevant terms
    top = results[0]
    comb_text = f"{top['title']} {top['description']} {' '.join(top.get('style_tags', []))}".lower()
    assert any(word in comb_text for word in ["vintage", "graphic", "tee"])

def test_search_listings_price_filter():
    # Limit to max price of $20
    results = search_listings("vintage graphic tee", max_price=20.0)
    for item in results:
        assert item["price"] <= 20.0

def test_search_listings_size_filter():
    # Filter by size 'M'
    results = search_listings("vintage graphic tee", size="M")
    for item in results:
        assert "m" in item["size"].lower()

def test_search_listings_no_results():
    # A query designed to return nothing
    results = search_listings("designer ballgown", size="XXS", max_price=5.0)
    assert results == []

def test_suggest_outfit_empty():
    from utils.data_loader import get_empty_wardrobe
    new_item = {
        "title": "Vintage Levi's 501 Jeans — Medium Wash",
        "description": "Classic 501s in a perfect medium wash. Some light fading at the knees.",
        "category": "bottoms",
        "style_tags": ["vintage", "classic", "denim"],
        "size": "W30 L30",
        "condition": "good",
        "price": 38.00,
        "colors": ["blue"],
        "brand": "Levi's",
        "platform": "depop"
    }
    empty_wardrobe = get_empty_wardrobe()
    suggestion = suggest_outfit(new_item, empty_wardrobe)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0

def test_suggest_outfit_populated():
    from utils.data_loader import get_example_wardrobe
    new_item = {
        "title": "Vintage Levi's 501 Jeans — Medium Wash",
        "description": "Classic 501s in a perfect medium wash. Some light fading at the knees.",
        "category": "bottoms",
        "style_tags": ["vintage", "classic", "denim"],
        "size": "W30 L30",
        "condition": "good",
        "price": 38.00,
        "colors": ["blue"],
        "brand": "Levi's",
        "platform": "depop"
    }
    wardrobe = get_example_wardrobe()
    suggestion = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0

def test_create_fit_card_error():
    new_item = {
        "title": "Vintage Levi's 501 Jeans — Medium Wash",
        "price": 38.00,
        "platform": "depop"
    }
    # Test blank outfit guard
    res = create_fit_card("", new_item)
    assert "Error" in res

def test_create_fit_card_success():
    new_item = {
        "title": "Vintage Levi's 501 Jeans — Medium Wash",
        "price": 38.00,
        "platform": "depop"
    }
    outfit = "Pair this with your dark wash baggy straight-leg jeans for a relaxed streetwear vibe."
    caption = create_fit_card(outfit, new_item)
    assert isinstance(caption, str)
    assert len(caption) > 0
    caption_lower = caption.lower()
    assert "depop" in caption_lower or "38" in caption_lower

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)
