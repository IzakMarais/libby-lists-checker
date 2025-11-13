# Library Audiobook Availability Checker

Check which audiobooks from the Western Cape Provincial Library are currently available to borrow.

## Quick Start

```bash
# Check a single book
python check_single_book.py 8919230

# Check all books by an author
python check_by_author.py "Agatha Christie"

# Check all books (creates available_audiobooks.json)
python check_availability.py
```

## Scripts

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

Results are saved to `available_audiobooks.json` with borrowing URLs.

## Full Workflow

These scripts work with your existing BBC World Book Club workflow:

```bash
# 1. Scrape BBC World Book Club episodes
python scrape_episodes.py
# Creates: bbc_world_book_club_episodes.json, bbc_world_book_club_episodes.csv

# 2. Search for audiobooks in the library
python search_audiobooks.py
# Creates: audiobook_search_results.json, audiobook_search_results.csv

# 3. Refine the search results
python refine_audiobooks.py
# Creates: audiobook_search_results_refined.json, audiobook_search_results_refined.csv

# 4. Check which books are currently available
python check_availability.py
# Creates: available_audiobooks.json
```
