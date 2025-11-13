#!/usr/bin/env python3
"""
Search for audiobooks on Western Cape OverDrive library for authors from podcast episodes.
"""

import json
import time
import urllib.parse
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


def search_audiobooks_for_author(author_name: str, base_url: str = "https://westerncape.overdrive.com") -> Optional[Dict]:
    """
    Search for audiobooks by a specific author on OverDrive.

    Args:
        author_name: The name of the author to search for
        base_url: The base URL of the OverDrive library

    Returns:
        Dictionary with count and list of books, or None if the request failed
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


def test_single_author():
    """Test with a single author first."""
    print("Testing with Abdulrazak Gurnah...")
    result = search_audiobooks_for_author("Abdulrazak Gurnah")
    if result is not None:
        count = result['count']
        books = result['books']
        print(f"✓ Found {count} audiobook(s) for Abdulrazak Gurnah")
        if books:
            print("\nBooks found:")
            for i, book in enumerate(books, 1):
                print(f"  {i}. {book['title']} by {book['author']}")
        print("\nTest successful!")
    else:
        print("✗ Test failed - could not retrieve results")
    return result


def load_episodes(filepath: str = "data/bbc_world_book_club_episodes.json") -> List[Dict]:
    """Load episode data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_all_authors(episodes: List[Dict], delay: float = 1.0) -> Dict[str, Dict]:
    """
    Search for audiobooks for all unique authors.

    Args:
        episodes: List of episode dictionaries
        delay: Delay between requests in seconds (to be polite to the server)

    Returns:
        Dictionary mapping author names to result dictionaries with count and books
    """
    # Get unique authors
    authors = sorted(set(ep['author'] for ep in episodes if ep.get('author')))

    results = {}
    total = len(authors)

    print(f"\nSearching for audiobooks for {total} authors...\n")

    for i, author in enumerate(authors, 1):
        print(f"[{i}/{total}] Searching for {author}...", end=" ")
        result = search_audiobooks_for_author(author)

        if result is not None:
            count = result['count']
            results[author] = result
            print(f"✓ {count} audiobook(s)")
        else:
            print("✗ Failed")

        # Be polite - don't hammer the server
        if i < total:
            time.sleep(delay)

    return results


def print_results(results: Dict[str, Dict]):
    """Print results in a formatted way."""
    print("\n" + "=" * 70)
    print("AUDIOBOOK SEARCH RESULTS")
    print("=" * 70)

    # Sort by count (descending), then by author name
    sorted_results = sorted(results.items(), key=lambda x: (-x[1]['count'], x[0]))

    for author, result in sorted_results:
        count = result['count']
        books = result.get('books', [])

        print(f"\n{author:50} {count:3} audiobook(s)")

        # List the books if we have them
        if books:
            for book in books:
                available_text = " [AVAILABLE]" if book.get('available') else ""
                print(f"  • {book['title']}{available_text}")

    print("\n" + "=" * 70)
    print(f"Total authors searched: {len(results)}")
    print(f"Authors with audiobooks: {sum(1 for r in results.values() if r['count'] > 0)}")
    print(f"Total audiobooks found: {sum(r['count'] for r in results.values())}")
    print("=" * 70)


def save_results(results: Dict[str, Dict], filepath: str = "data/audiobook_search_results.json"):
    """Save results to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {filepath}")

    # Also save a CSV for easy viewing
    csv_filepath = filepath.replace('.json', '.csv')
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['Author', 'Audiobook Count', 'Book Titles', 'Search URL'])

        for author, result in sorted(results.items(), key=lambda x: (-x[1]['count'], x[0])):
            count = result['count']
            books = result.get('books', [])
            book_titles = '; '.join([book['title'] for book in books])
            url = result.get('url', '')
            writer.writerow([author, count, book_titles, url])

    print(f"CSV saved to {csv_filepath}")


def main():
    """Main function."""
    # First, test with single author
    print("=" * 70)
    print("STEP 1: Testing with single author")
    print("=" * 70)
    test_result = test_single_author()

    if test_result is None:
        print("\n⚠ Test failed. Please check the HTML structure or provide the HTML content.")
        return

    # Ask user if they want to continue
    print("\n" + "=" * 70)
    response = input("Continue with full search? (y/n): ").strip().lower()

    if response != 'y':
        print("Search cancelled.")
        return

    # Load episodes and search for all authors
    print("\nLoading episodes...")
    episodes = load_episodes()
    print(f"Loaded {len(episodes)} episodes")

    # Search for all authors
    results = search_all_authors(episodes, delay=1.0)

    # Print and save results
    print_results(results)
    save_results(results)


if __name__ == "__main__":
    main()
