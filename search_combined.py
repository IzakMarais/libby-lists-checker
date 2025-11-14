#!/usr/bin/env python3
"""
Search for audiobooks in Western Cape OverDrive library for authors from multiple sources.
Supports both BBC World Book Club and Hugo Award authors.
"""

import json
import argparse
import os
from search_audiobooks import search_audiobooks_for_author
import time


def load_authors_from_json(filename):
    """
    Load authors from a JSON file.

    Args:
        filename: Path to JSON file

    Returns:
        List of author names
    """
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        # Could be a list of strings (hugo_award_authors.json)
        if data and isinstance(data[0], str):
            return data
        # Or a list of dicts (hugo_award_nominees.json)
        elif data and isinstance(data[0], dict):
            # Extract unique authors
            authors = set()
            for entry in data:
                if 'author' in entry:
                    authors.add(entry['author'])
            return sorted(list(authors))

    return []


def load_bbc_authors(filename='data/bbc_world_book_club_episodes.json'):
    """
    Load authors from BBC World Book Club episodes.
    First tries to load from bbc_world_book_club_authors.json,
    falls back to extracting from episodes if not found.

    Returns:
        List of author names
    """
    # Try loading from dedicated authors file first
    authors_file = 'data/bbc_world_book_club_authors.json'
    if os.path.exists(authors_file):
        authors = load_authors_from_json(authors_file)
        if authors:
            return authors

    # Fall back to extracting from episodes file
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []

    with open(filename, 'r', encoding='utf-8') as f:
        episodes = json.load(f)

    # Extract unique authors from episodes
    authors = set()
    for episode in episodes:
        if 'author' in episode and episode['author']:
            authors.add(episode['author'])

    return sorted(list(authors))


def load_hugo_authors(filename='data/hugo_award_authors.json'):
    """
    Load authors from Hugo Award data.

    Returns:
        List of author names
    """
    return load_authors_from_json(filename)


def load_booker_authors(filename='data/booker_prize_authors.json'):
    """
    Load authors from Booker Prize data.

    Returns:
        List of author names
    """
    return load_authors_from_json(filename)


def search_authors(authors, output_file, delay=2.0, limit=None):
    """
    Search for audiobooks for a list of authors.

    Args:
        authors: List of author names
        output_file: Path to save results
        delay: Delay between requests in seconds
        limit: Maximum number of authors to process (None for all)
    """
    if limit:
        authors = authors[:limit]
        print(f"\nSearching for audiobooks by {len(authors)} authors (limited)...")
    else:
        print(f"\nSearching for audiobooks by {len(authors)} authors...")
    print("=" * 60)

    results = {}

    for i, author in enumerate(authors, 1):
        print(f"\n[{i}/{len(authors)}] Searching for: {author}")

        result = search_audiobooks_for_author(author)

        if result:
            results[author] = {
                'count': result.get('count', 0),
                'books': result.get('books', []),
                'url': result.get('url', '')
            }
            print(f"  Found {result.get('count', 0)} audiobooks")
        else:
            print(f"  No results found")
            results[author] = {
                'count': 0,
                'books': [],
                'url': ''
            }

        # Delay between requests
        if i < len(authors):
            time.sleep(delay)

    # Save results
    print("\n" + "=" * 60)
    print(f"Saving results to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    total_books = sum(r['count'] for r in results.values())
    authors_with_books = sum(1 for r in results.values() if r['count'] > 0)

    print(f"\nSearch Summary:")
    print(f"  Total authors searched: {len(authors)}")
    print(f"  Authors with audiobooks: {authors_with_books}")
    print(f"  Total audiobooks found: {total_books}")


def main():
    parser = argparse.ArgumentParser(
        description='Search for audiobooks from multiple author sources'
    )

    parser.add_argument(
        '--source',
        choices=['bbc', 'hugo', 'booker', 'all'],
        default='all',
        help='Source of authors to search (default: all)'
    )

    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: data/{source}_audiobook_search_results.json)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of authors to process (default: process all)'
    )

    args = parser.parse_args()

    # Set default output filename based on source if not specified
    if args.output is None:
        args.output = f'data/{args.source}_audiobook_search_results.json'

    # Load authors based on source
    authors = []

    if args.source in ['bbc', 'all']:
        print("Loading BBC World Book Club authors...")
        bbc_authors = load_bbc_authors()
        authors.extend(bbc_authors)
        print(f"  Loaded {len(bbc_authors)} BBC authors")

    if args.source in ['hugo', 'all']:
        print("Loading Hugo Award authors...")
        hugo_authors = load_hugo_authors()
        authors.extend(hugo_authors)
        print(f"  Loaded {len(hugo_authors)} Hugo authors")

    if args.source in ['booker', 'all']:
        print("Loading Booker Prize authors...")
        booker_authors = load_booker_authors()
        authors.extend(booker_authors)
        print(f"  Loaded {len(booker_authors)} Booker Prize authors")

    if not authors:
        print("\nNo authors found. Please check your data files:")
        print("  - For BBC: data/bbc_world_book_club_episodes.json")
        print("  - For Hugo: data/hugo_award_authors.json")
        print("  - For Booker: data/booker_prize_authors.json")
        print("\nRun the appropriate scraper first:")
        print("  - BBC: python scrape_episodes.py")
        print("  - Hugo: python scrape_hugo_awards.py")
        print("  - Booker: python scrape_booker_prize.py")
        return

    # Remove duplicates while preserving order
    unique_authors = []
    seen = set()
    for author in authors:
        author_lower = author.lower()
        if author_lower not in seen:
            seen.add(author_lower)
            unique_authors.append(author)

    print(f"\nTotal unique authors: {len(unique_authors)}")

    # Search for audiobooks
    search_authors(unique_authors, args.output, args.delay, args.limit)


if __name__ == "__main__":
    main()
