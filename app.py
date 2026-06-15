"""
app.py

Gradio interface for FitFindr. Rebuilt to support a high-fidelity,
premium styling design matching the custom FitFindr mockups.
"""

import gradio as gr
import re

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# ── Color Resolution Helpers ──────────────────────────────────────────────────

COLOR_HEX_MAP = {
    "blue": "#475b75",
    "white": "#eae8e4",
    "black": "#2b2a28",
    "red": "#9c3b28",
    "green": "#527057",
    "yellow": "#ebd893",
    "cream": "#ebdcc5",
    "beige": "#ebdcc5",
    "grey": "#8c877f",
    "gray": "#8c877f",
    "brown": "#805235",
    "orange": "#b04c1c",
    "pink": "#d49fae",
    "purple": "#6a507a",
    "silver": "#d1cfca",
    "gold": "#ded9c3",
    "olive": "#606859"
}

def _resolve_color(color_name: str) -> str:
    if not color_name:
        return "#a84a15"
    color_name = color_name.lower().strip()
    for k, v in COLOR_HEX_MAP.items():
        if k in color_name:
            return v
    return "#a84a15"

def _truncate_name(name: str) -> str:
    words = name.split()
    if len(words) > 3:
        return " ".join(words[:2]) + "..."
    return name

def _get_category_svg(category: str) -> str:
    category = category.lower().strip()
    if "top" in category or "shirt" in category or "tee" in category:
        return """
        <svg viewBox="0 0 24 24" fill="none" stroke="#b04c1c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
            <path d="M20.59 13.41l-7.17-7.17a2 2 0 0 0-2.83 0L3.41 13.41A2 2 0 0 0 2 14.83V20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.17a2 2 0 0 0-.59-1.42z" />
            <path d="M12 2v4M9 5h6" />
        </svg>
        """
    elif "bottom" in category or "pant" in category or "jean" in category or "skirt" in category:
        return """
        <svg viewBox="0 0 24 24" fill="none" stroke="#b04c1c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
            <path d="M5 2h14v7l-2 13H7L5 9V2z" />
            <path d="M12 2v20M5 9h14" />
        </svg>
        """
    elif "outer" in category or "jacket" in category or "coat" in category:
        return """
        <svg viewBox="0 0 24 24" fill="none" stroke="#b04c1c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
            <path d="M2 6l10-3 10 3v13H2V6z" />
            <path d="M12 3v16M2 10h20" />
        </svg>
        """
    elif "shoe" in category or "boot" in category or "sneaker" in category:
        return """
        <svg viewBox="0 0 24 24" fill="none" stroke="#b04c1c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
            <path d="M3 18h18l-3-9h-7L7 14 3 14v4z" />
            <path d="M21 18v3h-3" />
        </svg>
        """
    else:
        return """
        <svg viewBox="0 0 24 24" fill="none" stroke="#b04c1c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
            <path d="M6 21V9a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1z" />
            <path d="M9 7V4a3 3 0 0 1 6 0v3" />
            <circle cx="12" cy="14" r="2" />
        </svg>
        """


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[dict, dict, dict, dict]:
    # 1. Guard against an empty query
    if not user_query or not user_query.strip():
        error_html = """
        <div class="ff-error-card">
            <div class="ff-error-icon">⚠️</div>
            <div class="ff-error-title">Empty Query</div>
            <div class="ff-error-text">Please enter a query to find items.</div>
        </div>
        """
        return (
            gr.update(value="", visible=False),
            gr.update(value=error_html, visible=True),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False)
        )

    # 2. Select the wardrobe
    if "example" in wardrobe_choice.lower():
        wardrobe = get_example_wardrobe()
    else:
        wardrobe = get_empty_wardrobe()

    # 3. Call run_agent()
    session = run_agent(user_query, wardrobe)

    # 4. Handle early exit error
    if session.get("error"):
        error_html = f"""
        <div class="ff-error-card">
            <div class="ff-error-icon">⚠️</div>
            <div class="ff-error-title">No matching items found</div>
            <div class="ff-error-text">Error: {session['error']}</div>
        </div>
        """
        return (
            gr.update(value="", visible=False),
            gr.update(value=error_html, visible=True),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False)
        )

    # 5. Extract item details
    item = session["selected_item"]
    condition = (item.get("condition") or "good").upper()
    price = item.get("price", 0.0)
    category = item.get("category", "tops")
    category_svg = _get_category_svg(category)
    brand = (item.get("brand") or "UNBRANDED").upper()
    tags = " • ".join(item.get("style_tags") or []).upper()
    meta_str = f"{brand} • {tags}" if tags else brand
    title = item.get("title", "Selected Thrift Find")
    size = item.get("size", "N/A")
    match_pct = 95 - int(price) % 10
    if match_pct > 99: match_pct = 99
    if match_pct < 85: match_pct = 85

    # Fallback retry warnings
    adjustments_html = ""
    if session.get("adjustments"):
        adj_list = "; ".join(session["adjustments"])
        adjustments_html = f"""
        <div class="fallback-alert">
            ⚠️ [Fallback Active] {adj_list}
        </div>
        """

    # Price assessment section
    price_assessment_html = ""
    if session.get("price_assessment"):
        price_assessment_html = f"""
        <div class="price-analysis-box">
            <div class="price-analysis-title">📊 Price Analysis</div>
            <div class="price-analysis-text">{session['price_assessment']}</div>
        </div>
        """

    card1_html = f"""
    {adjustments_html}
    <div class="ff-card">
        <div class="visual-area">
            <div class="condition-badge">{condition}</div>
            <button class="like-btn">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="none">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
            </button>
            <div class="category-visual">
                {category_svg}
                <span>{category.title()}</span>
            </div>
            <div class="price-tag">${price:.2f}</div>
        </div>
        <div class="item-meta">{meta_str}</div>
        <div class="item-title serif">{title}</div>
        <div class="badge-row">
            <span class="badge-tag">Size {size}</span>
            <span class="badge-tag">{item.get('condition', 'Good').title()}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:auto;">
            <a href="#" class="view-btn">View listing</a>
            <span class="match-pct">⚡ {match_pct}% match to your style</span>
        </div>
        {price_assessment_html}
    </div>
    """

    # ── CARD 2: OUTFIT SUGGESTION CARD ────────────────────────────────────────
    outfit_suggestion = session.get("outfit_suggestion", "")

    # Extract colors for blocks
    item_color_name = item.get("colors", ["orange"])[0]
    item_hex = _resolve_color(item_color_name)
    item_cat = item.get("category", "find")

    color_blocks_data = [
        {"color": item_hex, "label": f"This {item_cat}"}
    ]

    # Extract up to 2 items from user's wardrobe that are mentioned in the outfit text
    suggested_wardrobe_items = []
    outfit_lower = outfit_suggestion.lower()
    for w_item in wardrobe.get("items", []):
        name = w_item.get("name", "")
        keywords = [w.lower() for w in name.split() if len(w) > 3]
        if any(kw in outfit_lower for kw in keywords):
            suggested_wardrobe_items.append(w_item)
            if len(suggested_wardrobe_items) == 2:
                break

    if len(suggested_wardrobe_items) < 2:
        for w_item in wardrobe.get("items", []):
            if w_item not in suggested_wardrobe_items:
                suggested_wardrobe_items.append(w_item)
                if len(suggested_wardrobe_items) == 2:
                    break

    for w_item in suggested_wardrobe_items:
        w_color_name = w_item.get("colors", ["cream"])[0]
        w_hex = _resolve_color(w_color_name)
        color_blocks_data.append({
            "color": w_hex,
            "label": _truncate_name(w_item.get("name", "Wardrobe item"))
        })

    color_blocks_html = ""
    for block in color_blocks_data:
        color_blocks_html += f"""
        <div class="color-card">
            <div class="color-block" style="background-color: {block['color']};"></div>
            <div class="color-label">{block['label']}</div>
        </div>
        """

    card2_html = f"""
    <div class="ff-card">
        <div class="section-meta">Outfit Idea</div>
        <div class="section-title serif">Styled Look</div>
        <div class="color-blocks">
            {color_blocks_html}
        </div>
        <div class="outfit-text">
            {outfit_suggestion}
        </div>
    </div>
    """

    # ── CARD 3: FIT CARD ──────────────────────────────────────────────────────
    fit_card = session.get("fit_card", "")

    # Sizing Grid
    top_size = "M"
    bottom_size = "30"
    shoe_size = "8"

    cat = item.get("category", "")
    size = item.get("size", "")
    if cat == "tops" or cat == "outerwear":
        top_size = size
    elif cat == "bottoms":
        bottom_size = size
    elif cat == "shoes":
        shoe_size = size

    for w_item in wardrobe.get("items", []):
        w_cat = w_item.get("category", "")
        notes = (w_item.get("notes") or "").lower()
        m = re.search(r'size\s+([a-zA-Z0-9]+)', notes)
        w_size = m.group(1).upper() if m else None

        if w_cat == "tops" and not (cat == "tops" or cat == "outerwear"):
            top_size = w_size or top_size
        elif w_cat == "bottoms" and not cat == "bottoms":
            bottom_size = w_size or bottom_size
        elif w_cat == "shoes" and not cat == "shoes":
            shoe_size = w_size or shoe_size

    # Fit Vibe Title / Vibe Word
    vibe_word = "Vintage Vibe"
    for tag in item.get("style_tags", []):
        if len(tag) > 3:
            vibe_word = tag.title() + " Style"
            break

    fit_pref = "Relaxed"
    if "baggy" in outfit_lower or "oversized" in outfit_lower:
        fit_pref = "Relaxed"
    elif "slim" in outfit_lower or "fit" in outfit_lower:
        fit_pref = "Slim"
    elif "classic" in outfit_lower:
        fit_pref = "Classic"

    palette_html = ""
    for block in color_blocks_data:
        palette_html += f'<div class="palette-circle" style="background-color: {block["color"]};"></div>'
    palette_html += '<div class="palette-circle" style="background-color: #222222;"></div>'

    card3_html = f"""
    <div class="ff-card">
        <div class="section-meta">Your Fit Card</div>
        <div class="section-title serif">{vibe_word}</div>
        <div class="size-grid">
            <div class="size-box">
                <span class="size-box-label">Tops</span>
                <span class="size-box-val">{top_size}</span>
            </div>
            <div class="size-box">
                <span class="size-box-label">Bottoms</span>
                <span class="size-box-val">{bottom_size}</span>
            </div>
            <div class="size-box">
                <span class="size-box-label">Shoes</span>
                <span class="size-box-val">{shoe_size}</span>
            </div>
        </div>
        <div class="fit-pref-row">
            <span class="fit-pref-label">Fit preference</span>
            <span class="fit-pref-badge">{fit_pref}</span>
        </div>
        <div class="palette-row">
            <span class="fit-pref-label">Palette</span>
            <div class="palette-circles">
                {palette_html}
            </div>
        </div>
        <div class="fit-caption">
            {fit_card}
        </div>
        <div class="card-footer-tag">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
            <span>{vibe_word.lower()} • lived-in</span>
        </div>
    </div>
    """

    results_header = f'<div class="match-header-text serif">Top match <span>for "{user_query}"</span></div>'

    return (
        gr.update(value=results_header, visible=True),
        gr.update(value=card1_html, visible=True),
        gr.update(value=card2_html, visible=True),
        gr.update(value=card3_html, visible=True)
    )


# ── interface ─────────────────────────────────────────────────────────────────

def build_interface():
    # Premium visual design style sheet matching custom screenshot aesthetics
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    .gradio-container {
        background-color: #dedad2 !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        color: #2c2b29 !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 32px 24px !important;
    }
    
    .serif {
        font-family: 'Playfair Display', Georgia, serif !important;
    }

    /* Header Navigation bar */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        border-bottom: 1px solid rgba(0,0,0,0.05);
        padding-bottom: 16px;
    }
    .header-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 24px;
        font-weight: 700;
        color: #a84a15;
        text-decoration: none;
    }
    .header-nav {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .header-nav a {
        color: #4f4d49;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
    }
    .header-nav a:hover {
        color: #2c2b29;
    }
    .saved-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        background-color: #e8e4dc;
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        color: #2c2b29;
    }
    .saved-btn .badge {
        background-color: #a84a15;
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 600;
        margin-left: 2px;
    }

    /* Hero section */
    .hero-section {
        margin-bottom: 32px;
    }
    .hero-section h1 {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 44px;
        font-weight: 600;
        color: #2c2b29;
        margin: 0 0 12px 0;
        line-height: 1.2;
    }
    .hero-section h1 em {
        font-style: italic;
        color: #a84a15;
    }
    .hero-section p {
        font-size: 16px;
        color: #5e5a52;
        margin: 0;
        max-width: 650px;
        line-height: 1.5;
    }

    /* Card block wrapping search input and configurations */
    .search-card {
        background-color: #eae6dc !important;
        border-radius: 18px !important;
        padding: 24px !important;
        border: 1px solid rgba(0,0,0,0.04) !important;
        box-shadow: 0 4px 30px rgba(0,0,0,0.02) !important;
        margin-bottom: 40px !important;
    }

    #search-box-row {
        background-color: white !important;
        border-radius: 30px !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
        padding: 4px 6px 4px 16px !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.02) !important;
        gap: 8px !important;
        width: 100% !important;
    }
    
    #query-input {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        flex-grow: 1 !important;
    }
    #query-input textarea, #query-input input {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        font-size: 16px !important;
        color: #2c2b29 !important;
        padding: 0 !important;
        height: 24px !important;
    }

    #find-btn {
        background-color: #a84a15 !important;
        color: white !important;
        border-radius: 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        border: none !important;
        height: 40px !important;
        padding: 0 24px !important;
        cursor: pointer !important;
        transition: background-color 0.2s !important;
    }
    #find-btn:hover {
        background-color: #8f3d0f !important;
    }

    /* Style Gradio Radio as segmented pills */
    #wardrobe-choice {
        display: flex !important;
        gap: 8px !important;
    }
    #wardrobe-choice .wrap {
        display: flex !important;
        flex-direction: row !important;
        gap: 8px !important;
    }
    #wardrobe-choice label {
        background-color: transparent !important;
        border: 1px solid rgba(0,0,0,0.06) !important;
        border-radius: 20px !important;
        padding: 6px 16px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #4f4d49 !important;
        cursor: pointer !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
    }
    #wardrobe-choice label:hover {
        background-color: rgba(0,0,0,0.02) !important;
    }
    #wardrobe-choice input[type="radio"] {
        display: none !important;
    }
    #wardrobe-choice label.selected {
        background-color: white !important;
        border-color: rgba(0,0,0,0.04) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        color: #2c2b29 !important;
        font-weight: 600 !important;
    }

    /* Clickable Examples Try list */
    .try-row {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        flex-wrap: wrap !important;
        margin-top: 16px !important;
    }
    .try-btn {
        background-color: #e2ddd5 !important;
        border: 1px solid rgba(0,0,0,0.04) !important;
        border-radius: 20px !important;
        padding: 4px 14px !important;
        font-size: 13px !important;
        color: #2c2b29 !important;
        cursor: pointer !important;
        box-shadow: none !important;
        transition: all 0.2s !important;
        font-weight: 500 !important;
        border-style: none !important;
    }
    .try-btn:hover {
        background-color: #ded9cd !important;
    }

    /* Search Results Header */
    .match-header-text {
        font-size: 28px;
        font-weight: 600;
        color: #2c2b29;
        margin-bottom: 24px;
        margin-top: 12px;
    }
    .match-header-text span {
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        font-size: 14px;
        font-weight: 500;
        color: #706b61;
        margin-left: 8px;
    }

    /* Three column results grid layout */
    .results-grid {
        display: flex !important;
        flex-direction: row !important;
        gap: 24px !important;
        align-items: stretch !important;
        width: 100% !important;
    }

    /* Custom Cards */
    .ff-card {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 4px 30px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.03);
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
        flex: 1;
    }

    /* Card 1: Listing Visual Area */
    .visual-area {
        background-color: #f2efea;
        border-radius: 12px;
        height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        margin-bottom: 20px;
    }
    .condition-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background-color: #ffffff;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #2c2b29;
    }
    .like-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        background-color: #ffffff;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #a84a15;
    }
    .price-tag {
        position: absolute;
        bottom: 12px;
        right: 12px;
        background-color: #1e1d1b;
        color: white;
        padding: 6px 14px;
        border-radius: 8px;
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 18px;
        font-weight: 700;
    }
    .category-visual {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .category-visual svg {
        stroke: #b04c1c;
    }
    .category-visual span {
        font-size: 12px;
        font-weight: 600;
        color: #706b61;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .item-meta {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: #a84a15;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .item-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 22px;
        font-weight: 600;
        color: #2c2b29;
        margin: 0 0 12px 0;
        line-height: 1.3;
    }
    .badge-row {
        display: flex;
        gap: 6px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .badge-tag {
        background-color: #f2efea;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        color: #5e5a52;
    }
    .view-btn {
        background-color: #a84a15;
        color: white !important;
        text-decoration: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        text-align: center;
        transition: background-color 0.2s;
        display: inline-block;
        border-style: none !important;
    }
    .view-btn:hover {
        background-color: #8f3d0f;
    }
    .match-pct {
        font-size: 12px;
        font-weight: 500;
        color: #706b61;
    }

    /* Card 2: Outfit suggestion colors */
    .section-meta {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: #a84a15;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .section-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 22px;
        font-weight: 600;
        color: #2c2b29;
        margin: 0 0 20px 0;
    }
    .color-blocks {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
    }
    .color-card {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        min-width: 0;
    }
    .color-block {
        width: 100%;
        height: 64px;
        border-radius: 8px;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .color-label {
        font-size: 11px;
        font-weight: 500;
        color: #706b61;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    .outfit-text {
        font-size: 14px;
        line-height: 1.6;
        color: #4f4d49;
    }

    /* Card 3: Fit Card Details */
    .size-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .size-box {
        background-color: #f2efea;
        border-radius: 8px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .size-box-label {
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #706b61;
        text-transform: uppercase;
    }
    .size-box-val {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 20px;
        font-weight: 600;
        color: #2c2b29;
    }
    .fit-pref-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        font-size: 14px;
    }
    .fit-pref-label {
        color: #706b61;
    }
    .fit-pref-badge {
        background-color: #ebdcc5;
        color: #a84a15;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 700;
    }
    .palette-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        font-size: 14px;
    }
    .palette-circles {
        display: flex;
        gap: 6px;
    }
    .palette-circle {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .fit-caption {
        font-size: 14px;
        line-height: 1.6;
        color: #4f4d49;
        background-color: #fcfbfa;
        border-left: 3px solid #ebdcc5;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
        font-style: italic;
    }
    .card-footer-tag {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #706b61;
        margin-top: auto;
        border-top: 1px solid #f2efea;
        padding-top: 12px;
    }

    /* Fallback Warning Box */
    .fallback-alert {
        background-color: #fdf5e2;
        border-left: 4px solid #f0ad4e;
        color: #8a6d3b;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-size: 14px;
        font-weight: 500;
    }

    /* Price assessment section inside Listing Card */
    .price-analysis-box {
        margin-top: 20px;
        border-top: 1px dashed #dedad2;
        padding-top: 16px;
    }
    .price-analysis-title {
        font-size: 10px;
        font-weight: 700;
        color: #a84a15;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .price-analysis-text {
        font-size: 13px;
        line-height: 1.5;
        color: #5e5a52;
    }

    /* Error Card */
    .ff-error-card {
        grid-column: span 3;
        background-color: #fdf2f2 !important;
        border: 1px solid #fbd5d5 !important;
        border-radius: 18px !important;
        padding: 32px !important;
        text-align: center;
        color: #9b1c1c;
        width: 100% !important;
    }
    .ff-error-icon {
        font-size: 48px;
        margin-bottom: 16px;
    }
    .ff-error-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .ff-error-text {
        font-size: 16px;
        max-width: 500px;
        margin: 0 auto;
    }
    """

    with gr.Blocks(title="FitFindr", css=css) as demo:
        # Header Nav HTML
        gr.HTML("""
        <div class="header-row">
            <div class="header-logo">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <path d="M16 10a4 4 0 0 1-8 0"></path>
                </svg>
                <span>FitFindr</span>
            </div>
            <div class="header-nav">
                <a href="#">How it works</a>
                <button class="saved-btn">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 2px;">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                    Saved <span class="badge">3</span>
                </button>
            </div>
        </div>
        
        <div class="hero-section">
            <h1 class="serif">Find your next <em>secondhand</em> favorite.</h1>
            <p>Describe what you want — size, price, vibe — and we'll surface the best listing, an outfit built from your wardrobe, and a fit card that's all you.</p>
        </div>
        """)

        # Search Panel Container Card
        with gr.Column(elem_classes="search-card"):
            with gr.Row(elem_id="search-box-row"):
                query_input = gr.Textbox(
                    show_label=False,
                    placeholder="e.g. vintage graphic tee under $30, size M",
                    elem_id="query-input",
                    container=False,
                    scale=5
                )
                submit_btn = gr.Button("Find it", elem_id="find-btn", scale=1)
                
            with gr.Row(elem_classes="wardrobe-row", style="margin-top: 16px; align-items: center;"):
                gr.HTML("<span style='font-size: 14px; font-weight: 500; color: #706b61; margin-right: 12px;'>Wardrobe</span>")
                wardrobe_choice = gr.Radio(
                    choices=["Example wardrobe", "Empty wardrobe (new user)"],
                    value="Example wardrobe",
                    show_label=False,
                    elem_id="wardrobe-choice",
                    container=False
                )
                
            with gr.Row(elem_classes="try-row"):
                gr.HTML("<span style='font-size: 14px; font-weight: 500; color: #706b61; margin-right: 8px;'>Try</span>")
                example1 = gr.Button("vintage graphic tee • $30", elem_classes="try-btn")
                example2 = gr.Button("90s track jacket • M", elem_classes="try-btn")
                example3 = gr.Button("flowy midi skirt • $40", elem_classes="try-btn")
                example4 = gr.Button("black combat boots • 8", elem_classes="try-btn")
                example5 = gr.Button("designer ballgown • XXS • $5", elem_classes="try-btn")

        # Dynamic Results Header
        results_header_output = gr.HTML(visible=False)

        # Dynamic Outputs Grid
        with gr.Row(elem_classes="results-grid"):
            listing_output = gr.HTML(visible=False, elem_id="listing-html")
            outfit_output = gr.HTML(visible=False, elem_id="outfit-html")
            fitcard_output = gr.HTML(visible=False, elem_id="fitcard-html")

        # Wire Submit Event Handler
        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )

        # Wire click shortcuts for Try buttons
        example1.click(fn=lambda: "vintage graphic tee under $30", outputs=query_input).then(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )
        example2.click(fn=lambda: "90s track jacket in size M", outputs=query_input).then(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )
        example3.click(fn=lambda: "flowy midi skirt under $40", outputs=query_input).then(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )
        example4.click(fn=lambda: "black combat boots size 8", outputs=query_input).then(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )
        example5.click(fn=lambda: "designer ballgown size XXS under $5", outputs=query_input).then(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[results_header_output, listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
