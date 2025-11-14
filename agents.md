# Library Audiobook Finder

## Project Overview

This project automates the process of finding and checking availability of audiobooks in the **Western Cape Provincial Library** (South Africa) OverDrive/Libby collection from multiple sources:

1. **BBC World Book Club** - Audiobooks from the podcast's featured books
2. **Hugo Award for Best Novel** - Audiobooks from Hugo Award nominees and winners (1953-present)
3. **Booker Prize** - Audiobooks from Booker Prize winners, shortlists, and longlists (1969-present)
4. **Nobel Prize in Literature** - Audiobooks from Nobel laureates in Literature (1901-present)

## Purpose

This tool helps audiobook enthusiasts:

1. Discover which books from prestigious sources are available as audiobooks in their local library
2. Track availability status (available now vs. on loan)
3. Get direct borrowing URLs for available titles
4. Explore award-winning science fiction, fantasy, and literary fiction

## Architecture & Workflow

The project follows a 4-stage pipeline that can be applied to multiple data sources:

```
Stage 1: Scrape Data → Stage 2: Search Library → Stage 3: Refine Results → Stage 4: Check Availability
```

### Data Sources

The project supports four prestigious literary sources:

| Source                        | Content                                | Scale                                         | Script                       |
| ----------------------------- | -------------------------------------- | --------------------------------------------- | ---------------------------- |
| **BBC World Book Club**       | Episode metadata from BBC podcast      | ~130+ episodes                                | `scrape_episodes.py`         |
| **Hugo Award for Best Novel** | Wikipedia nominees/winners             | 79 years (1953-present), ~180 authors         | `scrape_hugo_awards.py`      |
| **Booker Prize**              | Wikipedia winners/shortlists/longlists | 57+ years (1969-present), hundreds of authors | `scrape_booker_prize.py`     |
| **Nobel Prize in Literature** | Wikipedia laureates                    | 125+ years (1901-present), 120+ laureates     | `scrape_nobel_literature.py` |

### Stage 1: Data Collection

**Common Pattern:** All scrapers extract author names, book titles, and metadata, then generate:

- A detailed entries file (episodes/nominees/laureates) with full metadata
- A deduplicated authors list for library searching
- Both JSON and CSV formats

**Source-Specific Features:**

- **BBC**: Parses episode titles to extract author/book, includes URLs and duration
- **Hugo/Booker**: Handles co-authors (extracts primary), parses Wikipedia tables, tracks winner/nominee status
- **Nobel**: Extracts laureate name, year, country, language, and genre from Wikipedia table structure

**Output Pattern:** `data/{source}_{type}.{json|csv}`

- Entries: `{source}_episodes.json` (BBC), `{source}_nominees.json` (Hugo/Booker), or `{source}_laureates.json` (Nobel)
- Authors: `{source}_authors.json` (all sources)

### Stage 2: Library Search

**Script:** `search_combined.py` (Universal search tool)

Universal search script supporting multiple data sources:

- Loads authors from Hugo Award, Booker Prize, Nobel Prize, or BBC data
- Searches library for each author using `search_audiobooks_for_author()`
- Supports selective searching (hugo, booker, nobel, bbc, or all)
- Configurable rate limiting
- Unified output format for all sources

**Usage:**

```bash
python search_combined.py --source hugo
python search_combined.py --source bbc
python search_combined.py --source booker
python search_combined.py --source nobel
python search_combined.py --source all --delay 2.0
```

**Output:**

- `data/{source}_audiobook_search_results.json`
- e.g., `data/hugo_audiobook_search_results.json`, `data/bbc_audiobook_search_results.json`, `data/booker_audiobook_search_results.json`, `data/nobel_audiobook_search_results.json`

**Note:** `search_audiobooks.py` is now a library module providing the core `search_audiobooks_for_author()` function used by `search_combined.py`.

### Stage 3: Result Refinement

**Script:** `refine_audiobooks.py`

Filters and matches results intelligently using fuzzy name matching (85% similarity threshold) to handle author variations and remove false positives.

**Output:** `data/{source}_audiobook_search_results_refined.{json|csv|txt}` plus changes log

### Stage 4: Availability Checking

**Script:** `check_availability.py`

Fetches real-time availability status by scraping OverDrive pages for copy counts, descriptions, and borrowing URLs.

**Output:** `data/{source}_available_audiobooks.json`

## Utility Scripts

### Workflow Automation

**`workflow.py`**
Complete end-to-end pipeline automation:

```bash
# Run complete workflow for Hugo authors
python workflow.py --source hugo

# Run for all sources
python workflow.py --source all

# Run specific stages only
python workflow.py --stages scrape search

# Skip scraping (use existing data)
python workflow.py --skip-scrape

# Run with limits for testing
python workflow.py --source hugo --limit 5
```

Features:

- Orchestrates all 4 stages automatically
- Source selection (bbc, hugo, booker, nobel, all)
- Stage selection
- Error handling and progress reporting
- Configurable limits for testing/development

### Testing & Validation

**`test_e2e.py`**
End-to-end testing with configurable data limits:

```bash
# Quick smoke test (all sources, 2 items each)
python test_e2e.py --limit 2

# Test specific source
python test_e2e.py --source hugo --limit 5
python test_e2e.py --source booker --limit 5
python test_e2e.py --source nobel --limit 5

# Test with custom delay
python test_e2e.py --limit 3 --delay 1.0
```

Features:

- Validates complete workflow with minimal data
- Tests BBC, Hugo, Booker, and Nobel sources
- Configurable item limits and delays
- Progress reporting and file verification
- Fast iteration during development

See [TESTING.md](TESTING.md) for comprehensive testing guide.

### Quick Check Tools

**`check_single_book.py`**
Test availability for one book by OverDrive ID:

```bash
python check_single_book.py 8919230
```

**`check_by_author.py`**
Check all books by a specific author:

```bash
python check_by_author.py "Agatha Christie"
```

## Technical Stack

### Dependencies (requirements.in)

- **requests** - HTTP library for web scraping
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser (faster than default)

### Key Technologies

- **Web Scraping**: Parses BBC and OverDrive websites
- **Regex Parsing**: Extracts availability data from JavaScript embedded in HTML
- **Fuzzy Matching**: Uses `difflib.SequenceMatcher` for author name comparison
- **Rate Limiting**: Built-in delays to be respectful of server resources
- **Configurable Limits**: All scripts support limiting data for testing/development

## Data Flow

```
Source Website (BBC/Wikipedia)
    ↓
Entries JSON/CSV (episodes/nominees with metadata)
    ↓
Authors JSON/CSV (deduplicated list)
    ↓
OverDrive Search (per author)
    ↓
Search Results JSON/CSV ({source}_audiobook_search_results)
    ↓
Refined Results (filtered by author match)
    ↓
Availability Check (real-time status)
    ↓
Available Audiobooks JSON ({source}_available_audiobooks)
```

## Data Structures

### Stage 1: Source Entry Schemas

**Pattern:** Each source has entries with `author`, `title` fields, plus source-specific metadata:

- **BBC**: `id`, `url`, `original_title`, `date`, `duration`, `page`
- **Hugo/Booker**: `year`, `won` (Hugo) or `status` (Booker: winner/shortlist/longlist)

**Author Lists:** All sources produce simple string arrays of unique author names for Stage 2 searching.

### Stage 2: Search Results Schema

**Universal format** across all sources:

```json
{
  "searched_author": "Author Name",
  "book_id": "8919230",
  "title": "Book Title",
  "author": "Author Name",
  "cover_image": "https://...",
  "search_url": "https://westerncape.overdrive.com/search?..."
}
```

### Stage 3: Refined Results Schema

Same as Stage 2, but filtered to remove non-matching authors. Output includes `.json`, `.csv`, `.txt`, and `_changes.csv`.

### Stage 4: Availability Schema

Extends Stage 3 with real-time availability:

```json
{
  "book_id": "8919230",
  "title": "Book Title",
  "author": "Author Name",
  "is_available": true,
  "available_copies": 1,
  "total_copies": 1,
  "borrow_url": "https://westerncape.overdrive.com/media/8919230",
  "description": "Book description..."
}
```

## Key Features

### Intelligent Author Matching

- Handles name variations (A.S. Byatt vs AS Byatt)
- Removes punctuation and normalizes whitespace
- Uses similarity ratios to account for typos
- Substring matching for partial names

### Availability Detection

- Parses embedded JavaScript data from OverDrive pages
- Extracts `availableCopies` and `ownedCopies` counts
- Shows format: `(1/2)` = 1 available out of 2 total copies
- Cleans HTML descriptions (removes tags, decodes entities)

### Rate Limiting & Error Handling

- Configurable delays between requests
- Timeout handling for network requests
- Graceful degradation on parsing failures
- Progress indicators for batch operations

### Testing & Development Features

- `--limit` parameter on all scripts for testing with small datasets
- End-to-end test script for rapid validation
- Fast iteration during development
- Configurable delays and limits per stage

### Output Formats

- **JSON**: Machine-readable, preserves full data
- **CSV**: Spreadsheet-compatible for analysis
- **TXT**: Human-readable summaries

## Usage Examples

### Quick Testing

```bash
# Fast end-to-end test (2 items per source)
python test_e2e.py --limit 2

# Test specific source with more data
python test_e2e.py --source hugo --limit 5

# See TESTING.md for complete testing guide
```

### Full Workflow

```bash
# Automated workflow (recommended)
python workflow.py --source hugo
python workflow.py --source booker
python workflow.py --source bbc
python workflow.py --source nobel
python workflow.py --source all

# Manual step-by-step (replace {source} with: hugo, booker, nobel, or bbc)
python scrape_{source}.py  # Use scrape_hugo_awards.py, scrape_booker_prize.py, scrape_nobel_literature.py, or scrape_episodes.py
python search_combined.py --source {source}
python refine_audiobooks.py --input data/{source}_audiobook_search_results.json
python check_availability.py --input data/{source}_audiobook_search_results_refined.json
```

### Quick Checks

```bash
# Check one specific book
python check_single_book.py 8919230

# Check all books by an author
python check_by_author.py "Agatha Christie"

# Check with custom delay and output
python check_availability.py --delay 1.0 --output my_results.json
```

## Project Structure

```
libby-world-book-club/
├── workflow.py                 # Complete automated workflow
├── test_e2e.py                 # End-to-end testing
├── scrape_hugo_awards.py       # Stage 1: Hugo scraper (with --limit)
├── scrape_booker_prize.py      # Stage 1: Booker scraper (with --limit)
├── scrape_nobel_literature.py  # Stage 1: Nobel scraper (with --limit)
├── scrape_episodes.py          # Stage 1: BBC scraper (with --limit, includes author extraction)
├── search_combined.py          # Stage 2: Multi-source search (with --limit)
├── search_audiobooks.py        # Library: Core search function
├── refine_audiobooks.py        # Stage 3: Result filtering (with --limit)
├── check_availability.py       # Stage 4: Real-time status (with --limit)
├── check_single_book.py        # Utility: Single book check
├── check_by_author.py          # Utility: Author-specific check
├── debug_search.py             # Utility: HTML debugging
├── requirements.in             # Python dependencies
├── README.md                   # User documentation
├── TESTING.md                  # Testing guide
├── agents.md                   # This file (technical overview)
└── data/                       # All generated data files
    ├── hugo_award_nominees.json            # Hugo entries
    ├── hugo_award_nominees.csv
    ├── hugo_award_authors.json             # Unique authors
    ├── hugo_award_authors.csv
    ├── hugo_audiobook_search_results.json  # Hugo search
    ├── booker_prize_nominees.json          # Booker entries
    ├── booker_prize_nominees.csv
    ├── booker_prize_authors.json           # Unique authors
    ├── booker_prize_authors.csv
    ├── booker_audiobook_search_results.json # Booker search
    ├── nobel_literature_laureates.json     # Nobel entries
    ├── nobel_literature_laureates.csv
    ├── nobel_literature_authors.json       # Unique authors
    ├── nobel_literature_authors.csv
    ├── nobel_audiobook_search_results.json # Nobel search
    ├── bbc_world_book_club_episodes.json   # BBC episodes with parsed authors
    ├── bbc_world_book_club_episodes.csv
    ├── bbc_world_book_club_authors.json    # BBC unique authors
    ├── bbc_world_book_club_authors.csv
    ├── bbc_audiobook_search_results.json   # BBC search (via search_combined.py)
    ├── audiobook_search_results_refined.json
    ├── audiobook_search_results_refined.csv
    ├── audiobook_search_results_refined.txt
    ├── audiobook_search_results_refined_changes.csv
    └── available_audiobooks.json
```
