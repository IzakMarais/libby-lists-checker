#!/usr/bin/env python3
"""
Script to scrape Booker Prize nominees and winners from Wikipedia.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time
import argparse


def scrape_booker_prize():
    """
    Scrape Booker Prize nominees and winners from Wikipedia.

    Returns:
        List of dictionaries containing author, book title, year, won status
    """
    url = "https://en.wikipedia.org/wiki/List_of_winners_and_nominated_authors_of_the_Booker_Prize"

    print(f"Scraping Booker Prize data from Wikipedia...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        entries = []

        # Find all tables with class wikitable
        tables = soup.find_all('table', class_='wikitable')

        print(f"Found {len(tables)} tables on the page")

        # Track current year
        current_year = None

        for table in tables:
            # Get the rows from the table
            rows = table.find_all('tr')

            # Skip header row
            for row in rows[1:]:
                cells = row.find_all('td')

                # Skip empty rows
                if len(cells) < 2:
                    continue

                try:
                    # First cell contains the status (Winner/Shortlist/Longlist)
                    status_cell = cells[0]
                    status_text = status_cell.get_text(strip=True)

                    # Determine if winner, shortlist, or longlist
                    won = False
                    shortlist = False
                    longlist = False

                    if 'Winner' in status_text or 'Winners' in status_text:
                        won = True
                    elif 'Shortlist' in status_text:
                        shortlist = True
                    elif 'Longlist' in status_text:
                        longlist = True
                    else:
                        # Skip header rows and other non-entry rows
                        continue

                    # Second cell contains the author
                    if len(cells) < 2:
                        continue

                    author_cell = cells[1]
                    author_text = author_cell.get_text(strip=True)

                    # Clean author name
                    author = author_text.strip()

                    # Skip empty authors
                    if not author or author == '':
                        continue

                    # Handle multiple authors (take first one)
                    if '/' in author or ' and ' in author:
                        # Keep as is for now, can be split later if needed
                        pass

                    # Third cell contains the title
                    if len(cells) < 3:
                        continue

                    title_cell = cells[2]
                    title = title_cell.get_text(strip=True)

                    # Clean up title (remove parenthetical notes, reference markers)
                    title = re.sub(r'\[\d+\]', '', title)  # Remove [1], [2] etc
                    title = re.sub(r'\s*\(.*?\)', '', title)  # Remove (notes)

                    # Skip if no title
                    if not title or title == '':
                        continue

                    # Check if this looks like a valid entry (has both author and title)
                    if author and title and len(author) > 1 and len(title) > 1:
                        entry = {
                            'author': author,
                            'title': title,
                            'won': won,
                            'shortlist': shortlist,
                            'longlist': longlist,
                            'year': current_year  # Will be filled in later
                        }

                        entries.append(entry)

                except Exception as e:
                    # Skip problematic rows
                    continue

        # Now assign years based on sections
        entries_with_years = assign_years_to_entries(soup, entries)

        print(f"Found {len(entries_with_years)} total entries")
        print(f"  Winners: {sum(1 for e in entries_with_years if e['won'])}")
        print(f"  Shortlist: {sum(1 for e in entries_with_years if e['shortlist'])}")
        print(f"  Longlist: {sum(1 for e in entries_with_years if e['longlist'])}")

        return entries_with_years

    except Exception as e:
        print(f"Error scraping Booker Prize: {e}")
        return []


def assign_years_to_entries(soup, entries):
    """
    Assign years to entries by parsing the Wikipedia page structure.

    The Booker Prize page has year information in the table rows themselves.
    We need to track the current year as we process rows.

    Args:
        soup: BeautifulSoup object of the page
        entries: List of entries without years

    Returns:
        List of entries with years assigned
    """
    entries_with_years = []
    tables = soup.find_all('table', class_='wikitable')

    # Track year from the structure
    # The page has tables grouped by year, with year appearing in row headers
    current_year = None

    for table in tables:
        rows = table.find_all('tr')

        for row in rows[1:]:  # Skip header
            cells = row.find_all('td')

            if len(cells) < 2:
                continue

            # Extract year from rowspan pattern if present
            # Check if there's a year marker in the first cell or surrounding context
            status_cell = cells[0]
            status_text = status_cell.get_text(strip=True)

            # Try to extract year from status text (some rows have year indicators)
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', status_text)
            if year_match:
                current_year = int(year_match.group(1))

            # Look for year in previous heading or table caption
            if current_year is None:
                prev_heading = row.find_previous(['h3', 'h4', 'caption'])
                if prev_heading:
                    heading_text = prev_heading.get_text(strip=True)
                    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', heading_text)
                    if year_match:
                        current_year = int(year_match.group(1))

            # Now process the entry if it's a winner/shortlist/longlist row
            if any(x in status_text for x in ['Winner', 'Winners', 'Shortlist', 'Longlist']):
                if len(cells) >= 3:
                    author_cell = cells[1]
                    author = author_cell.get_text(strip=True)

                    title_cell = cells[2]
                    title = title_cell.get_text(strip=True)
                    title = re.sub(r'\[\d+\]', '', title)
                    title = re.sub(r'\s*\(.*?\)', '', title)

                    if author and title and len(author) > 1 and len(title) > 1:
                        won = 'Winner' in status_text
                        shortlist = 'Shortlist' in status_text
                        longlist = 'Longlist' in status_text

                        entry = {
                            'author': author,
                            'title': title,
                            'won': won,
                            'shortlist': shortlist,
                            'longlist': longlist,
                            'year': current_year
                        }

                        entries_with_years.append(entry)

    return entries_with_years


def deduplicate_entries(entries):
    """
    Remove duplicate entries (same author + title combination).
    Keep the entry marked as winner if there are duplicates.

    Args:
        entries: List of entry dictionaries

    Returns:
        Deduplicated list of entries
    """
    seen = {}
    deduplicated = []

    for entry in entries:
        key = (entry['author'].lower(), entry['title'].lower())

        if key not in seen:
            seen[key] = entry
            deduplicated.append(entry)
        else:
            # If new entry is a winner and old one isn't, replace
            if entry['won'] and not seen[key]['won']:
                # Remove old entry from deduplicated list
                deduplicated = [e for e in deduplicated if (e['author'].lower(), e['title'].lower()) != key]
                seen[key] = entry
                deduplicated.append(entry)

    return deduplicated


def get_unique_authors(entries):
    """
    Extract unique authors from the entries.

    Args:
        entries: List of entry dictionaries

    Returns:
        Sorted list of unique author names
    """
    authors = set()

    for entry in entries:
        # Clean author name
        author = entry['author']

        # Remove common suffixes and reference markers
        author = re.sub(r'\s+\(.*?\)$', '', author)  # Remove (translator) etc
        author = re.sub(r'\s+\[.*?\]$', '', author)  # Remove [reference] etc
        author = re.sub(r'\[\d+\]', '', author)  # Remove [1], [2] etc

        # Handle co-authors - take the primary author (first one)
        if ' and ' in author:
            author = author.split(' and ')[0].strip()

        # Handle special cases
        if author and len(author) > 1:
            authors.add(author.strip())

    return sorted(list(authors))


def save_to_json(entries, filename='data/booker_prize_nominees.json'):
    """Save entries to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(entries)} entries to {filename}")


def save_to_csv(entries, filename='data/booker_prize_nominees.csv'):
    """Save entries to CSV file."""
    if not entries:
        print("No entries to save to CSV")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['author', 'title', 'won', 'shortlist', 'longlist', 'year']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    print(f"Saved {len(entries)} entries to {filename}")


def save_authors_to_json(authors, filename='data/booker_prize_authors.json'):
    """Save unique authors to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(authors, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(authors)} unique authors to {filename}")


def save_authors_to_csv(authors, filename='data/booker_prize_authors.csv'):
    """Save unique authors to CSV file."""
    if not authors:
        print("No authors to save to CSV")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['author'])
        for author in authors:
            writer.writerow([author])
    print(f"Saved {len(authors)} unique authors to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Booker Prize data from Wikipedia'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of entries to save (default: save all)'
    )

    args = parser.parse_args()

    print("Starting to scrape Booker Prize data...")
    print("=" * 60)

    # Scrape the data
    entries = scrape_booker_prize()

    if not entries:
        print("\nNo entries were scraped. Please check the script and try again.")
        return

    # Deduplicate entries
    entries = deduplicate_entries(entries)

    # Apply limit if specified
    if args.limit:
        entries = entries[:args.limit]
        print(f"\nLimited to {len(entries)} entries")

    print("\n" + "=" * 60)
    print(f"Total deduplicated entries: {len(entries)}")
    print(f"  Winners: {sum(1 for e in entries if e['won'])}")
    print(f"  Shortlist: {sum(1 for e in entries if e['shortlist'])}")
    print(f"  Longlist: {sum(1 for e in entries if e['longlist'])}")

    # Save entries
    save_to_json(entries)
    save_to_csv(entries)

    # Extract unique authors
    authors = get_unique_authors(entries)
    print(f"\nUnique authors: {len(authors)}")

    # Save authors
    save_authors_to_json(authors)
    save_authors_to_csv(authors)

    # Print some statistics
    print("\n" + "=" * 60)
    print("Sample entries:")
    for i, entry in enumerate(entries[:10], 1):
        status = "WINNER" if entry['won'] else ("SHORTLIST" if entry['shortlist'] else "LONGLIST")
        year_str = f" ({entry['year']})" if entry['year'] else ""
        print(f"{i}. [{status}]{year_str} {entry['author']} - {entry['title']}")

    print("\nSample authors:")
    for i, author in enumerate(authors[:20], 1):
        print(f"{i}. {author}")


if __name__ == "__main__":
    main()
