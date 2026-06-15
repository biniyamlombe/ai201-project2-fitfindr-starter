import pytest
from tools import search_listings

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
