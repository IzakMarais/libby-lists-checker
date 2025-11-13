#!/usr/bin/env python3
"""
Script to check which audiobooks from the library are currently available to borrow.
Fetches the availability status from the OverDrive website for each book.
"""

import json
import requests
import re
import time
from typing import Dict, List, Tuple, Optional
import argparse
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


def fetch_availability(book_id: str) -> Tuple[bool, int, int, Optional[str]]:
    """
    Fetch the availability status for a book from OverDrive.

    Args:
        book_id: The book ID from OverDrive

    Returns:
        Tuple of (is_available, available_copies, total_copies, description)
    """
    url = f"https://westerncape.overdrive.com/media/{book_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        html = response.text

        # Look for the availability information in the JavaScript data
        # Pattern: "availableCopies":1,"ownedCopies":1
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

        # Fallback: Check for "isAvailable" flag
        is_available_match = re.search(r'"isAvailable":(true|false)', html)
        if is_available_match:
            is_available = is_available_match.group(1) == 'true'
            return is_available, 0, 0, description

        return False, 0, 0, description

    except requests.RequestException as e:
        print(f"Error fetching {book_id}: {e}")
        return False, 0, 0, None


def check_all_books(books_data: Dict, delay: float = 0.5, limit: int = None) -> List[Dict]:
    """
    Check availability for all books in the dataset.

    Args:
        books_data: Dictionary containing book information
        delay: Delay between requests in seconds (to be respectful to the server)
        limit: Maximum number of books to check (None for all)

    Returns:
        List of available books with their details
    """
    available_books = []
    total_books = sum(author_data['count'] for author_data in books_data.values())
    
    if limit:
        print(f"Checking availability for up to {limit} books (limited from {total_books})...\n")
    else:
        print(f"Checking availability for {total_books} books...\n")
    
    processed = 0
    checked = 0

    for author, author_data in books_data.items():
        if author_data['count'] == 0:
            continue

        for book in author_data['books']:
            if limit and checked >= limit:
                break
            
            processed += 1
            checked += 1
            book_id = book['id']
            title = book['title']

            print(f"[{checked}/{min(limit, total_books) if limit else total_books}] Checking: {title} by {author}...", end=' ')

            is_available, available_copies, owned_copies, description = fetch_availability(book_id)

            if is_available:
                print(f"✓ AVAILABLE ({available_copies}/{owned_copies})")
                available_books.append({
                    'title': title,
                    'author': author,
                    'id': book_id,
                    'url': f"https://westerncape.overdrive.com/media/{book_id}",
                    'available_copies': available_copies,
                    'owned_copies': owned_copies,
                    'formats': book.get('formats', []),
                    'description': description
                })
            else:
                print(f"✗ Not available ({available_copies}/{owned_copies})")

            # Be respectful to the server
            time.sleep(delay)
        
        if limit and checked >= limit:
            break

    return available_books


def save_results(available_books: List[Dict], output_file: str):
    """Save the available books to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(available_books, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_file}")


def print_summary(available_books: List[Dict]):
    """Print a summary of available books."""
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {len(available_books)} books available to borrow")
    print(f"{'=' * 80}\n")

    if available_books:
        for book in available_books:
            print(f"📚 {book['title']}")
            print(f"   by {book['author']}")
            print(f"   Available: {book['available_copies']}/{book['owned_copies']} copies")
            print(f"   URL: {book['url']}")
            if book.get('description'):
                # Truncate long descriptions
                desc = book['description']
                if len(desc) > 200:
                    desc = desc[:197] + '...'
                print(f"   Summary: {desc}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Check availability of library audiobooks'
    )
    parser.add_argument(
        '--input',
        default='data/audiobook_search_results_refined.json',
        help='Input JSON file with book data (default: data/audiobook_search_results_refined.json)'
    )
    parser.add_argument(
        '--output',
        default='data/available_audiobooks.json',
        help='Output JSON file for available books (default: data/available_audiobooks.json)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of books to check (default: check all)'
    )

    args = parser.parse_args()

    # Load the book data
    print(f"Loading book data from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        books_data = json.load(f)

    # Check availability
    available_books = check_all_books(books_data, delay=args.delay, limit=args.limit)

    # Save results
    save_results(available_books, args.output)

    # Print summary
    print_summary(available_books)


if __name__ == '__main__':
    main()
