import pytest
from agent import run_agent
from utils.data_loader import get_example_wardrobe

def test_run_agent_happy_path():
    # Test graphic tee happy path
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] is None
    assert session["selected_item"] is not None
    assert session["outfit_suggestion"] is not None
    assert session["fit_card"] is not None
    assert len(session["search_results"]) > 0
    assert session["parsed"]["max_price"] == 30.0

def test_run_agent_no_results():
    # Test no results early exit
    session = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] == "No matching items found for your search."
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None

def test_handle_query_happy_path():
    from app import handle_query
    listing_text, outfit_suggestion, fit_card = handle_query(
        "vintage graphic tee under $30", "Example wardrobe"
    )
    assert "Title:" in listing_text
    assert len(outfit_suggestion) > 0
    assert len(fit_card) > 0

def test_handle_query_empty_query():
    from app import handle_query
    listing_text, outfit_suggestion, fit_card = handle_query("", "Example wardrobe")
    assert "Please enter a query" in listing_text
    assert outfit_suggestion == ""
    assert fit_card == ""

def test_handle_query_no_results():
    from app import handle_query
    listing_text, outfit_suggestion, fit_card = handle_query(
        "designer ballgown size XXS under $5", "Example wardrobe"
    )
    assert "Error:" in listing_text
    assert outfit_suggestion == ""
    assert fit_card == ""

def test_agent_retry_size_fallback():
    # Attempting to search for Demonia in size XXL (doesn't exist; listing lst_009 is size US 7)
    session = run_agent(
        query="Demonia in size XXL under $80",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] is None
    assert session["selected_item"] is not None
    # Verify that the size constraint was dropped/loosened
    assert any("size" in adj.lower() for adj in session["adjustments"])

def test_agent_retry_price_fallback():
    # Attempting to search for Demonia under $40 (normal price is $55.00)
    session = run_agent(
        query="Demonia under $40",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] is None
    assert session["selected_item"] is not None
    # Verify that the price constraint was loosened
    assert any("price" in adj.lower() for adj in session["adjustments"])
