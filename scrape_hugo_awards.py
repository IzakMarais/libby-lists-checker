#!/usr/bin/env python3
"""
Script to scrape Hugo Award for Best Novel nominees and winners from Wikipedia.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time
import argparse


def scrape_hugo_awards():
    """
    Scrape Hugo Award nominees and winners from Wikipedia.

    Returns:
        List of dictionaries containing author, book title, year, won status
    """
    url = "https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novel"

    print(f"Scraping Hugo Award data from Wikipedia...")
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

        for table in tables:
            # Get the rows from the table
            rows = table.find_all('tr')

            # Skip header row
            for row in rows[1:]:
                cells = row.find_all('td')

                # Skip empty rows
                if len(cells) < 2:
                    continue

                # Try to extract author, title, and year
                # Format varies but typically: Author* | Title | Publisher | [Year]
                try:
                    # First cell contains the author(s)
                    author_cell = cells[0]
                    author_text = author_cell.get_text(strip=True)

                    # Remove asterisks (indicates winner)
                    won = '*' in author_text
                    author = author_text.replace('*', '').strip()

                    # Skip empty authors
                    if not author or author == '':
                        continue

                    # Handle co-authors (split by newlines, which appear as separate text nodes)
                    # Get all text, split by newlines
                    full_author_text = author_cell.get_text(separator='|', strip=True)
                    authors = [a.strip().replace('*', '') for a in full_author_text.split('|') if a.strip()]

                    # Use the first/main author
                    if authors:
                        author = authors[0]

                    # Second cell contains the title
                    if len(cells) > 1:
                        title_cell = cells[1]
                        title = title_cell.get_text(strip=True)

                        # Clean up title (remove parenthetical notes)
                        title = re.sub(r'\s*\(also known as.*?\)', '', title)

                        # Skip if no title
                        if not title or title == '':
                            continue
                    else:
                        continue

                    # Try to extract year from the last cell (which typically has [XX] references)
                    # We'll infer year from context later or add it as we process
                    year = None

                    # Check if this looks like a valid entry (has both author and title)
                    if author and title and len(author) > 1 and len(title) > 1:
                        # Check if row has a yellow background (winner indicator)
                        style = row.get('style', '')
                        if not won and 'background' in style.lower() and 'yellow' in style.lower():
                            won = True

                        entry = {
                            'author': author,
                            'title': title,
                            'won': won,
                            'year': year  # Will be filled in later
                        }

                        entries.append(entry)

                except Exception as e:
                    # Skip problematic rows
                    continue

        # Now assign years based on sections
        # Re-parse to get year headers
        entries_with_years = assign_years_to_entries(soup, entries)

        print(f"Found {len(entries_with_years)} total entries")
        print(f"  Winners: {sum(1 for e in entries_with_years if e['won'])}")
        print(f"  Nominees: {sum(1 for e in entries_with_years if not e['won'])}")

        return entries_with_years

    except Exception as e:
        print(f"Error scraping Hugo Awards: {e}")
        return []


def assign_years_to_entries(soup, entries):
    """
    Assign years to entries by parsing the Wikipedia page structure.

    The page has links at the top like "1953 •" which correspond to years.
    We'll try to match entries based on their order in the document.

    Args:
        soup: BeautifulSoup object of the page
        entries: List of entries without years

    Returns:
        List of entries with years assigned
    """
    # Find all tables and preceding year headers
    tables = soup.find_all('table', class_='wikitable')
    current_entries = list(entries)  # Copy of entries
    entries_with_years = []

    # Since Wikipedia tables don't have explicit year markers in each row,
    # we'll extract years from the data itself or use section headers

    # Alternative approach: Look for patterns in the reference links [XX]
    # and extract years from section context

    # For now, we'll use a simpler approach: extract year from table context
    for table in tables:
        # Look for heading before table
        prev_element = table.find_previous(['h3', 'h4', 'h5'])
        year = None

        if prev_element:
            # Try to extract year from heading
            heading_text = prev_element.get_text(strip=True)
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', heading_text)
            if year_match:
                year = int(year_match.group(1))

        # Process rows in this table
        rows = table.find_all('tr')[1:]  # Skip header

        for row in rows:
            cells = row.find_all('td')

            if len(cells) < 2:
                continue

            author_cell = cells[0]
            author_text = author_cell.get_text(strip=True)
            won = '*' in author_text
            author = author_text.replace('*', '').strip()

            # Get author properly (handle co-authors)
            full_author_text = author_cell.get_text(separator='|', strip=True)
            authors = [a.strip().replace('*', '') for a in full_author_text.split('|') if a.strip()]
            if authors:
                author = authors[0]

            if len(cells) > 1:
                title_cell = cells[1]
                title = title_cell.get_text(strip=True)
                title = re.sub(r'\s*\(also known as.*?\)', '', title)
            else:
                continue

            if author and title and len(author) > 1 and len(title) > 1:
                # Check for yellow background (winner)
                style = row.get('style', '')
                if not won and 'background' in style.lower() and 'yellow' in style.lower():
                    won = True

                entry = {
                    'author': author,
                    'title': title,
                    'won': won,
                    'year': year
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

        # Remove common suffixes
        author = re.sub(r'\s+\(.*?\)$', '', author)  # Remove (translator) etc
        author = re.sub(r'\s+\[.*?\]$', '', author)  # Remove [reference] etc

        # Handle special cases
        if author and len(author) > 1:
            authors.add(author.strip())

    return sorted(list(authors))


def save_to_json(entries, filename='data/hugo_award_nominees.json'):
    """Save entries to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(entries)} entries to {filename}")


def save_to_csv(entries, filename='data/hugo_award_nominees.csv'):
    """Save entries to CSV file."""
    if not entries:
        print("No entries to save to CSV")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['author', 'title', 'won', 'year']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    print(f"Saved {len(entries)} entries to {filename}")


def save_authors_to_json(authors, filename='data/hugo_award_authors.json'):
    """Save unique authors to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(authors, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(authors)} unique authors to {filename}")


def save_authors_to_csv(authors, filename='data/hugo_award_authors.csv'):
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
        description='Scrape Hugo Award for Best Novel data from Wikipedia'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of entries to save (default: save all)'
    )
    
    args = parser.parse_args()
    
    print("Starting to scrape Hugo Award for Best Novel data...")
    print("=" * 60)

    # Scrape the data
    entries = scrape_hugo_awards()

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
    print(f"  Nominees: {sum(1 for e in entries if not e['won'])}")

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
        status = "WINNER" if entry['won'] else "Nominee"
        year_str = f" ({entry['year']})" if entry['year'] else ""
        print(f"{i}. [{status}]{year_str} {entry['author']} - {entry['title']}")

    print("\nSample authors:")
    for i, author in enumerate(authors[:20], 1):
        print(f"{i}. {author}")


if __name__ == "__main__":
    main()
