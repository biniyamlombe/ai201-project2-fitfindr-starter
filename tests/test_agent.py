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
    header, listing, outfit, fit_card = handle_query(
        "vintage graphic tee under $30", "Example wardrobe"
    )
    assert "Single-Stitch" in listing["value"] or "Tee" in listing["value"]
    assert "Styled Look" in outfit["value"]
    assert "Fit Card" in fit_card["value"]

def test_handle_query_empty_query():
    from app import handle_query
    header, listing, outfit, fit_card = handle_query("", "Example wardrobe")
    assert "Empty Query" in listing["value"]
    assert outfit.get("visible") is False
    assert fit_card.get("visible") is False

def test_handle_query_no_results():
    from app import handle_query
    header, listing, outfit, fit_card = handle_query(
        "designer ballgown size XXS under $5", "Example wardrobe"
    )
    assert "No matching items found" in listing["value"]
    assert outfit.get("visible") is False
    assert fit_card.get("visible") is False

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
