# Library Audiobook Availability Checker

Check which audiobooks from the Western Cape Provincial Library are currently available to borrow. Supports finding audiobooks from multiple sources:

- **BBC World Book Club** podcast episodes
- **Hugo Award for Best Novel** nominees and winners
- **Booker Prize** winners, shortlists, and longlists

## Quick Start

```bash
# Complete workflow for Hugo Award authors
python workflow.py --source hugo

# Complete workflow for all sources (BBC, Hugo, and Booker)
python workflow.py --source all

# Or check individual books/authors:
python check_single_book.py 8919230
python check_by_author.py "Agatha Christie"
```

## Scripts

### Automated Workflow

**`workflow.py`** - Complete end-to-end workflow

```bash
# Hugo Award authors only
python workflow.py --source hugo

# BBC World Book Club only
python workflow.py --source bbc

# Booker Prize only
python workflow.py --source booker

# All sources (default)
python workflow.py --source all

# Run specific stages only
python workflow.py --stages scrape search

# Skip scraping (use existing data)
python workflow.py --skip-scrape
```

### Data Collection

**`scrape_hugo_awards.py`** - Scrape Hugo Award nominees from Wikipedia

```bash
python scrape_hugo_awards.py
# Creates: data/hugo_award_nominees.json, data/hugo_award_authors.json
```

**`scrape_booker_prize.py`** - Scrape Booker Prize nominees from Wikipedia

```bash
python scrape_booker_prize.py
# Creates: data/booker_prize_nominees.json, data/booker_prize_authors.json
```

**`scrape_episodes.py`** - Scrape BBC World Book Club episodes

```bash
python scrape_episodes.py
# Creates: data/bbc_world_book_club_episodes.json
```

**`search_combined.py`** - Search library for audiobooks by authors

```bash
# Search Hugo authors
python search_combined.py --source hugo

# Search Booker Prize authors
python search_combined.py --source booker

# Search all sources
python search_combined.py --source all --delay 2.0
```

### Availability Checking

**`check_single_book.py`** - Test one book by ID

```bash
python check_single_book.py <book_id>
```

**`check_by_author.py`** - Check one author's books

```bash
python check_by_author.py "Author Name"
```

**`check_availability.py`** - Check all books

```bash
python check_availability.py [--input file.json] [--output results.json] [--delay 0.5]
```

## How It Works

Fetches each book's page from `https://westerncape.overdrive.com/media/{book_id}` and parses the HTML to extract `"availableCopies"` and `"ownedCopies"`.

## Output Format

```
[42/150] Checking: Paradise by Abdulrazak Gurnah... ✓ AVAILABLE (1/1)
```

- `(1/1)` = 1 available copy out of 1 total
- `(0/1)` = All copies checked out

Results are saved to `data/available_audiobooks.json` with borrowing URLs.

## Full Workflow

The complete pipeline works with multiple data sources:

### Option 1: Automated Workflow (Recommended)

```bash
# Run everything for Hugo Award authors
python workflow.py --source hugo

# Run everything for Booker Prize authors
python workflow.py --source booker

# Run everything for all sources
python workflow.py --source all
```

### Option 2: Manual Step-by-Step

**For Hugo Award Authors:**

```bash
# 1. Scrape Hugo Award nominees from Wikipedia
python scrape_hugo_awards.py
# Creates: data/hugo_award_nominees.json, data/hugo_award_authors.json

# 2. Search for audiobooks in the library
python search_combined.py --source hugo
# Creates: data/hugo_audiobook_search_results.json

# 3. Refine the search results (filter by author matching)
python refine_audiobooks.py --input data/hugo_audiobook_search_results.json
# Creates: data/hugo_audiobook_search_results_refined.json

# 4. Check which books are currently available
python check_availability.py --input data/hugo_audiobook_search_results_refined.json
# Creates: data/hugo_available_audiobooks.json
```

**For Booker Prize Authors:**

```bash
# 1. Scrape Booker Prize nominees from Wikipedia
python scrape_booker_prize.py
# Creates: data/booker_prize_nominees.json, data/booker_prize_authors.json

# 2. Search for audiobooks in the library
python search_combined.py --source booker
# Creates: data/booker_audiobook_search_results.json

# 3. Refine the search results
python refine_audiobooks.py --input data/booker_audiobook_search_results.json
# Creates: data/booker_audiobook_search_results_refined.json

# 4. Check which books are currently available
python check_availability.py --input data/booker_audiobook_search_results_refined.json
# Creates: data/booker_available_audiobooks.json
```

**For BBC World Book Club:**

```bash
# 1. Scrape BBC World Book Club episodes
python scrape_episodes.py
# Creates: data/bbc_world_book_club_episodes.json

# 2. Search for audiobooks in the library
python search_combined.py --source bbc
# Creates: data/bbc_audiobook_search_results.json

# 3. Refine the search results
python refine_audiobooks.py --input data/bbc_audiobook_search_results.json
# Creates: data/bbc_audiobook_search_results_refined.json

# 4. Check which books are currently available
python check_availability.py --input data/bbc_audiobook_search_results_refined.json
# Creates: data/bbc_available_audiobooks.json
```

## Project Structure

```
.
├── workflow.py                # Complete automated workflow
├── scrape_hugo_awards.py      # Scrape Hugo Award nominees
├── scrape_booker_prize.py     # Scrape Booker Prize nominees
├── scrape_episodes.py         # Scrape BBC World Book Club episodes
├── search_combined.py         # Search library for multiple sources
├── search_audiobooks.py       # Core search library (used by search_combined.py)
├── refine_audiobooks.py       # Filter search results
├── check_availability.py      # Check availability of all books
├── check_by_author.py         # Check availability for one author
├── check_single_book.py       # Check availability for one book
├── requirements.in            # Python dependencies
└── data/                      # All data files (CSV, JSON, etc.)
    ├── hugo_award_nominees.json           # Hugo nominees & winners
    ├── hugo_award_authors.json            # Unique Hugo authors
    ├── hugo_audiobook_search_results.json # Hugo search results
    ├── booker_prize_nominees.json         # Booker nominees & winners
    ├── booker_prize_authors.json          # Unique Booker authors
    ├── booker_audiobook_search_results.json # Booker search results
    ├── bbc_world_book_club_episodes.json  # BBC episodes
    ├── bbc_audiobook_search_results.json  # BBC search results
    ├── audiobook_search_results_refined.json
    └── available_audiobooks.json
```

## Data Sources

### Hugo Award for Best Novel

- **Source**: [Wikipedia](https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novel)
- **Coverage**: 1953-present (79 years)
- **Content**: ~180 authors, winners and nominees
- **Updated**: Manually run scraper to get latest nominees

### Booker Prize

- **Source**: [Wikipedia](https://en.wikipedia.org/wiki/Booker_Prize)
- **Coverage**: 1969-present (57+ years)
- **Content**: Winners, shortlists, and longlists
- **Updated**: Manually run scraper to get latest nominees

### BBC World Book Club

- **Source**: [BBC Audio](https://www.bbc.com/audio/brand/p003jhsk)
- **Coverage**: 130+ episodes
- **Content**: Podcast discussions with authors
- **Updated**: Manually run scraper for new episodes
