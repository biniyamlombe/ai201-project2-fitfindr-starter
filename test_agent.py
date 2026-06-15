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
