#!/usr/bin/env python3
"""
Library module for searching audiobooks on Western Cape OverDrive library.

This module provides the core search functionality used by other scripts.
Use search_combined.py as the CLI tool for batch searches.
"""

import json
import urllib.parse
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup


def search_audiobooks_for_author(author_name: str, base_url: str = "https://westerncape.overdrive.com") -> Optional[Dict]:
    """
    Search for audiobooks by a specific author on OverDrive.

    Args:
        author_name: The name of the author to search for
        base_url: The base URL of the OverDrive library

    Returns:
        Dictionary with count, books list, and search URL, or None if the request failed

        Example return value:
        {
            'count': 5,
            'books': [
                {
                    'title': 'Book Title',
                    'author': 'Author Name',
                    'id': '12345',
                    'available': True,
                    'formats': ['Audiobook']
                },
                ...
            ],
            'url': 'https://westerncape.overdrive.com/search?...'
        }
    """
    import re

    # Encode the author name for URL
    encoded_author = urllib.parse.quote(author_name)

    # Build the search URL
    search_url = f"{base_url}/search?query={encoded_author}&format=audiobook-overdrive%2Caudiobook-overdrive-provisional&sortBy=relevance"

    try:
        # Make the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Method 1: Extract from the "Showing X-Y of Z results" text
        results_count = 0
        books = []

        # Look for the results heading
        results_heading = soup.find('h1', class_='search-text')
        if results_heading:
            text = results_heading.get_text(strip=True)
            # Pattern: "Showing 1-2 of 2 results"
            match = re.search(r'Showing\s+\d+-\d+\s+of\s+(\d+)\s+results?', text, re.IGNORECASE)
            if match:
                results_count = int(match.group(1))

        # Method 2: Extract book data from JavaScript
        # Look for window.OverDrive.titleCollection
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.OverDrive.titleCollection' in script.string:
                # Extract the JSON array
                match = re.search(r'window\.OverDrive\.titleCollection\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                if match:
                    try:
                        title_collection = json.loads(match.group(1))
                        results_count = len(title_collection)

                        # Extract book details
                        for book in title_collection:
                            books.append({
                                'title': book.get('title', 'Unknown'),
                                'author': book.get('firstCreatorName', 'Unknown'),
                                'id': book.get('id', ''),
                                'available': book.get('isAvailable', False),
                                'formats': [fmt.get('name', '') for fmt in book.get('formats', [])]
                            })
                    except json.JSONDecodeError:
                        pass
                break

        return {
            'count': results_count,
            'books': books,
            'url': search_url
        }

    except requests.RequestException as e:
        print(f"Error searching for {author_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {author_name}: {e}")
        return None
