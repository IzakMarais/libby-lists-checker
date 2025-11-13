#!/usr/bin/env python3
"""
Check availability for books by a specific author from your JSON file.
Usage: python check_by_author.py "Author Name"
Example: python check_by_author.py "Abdulrazak Gurnah"
"""

import json
import requests
import re
import sys
import time
import html as html_module


def clean_html_description(description: str) -> str:
    """Clean HTML description by removing tags and decoding entities."""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', description)
    # Decode HTML entities
    clean = html_module.unescape(clean)
    # Clean up whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def fetch_availability(book_id: str):
    """Fetch the availability status for a book from OverDrive."""
    url = f"https://westerncape.overdrive.com/media/{book_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text

        available_match = re.search(r'"availableCopies":(\d+)', html)
        owned_match = re.search(r'"ownedCopies":(\d+)', html)

        # Extract description from window.OverDrive.titleCollection specifically
        description = None
        title_collection_match = re.search(r'window\.OverDrive\.titleCollection\s*=\s*({[^;]+})', html)
        if title_collection_match:
            title_data = title_collection_match.group(1)
            # Look for description after "publisher" field to avoid bisac descriptions
            description_match = re.search(r'"publisher":[^}]+},"description":"((?:[^"\\]|\\.)*?)"', title_data)
            if description_match:
                description = description_match.group(1)
                # Unescape JSON string
                description = description.encode().decode('unicode_escape')
                description = clean_html_description(description)

        # If no description or it looks like a BISAC code, try the HTML body
        if not description or description.startswith('FICTION ') or description.startswith('Fiction /'):
            body_desc_match = re.search(r'<article class="TitleDetailsDescription-description[^>]*>(.*?)</article>', html, re.DOTALL)
            if body_desc_match:
                description = body_desc_match.group(1)
                description = clean_html_description(description)

        if available_match and owned_match:
            available_copies = int(available_match.group(1))
            owned_copies = int(owned_match.group(1))
            is_available = available_copies > 0
            return is_available, available_copies, owned_copies, description

        return False, 0, 0, description

    except requests.RequestException as e:
        print(f"Error fetching {book_id}: {e}")
        return False, 0, 0, None


def check_author_books(author_name: str, books_data: dict):
    """Check availability for all books by a specific author."""

    # Find the author (case-insensitive search)
    author_key = None
    for key in books_data.keys():
        if key.lower() == author_name.lower():
            author_key = key
            break

    if not author_key:
        print(f"Author '{author_name}' not found in the database.")
        print("\nAvailable authors:")
        for author in sorted(books_data.keys()):
            if books_data[author]['count'] > 0:
                print(f"  - {author} ({books_data[author]['count']} books)")
        return

    author_data = books_data[author_key]

    if author_data['count'] == 0:
        print(f"No books found for {author_key}")
        return

    print(f"\n{'=' * 80}")
    print(f"Checking {author_data['count']} book(s) by {author_key}")
    print(f"{'=' * 80}\n")

    available_books = []

    for book in author_data['books']:
        title = book['title']
        book_id = book['id']
        url = f"https://westerncape.overdrive.com/media/{book_id}"

        print(f"📚 {title}")
        print(f"   Checking availability...", end=' ')

        is_available, available_copies, owned_copies, description = fetch_availability(book_id)

        if is_available:
            print(f"✓ AVAILABLE ({available_copies}/{owned_copies})")
            print(f"   🔗 {url}")
            if description:
                # Truncate long descriptions
                desc = description
                if len(desc) > 150:
                    desc = desc[:147] + '...'
                print(f"   Summary: {desc}")
            available_books.append({
                'title': title,
                'available_copies': available_copies,
                'owned_copies': owned_copies,
                'url': url,
                'description': description
            })
        else:
            print(f"✗ Not available ({available_copies}/{owned_copies})")

        print()
        time.sleep(0.5)  # Be respectful to the server

    # Summary
    print(f"{'=' * 80}")
    if available_books:
        print(f"✓ {len(available_books)} of {author_data['count']} book(s) available to borrow")
        print(f"{'=' * 80}\n")
        print("Available now:")
        for book in available_books:
            print(f"  • {book['title']} - {book['url']}")
    else:
        print(f"✗ None of the {author_data['count']} book(s) are currently available")
        print(f"{'=' * 80}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_by_author.py \"Author Name\"")
        print("Example: python check_by_author.py \"Abdulrazak Gurnah\"")
        sys.exit(1)

    author_name = sys.argv[1]

    # Load the book data
    try:
        with open('data/audiobook_search_results_refined.json', 'r', encoding='utf-8') as f:
            books_data = json.load(f)
    except FileNotFoundError:
        print("Error: data/audiobook_search_results_refined.json not found")
        sys.exit(1)

    check_author_books(author_name, books_data)


if __name__ == '__main__':
    main()
