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

### Planning Loop

FitFindr uses a sequential planning loop built on top of state management across a single session:
1. **Query Parsing**: A specialized `llama-3.3-70b-versatile` LLM parser processes raw natural language inputs to extract structured parameters (`description`, `size`, `max_price`) as JSON attributes.
2. **Search Execution**: It executes `search_listings` using the parsed criteria.
3. **Branching/Guard Check**: If no relevant items are retrieved, the agent halts early, records the reason in the session state, and reports it.
4. **Outfit Suggestions**: It selects the top search match and triggers `suggest_outfit` alongside the user's wardrobe details.
5. **Fit Card Generation**: Finally, it triggers `create_fit_card` using the styled outfit output and the selected item to generate a shareable social media OOTD caption.

### Error Handling Strategy

Each tool features standalone fallback handlers:
* **search_listings**: Returns an empty list `[]` on failure/no-match, allowing the planning loop to catch this condition, set a helpful error message (`"No matching items found for your search."`), and terminate execution early.
* **suggest_outfit**: If the wardrobe is empty, it bypasses specific garment pairings and instructs the LLM to write general styling tips and aesthetic vibes for the new item. If LLM calls fail, it catches exceptions and writes an error message to the session state.
* **create_fit_card**: Validates inputs. If the outfit input is blank, it returns a descriptive error string: `"Error: Cannot generate fit card due to missing outfit details."` instead of crashing.

