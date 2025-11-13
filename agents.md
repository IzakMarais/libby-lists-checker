# Library Audiobook Finder

## Project Overview

This project automates the process of finding and checking availability of audiobooks in the **Western Cape Provincial Library** (South Africa) OverDrive/Libby collection from multiple sources:

1. **BBC World Book Club** - Audiobooks from the podcast's featured books
2. **Hugo Award for Best Novel** - Audiobooks from Hugo Award nominees and winners (1953-present)

## Purpose

This tool helps audiobook enthusiasts:

1. Discover which books from prestigious sources are available as audiobooks in their local library
2. Track availability status (available now vs. on loan)
3. Get direct borrowing URLs for available titles
4. Explore award-winning science fiction and fantasy literature

## Architecture & Workflow

The project follows a 4-stage pipeline that can be applied to multiple data sources:

```
Stage 1: Scrape Data → Stage 2: Search Library → Stage 3: Refine Results → Stage 4: Check Availability
```

### Data Sources

**Source 1: BBC World Book Club** (Original)

- Scrapes episode metadata from BBC website
- ~130+ episodes featuring author discussions

**Source 2: Hugo Award for Best Novel** (New)

- Scrapes nominees and winners from Wikipedia
- 79 years of awards (1953-present)
- ~180 unique authors
- Both winners and finalists included

### Stage 1: Data Collection

**Script:** `scrape_episodes.py` (BBC)

Scrapes the BBC World Book Club website to extract:

- Episode metadata (ID, author, book title, date, duration)
- Direct episode URLs
- Processes all pages of the podcast archive
- Parses episode titles to extract author and book title fields
- Generates a separate authors list for searching

**Output:**

- `data/bbc_world_book_club_episodes.json`
- `data/bbc_world_book_club_episodes.csv`
- `data/bbc_world_book_club_authors.json`
- `data/bbc_world_book_club_authors.csv`

**Script:** `scrape_hugo_awards.py` (Hugo - NEW)

Scrapes Wikipedia's Hugo Award for Best Novel page to extract:

- Author names
- Book titles
- Winner/nominee status
- Year of nomination

Features:

- Handles co-authors (extracts primary author)
- Deduplicates entries
- Generates separate author list for searching
- Parses complex Wikipedia table structures

**Output:**

- `data/hugo_award_nominees.json` (all nominations)
- `data/hugo_award_nominees.csv`
- `data/hugo_award_authors.json` (unique authors)
- `data/hugo_award_authors.csv`

### Stage 2: Library Search

**Script:** `search_combined.py` (Universal search tool)

Universal search script supporting multiple data sources:

- Loads authors from Hugo Award or BBC data
- Searches library for each author using `search_audiobooks_for_author()`
- Supports selective searching (hugo, bbc, or both)
- Configurable rate limiting
- Unified output format for all sources

**Usage:**

```bash
python search_combined.py --source hugo
python search_combined.py --source bbc
python search_combined.py --source both --delay 2.0
```

**Output:**

- `data/{source}_audiobook_search_results.json`
- e.g., `data/hugo_audiobook_search_results.json`, `data/bbc_audiobook_search_results.json`

**Note:** `search_audiobooks.py` is now a library module providing the core `search_audiobooks_for_author()` function used by `search_combined.py`.

### Stage 3: Result Refinement

**Script:** `refine_audiobooks.py`

Filters and matches results intelligently:

- Uses fuzzy name matching to handle author name variations
- Removes false positives (books by different authors)
- Normalizes author names (handles punctuation, capitalization)
- Applies similarity threshold (default 85%) for matching

**Output:**

- `data/audiobook_search_results_refined.json`
- `data/audiobook_search_results_refined.csv`
- `data/audiobook_search_results_refined.txt`
- `data/audiobook_search_results_refined_changes.csv`

### Stage 4: Availability Checking

**Script:** `check_availability.py`

Fetches real-time availability status:

- Scrapes each book's OverDrive page
- Extracts available/owned copy counts
- Retrieves book descriptions
- Generates borrowing URLs

**Output:**

- `data/available_audiobooks.json` (with availability status)

## Utility Scripts

### Workflow Automation

**`workflow.py`**
Complete end-to-end pipeline automation:

```bash
# Run complete workflow for Hugo authors
python workflow.py --source hugo

# Run for both sources
python workflow.py --source both

# Run specific stages only
python workflow.py --stages scrape search

# Skip scraping (use existing data)
python workflow.py --skip-scrape

# Run with limits for testing (NEW)
python workflow.py --source hugo --limit 5
```

Features:

- Orchestrates all 4 stages automatically
- Source selection (bbc, hugo, both)
- Stage selection
- Error handling and progress reporting
- Configurable limits for testing/development

### Testing & Validation

**`test_e2e.py`** (NEW)
End-to-end testing with configurable data limits:

```bash
# Quick smoke test (both sources, 2 items each)
python test_e2e.py --limit 2

# Test specific source
python test_e2e.py --source hugo --limit 5

# Test with custom delay
python test_e2e.py --limit 3 --delay 1.0
```

Features:

- Validates complete workflow with minimal data
- Tests both BBC and Hugo sources
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
BBC Website
    ↓
Episodes JSON/CSV (130+ episodes)
    ↓
OverDrive Search (per author)
    ↓
Search Results JSON/CSV (~200-300 results)
    ↓
Refined Results (filtered by author match)
    ↓
Availability Check (real-time status)
    ↓
Available Audiobooks JSON (ready to borrow)
```

## Data Structures

### Episode Data (BBC)

```json
{
  "id": "w3cswsss",
  "url": "https://www.bbc.com/audio/play/w3cswsss",
  "original_title": "Ngũgĩ wa Thiong'o - A Grain of Wheat",
  "author": "Ngũgĩ wa Thiong'o",
  "book_title": "A Grain of Wheat",
  "date": "9 Mar 2019",
  "duration": "48 mins",
  "page": 0
}
```

### BBC Author List

```json
[
  "Agatha Christie",
  "Ngũgĩ wa Thiong'o",
  "Oyinkan Braithwaite",
  ...
]
```

### Hugo Award Entry

```json
{
  "author": "N. K. Jemisin",
  "title": "The Fifth Season",
  "won": true,
  "year": 2016
}
```

### Hugo Author List

```json
[
  "Alfred Bester",
  "Isaac Asimov",
  "N. K. Jemisin",
  ...
]
```

### Audiobook Search Result

```json
{
  "searched_author": "Ngũgĩ wa Thiong'o",
  "book_id": "8919230",
  "title": "A Grain of Wheat",
  "author": "Ngũgĩ wa Thiong'o",
  "cover_image": "https://...",
  "search_url": "https://westerncape.overdrive.com/search?..."
}
```

### Availability Result

```json
{
  "book_id": "8919230",
  "title": "A Grain of Wheat",
  "author": "Ngũgĩ wa Thiong'o",
  "is_available": true,
  "available_copies": 1,
  "total_copies": 1,
  "borrow_url": "https://westerncape.overdrive.com/media/8919230",
  "description": "Set in Kenya during the Mau Mau uprising..."
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

### Testing & Development Features (NEW)

- `--limit` parameter on all scripts for testing with small datasets
- End-to-end test script for rapid validation
- Fast iteration during development
- Configurable delays and limits per stage

### Output Formats

- **JSON**: Machine-readable, preserves full data
- **CSV**: Spreadsheet-compatible for analysis
- **TXT**: Human-readable summaries

## Usage Examples

### Quick Testing (NEW)

```bash
# Fast end-to-end test (2 items per source)
python test_e2e.py --limit 2

# Test specific source with more data
python test_e2e.py --source hugo --limit 5

# See TESTING.md for complete testing guide
```

### Full Workflow

```bash
# Automated workflow for Hugo authors (recommended)
python workflow.py --source hugo

# Automated workflow for both sources
python workflow.py --source both

# Manual step-by-step (Hugo)
python scrape_hugo_awards.py
python search_combined.py --source hugo
python refine_audiobooks.py --input data/hugo_audiobook_search_results.json
python check_availability.py --input data/hugo_audiobook_search_results_refined.json

# Manual step-by-step (BBC - original workflow)
python scrape_episodes.py
python search_combined.py --source bbc
python refine_audiobooks.py --input data/bbc_audiobook_search_results.json
python check_availability.py --input data/bbc_audiobook_search_results_refined.json
```

### Quick Checks

```bash
# Check one specific book
python check_single_book.py 8919230

# Check all Agatha Christie audiobooks
python check_by_author.py "Agatha Christie"

# Check with custom delay and output
python check_availability.py --delay 1.0 --output my_results.json
```

## Project Structure

```
libby-world-book-club/
├── workflow.py                 # Complete automated workflow
├── test_e2e.py                 # NEW: End-to-end testing
├── scrape_hugo_awards.py       # Stage 1 Hugo scraper (with --limit)
├── scrape_episodes.py          # Stage 1: BBC scraper (with --limit, includes author extraction)
├── search_combined.py          # Stage 2 multi-source search (with --limit)
├── search_audiobooks.py        # Library: Core search function
├── refine_audiobooks.py        # Stage 3: Result filtering (with --limit)
├── check_availability.py       # Stage 4: Real-time status (with --limit)
├── check_single_book.py        # Utility: Single book check
├── check_by_author.py          # Utility: Author-specific check
├── debug_search.py             # Utility: HTML debugging
├── requirements.in             # Python dependencies
├── README.md                   # User documentation
├── TESTING.md                  # NEW: Testing guide
├── agents.md                   # This file (technical overview)
└── data/                       # All generated data files
    ├── hugo_award_nominees.json            # Hugo entries
    ├── hugo_award_nominees.csv
    ├── hugo_award_authors.json             # Unique authors
    ├── hugo_award_authors.csv
    ├── hugo_audiobook_search_results.json  # Hugo search
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

## Development Notes

### Web Scraping Approach

- Uses BeautifulSoup for HTML parsing
- Employs regex for extracting embedded JavaScript data
- Sets appropriate User-Agent headers to avoid blocking
- Respects rate limits with configurable delays

### Author Matching Algorithm

1. Normalize both names (lowercase, remove punctuation)
2. Check exact match
3. Check substring containment
4. Calculate similarity ratio with SequenceMatcher
5. Apply threshold (default 0.85)

### Future Enhancements

- Add scheduling/automation for regular checks
- Email/notification system for newly available books
- Support for multiple library systems
- Wishlist functionality
- Integration with Libby app API

## Target Audience

This tool is designed for:

- BBC World Book Club listeners
- Western Cape library patrons
- Audiobook enthusiasts
- Anyone wanting to automate library availability checking

## License & Usage

This is a personal utility project for educational and individual use. When using this tool:

- Respect website terms of service
- Use appropriate rate limiting
- Don't overwhelm servers with requests
- Consider caching results to minimize repeated scraping

## Maintenance

The scripts may need updates if:

- BBC World Book Club website structure changes
- OverDrive/Libby website HTML changes
- Search result parsing breaks
- New authentication requirements are added

## Statistics

- **130+ Episodes**: BBC World Book Club archive
- **180+ Authors**: Hugo Award nominees and winners (1953-present)
- **79 Years**: Hugo Award history
- **Multiple Authors**: From contemporary to classic literature
- **OverDrive Collection**: Western Cape Provincial Library system
- **Pipeline Stages**: 4 main stages + 3 utility scripts
- **Data Formats**: JSON, CSV, TXT outputs
