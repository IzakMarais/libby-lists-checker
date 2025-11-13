#!/usr/bin/env python3
"""
Quick test script to check availability of a single book.
Usage: python check_single_book.py <book_id>
Example: python check_single_book.py 8919230
"""

import requests
import re
import sys
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


def check_book_availability(book_id: str):
    """Check and display availability for a single book."""
    url = f"https://westerncape.overdrive.com/media/{book_id}"

    print(f"Fetching: {url}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        html = response.text

        # Extract book title
        title_match = re.search(r'"title":"([^"]+)"', html)
        title = title_match.group(1) if title_match else "Unknown"

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

        # Extract availability information
        available_match = re.search(r'"availableCopies":(\d+)', html)
        owned_match = re.search(r'"ownedCopies":(\d+)', html)
        is_available_match = re.search(r'"isAvailable":(true|false)', html)

        print(f"Title: {title}")
        print(f"Book ID: {book_id}")
        print(f"URL: {url}\n")

        if available_match and owned_match:
            available_copies = int(available_match.group(1))
            owned_copies = int(owned_match.group(1))
            is_available = available_copies > 0

            print(f"Available Copies: {available_copies}")
            print(f"Total Copies: {owned_copies}")
            print(f"Status: {'✓ AVAILABLE' if is_available else '✗ NOT AVAILABLE'}")

            if description:
                print(f"\nSummary:")
                print(f"{description}")

            if is_available:
                print(f"\n🎉 You can borrow this book now!")
            else:
                print(f"\n⏳ This book is currently checked out.")

        elif is_available_match:
            is_available = is_available_match.group(1) == 'true'
            print(f"Status: {'✓ AVAILABLE' if is_available else '✗ NOT AVAILABLE'}")
            if description:
                print(f"\nSummary:")
                print(f"{description}")
        else:
            print("Could not determine availability status")

    except requests.RequestException as e:
        print(f"Error fetching book information: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_single_book.py <book_id>")
        print("Example: python check_single_book.py 8919230")
        sys.exit(1)

    book_id = sys.argv[1]
    check_book_availability(book_id)
