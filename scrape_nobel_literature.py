#!/usr/bin/env python3
"""
Script to scrape Nobel Prize in Literature laureates from Wikipedia.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time
import argparse


def scrape_nobel_literature():
    """
    Scrape Nobel Prize in Literature laureates from Wikipedia.

    Returns:
        List of dictionaries containing author name, year, country, language, genres
    """
    url = "https://en.wikipedia.org/wiki/List_of_Nobel_laureates_in_Literature"

    print(f"Scraping Nobel Prize in Literature data from Wikipedia...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        entries = []

        # Find the main laureates table - it's the first wikitable on the page
        # The table has columns: Year, Laureate(s), Country, Language, Citation, Genre
        tables = soup.find_all('table', class_='wikitable')

        print(f"Found {len(tables)} tables on the page")

        if not tables:
            print("No tables found!")
            return []

        # Use the first table which contains all laureates
        main_table = tables[0]
        rows = main_table.find_all('tr')

        print(f"Processing {len(rows)} rows")

        for row in rows[1:]:  # Skip header row
            # Find both td and th cells (laureate name is in a th element)
            cells = row.find_all(['td', 'th'])

            # Skip empty rows or rows without enough cells
            # Table structure: Year | Picture | Laureate | Country | Language | Citation | Genre
            if len(cells) < 6:
                continue

            try:
                # Column 0: Year
                year_cell = cells[0]
                year_text = year_cell.get_text(strip=True)

                # Handle "Not awarded" entries
                if 'Not awarded' in year_text or year_text == '':
                    continue

                # Extract year
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_text)
                if not year_match:
                    continue
                year = int(year_match.group(1))

                # Column 1: Picture (skip)
                # Column 2: Laureate(s) - contains name(s)
                laureate_cell = cells[2]

                # Get all text, but extract just the name(s)
                # Names are typically in links
                name_links = laureate_cell.find_all('a')

                if not name_links:
                    # Fallback to plain text
                    laureate_name = laureate_cell.get_text(strip=True)
                else:
                    # Get name from first link (primary laureate if multiple)
                    laureate_name = name_links[0].get_text(strip=True)

                # Clean up the name - remove birth/death years in parentheses
                laureate_name = re.sub(r'\s*\(\d{4}–\d{4}\)', '', laureate_name)
                laureate_name = re.sub(r'\s*\(\d{4}–\)', '', laureate_name)
                laureate_name = re.sub(r'\s+', ' ', laureate_name).strip()

                # Skip if no name
                if not laureate_name or laureate_name == '':
                    continue

                # Column 3: Country
                country_cell = cells[3]
                country = country_cell.get_text(strip=True)
                country = re.sub(r'\s+', ' ', country).strip()

                # Column 4: Language
                language_cell = cells[4]
                language = language_cell.get_text(strip=True)
                language = re.sub(r'\s+', ' ', language).strip()

                # Column 5: Citation
                citation_cell = cells[5]
                citation = citation_cell.get_text(strip=True)
                # Clean up citation - remove quotes and extra whitespace
                citation = citation.strip('"\'')
                citation = re.sub(r'\s+', ' ', citation).strip()
                # Remove reference markers like [8]
                citation = re.sub(r'\[\d+\]', '', citation)

                # Column 6: Genre (if available)
                genre = ""
                if len(cells) > 6:
                    genre_cell = cells[6]
                    genre = genre_cell.get_text(strip=True)
                    genre = re.sub(r'\s+', ' ', genre).strip()

                # Create entry
                entry = {
                    'author': laureate_name,
                    'year': year,
                    'country': country,
                    'language': language,
                    'citation': citation,
                    'genre': genre
                }

                entries.append(entry)

            except Exception as e:
                # Skip problematic rows
                print(f"Error processing row: {e}")
                continue

        print(f"Found {len(entries)} Nobel laureates in Literature")
        if entries:
            print(f"  Years: {min(e['year'] for e in entries)} - {max(e['year'] for e in entries)}")

        return entries

    except Exception as e:
        print(f"Error scraping Nobel Literature: {e}")
        return []


def extract_unique_authors(entries):
    """
    Extract unique author names from entries.

    Args:
        entries: List of entry dictionaries

    Returns:
        List of unique author names (sorted)
    """
    authors = set()

    for entry in entries:
        author = entry.get('author', '')
        if author:
            # Clean up author name
            # Remove any trailing punctuation or notes
            author = re.sub(r'\s*\(.*?\)', '', author)
            author = author.strip()

            if author:
                authors.add(author)

    return sorted(list(authors))


def save_data(entries, output_dir='data'):
    """
    Save entries and unique authors to JSON and CSV files.

    Args:
        entries: List of entry dictionaries
        output_dir: Directory to save files to
    """
    import os

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save laureates
    laureates_json = os.path.join(output_dir, 'nobel_literature_laureates.json')
    laureates_csv = os.path.join(output_dir, 'nobel_literature_laureates.csv')

    # JSON
    with open(laureates_json, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(entries)} laureates to {laureates_json}")

    # CSV
    if entries:
        fieldnames = ['author', 'year', 'country', 'language', 'citation', 'genre']
        with open(laureates_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)
        print(f"Saved {len(entries)} laureates to {laureates_csv}")

    # Extract and save unique authors
    authors = extract_unique_authors(entries)

    authors_json = os.path.join(output_dir, 'nobel_literature_authors.json')
    authors_csv = os.path.join(output_dir, 'nobel_literature_authors.csv')

    # JSON
    with open(authors_json, 'w', encoding='utf-8') as f:
        json.dump(authors, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(authors)} unique authors to {authors_json}")

    # CSV
    with open(authors_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['author'])
        for author in authors:
            writer.writerow([author])
    print(f"Saved {len(authors)} unique authors to {authors_csv}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Scrape Nobel Prize in Literature laureates from Wikipedia'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit the number of laureates to scrape (for testing)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for data files (default: data)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Nobel Prize in Literature Laureates Scraper")
    print("=" * 60)

    # Scrape data
    entries = scrape_nobel_literature()

    if not entries:
        print("No data scraped. Exiting.")
        return

    # Apply limit if specified
    if args.limit:
        print(f"\nLimiting to {args.limit} laureates for testing")
        entries = entries[:args.limit]

    # Save data
    print("\nSaving data...")
    save_data(entries, args.output_dir)

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
