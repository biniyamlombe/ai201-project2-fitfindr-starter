import sys
sys.path.append("/Users/biniyamlombe/ai201-project2-fitfindr-starter")

from agent import run_agent
from utils.data_loader import get_example_wardrobe

# Run happy path
print("=== Running Happy Path Query ===")
query = "looking for a vintage graphic tee under $30"
session = run_agent(query=query, wardrobe=get_example_wardrobe())

print(f"\n1. State Verification:")
print(f"   Original Query: {session['query']}")
print(f"   Parsed Parameters: {session['parsed']}")
print(f"   Selected Item (id): {session['selected_item']['id'] if session['selected_item'] else None}")
print(f"   Selected Item (Title): {session['selected_item']['title'] if session['selected_item'] else None}")
print(f"   Selected Item (Price): ${session['selected_item']['price'] if session['selected_item'] else None}")
print(f"   Outfit Suggestion Length: {len(session['outfit_suggestion']) if session['outfit_suggestion'] else 0} chars")
print(f"   Fit Card: {session['fit_card']}")
print(f"   Error: {session['error']}")

# Verify that the outfit went to fit card input
assert session["selected_item"] is not None
assert session["outfit_suggestion"] is not None
assert session["fit_card"] is not None
print("\n[SUCCESS] Happy Path State Verification Passed!")

print("\n=== Running No-Results Path Query ===")
query2 = "designer ballgown size XXS under $5"
session2 = run_agent(query=query2, wardrobe=get_example_wardrobe())
print(f"   Original Query: {session2['query']}")
print(f"   Error Message: {session2['error']}")
print(f"   Selected Item: {session2['selected_item']}")
print(f"   Outfit Suggestion: {session2['outfit_suggestion']}")
print(f"   Fit Card: {session2['fit_card']}")

# Verify branching behavior
assert session2["error"] == "No matching items found for your search."
assert session2["selected_item"] is None
assert session2["outfit_suggestion"] is None
assert session2["fit_card"] is None
print("\n[SUCCESS] No-Results Branch Verification Passed!")
