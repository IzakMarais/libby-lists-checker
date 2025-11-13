#!/usr/bin/env python3
"""
Refine audiobook search results to include only books where the author
matches the searched author.
"""

import json
import csv
from typing import Dict, List
from difflib import SequenceMatcher


def normalize_name(name: str) -> str:
    """
    Normalize author name for comparison.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove common punctuation
    """
    import re
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = ' '.join(name.split())  # Normalize whitespace
    return name


def names_match(searched_author: str, book_author: str, threshold: float = 0.85) -> bool:
    """
    Check if two author names match, accounting for slight variations.

    Args:
        searched_author: The author name that was searched for
        book_author: The author name from the book metadata
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if names are similar enough to be considered a match
    """
    # Normalize both names
    search_norm = normalize_name(searched_author)
    book_norm = normalize_name(book_author)

    # Exact match after normalization
    if search_norm == book_norm:
        return True

    # Check if one is contained in the other (handles "AS Byatt" vs "A.S. Byatt")
    if search_norm in book_norm or book_norm in search_norm:
        return True

    # Use fuzzy matching for slight variations
    similarity = SequenceMatcher(None, search_norm, book_norm).ratio()
    return similarity >= threshold


def refine_results(input_file: str = "audiobook_search_results.json") -> Dict:
    """
    Load results and filter to keep only books where author matches searched author.

    Args:
        input_file: Path to the input JSON file

    Returns:
        Dictionary with refined results
    """
    print(f"Loading results from {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    refined_results = {}
    total_books_before = 0
    total_books_after = 0
    authors_changed = []

    print("\nRefining results...\n")

    for searched_author, data in results.items():
        original_count = data['count']
        original_books = data['books']
        total_books_before += original_count

        # Filter books to only include matching authors
        matching_books = [
            book for book in original_books
            if names_match(searched_author, book['author'])
        ]

        refined_count = len(matching_books)
        total_books_after += refined_count

        # Store refined results
        refined_results[searched_author] = {
            'count': refined_count,
            'books': matching_books,
            'url': data['url'],
            'original_count': original_count,
            'filtered_count': original_count - refined_count
        }

        # Report if there was a change
        if original_count != refined_count:
            authors_changed.append({
                'author': searched_author,
                'before': original_count,
                'after': refined_count,
                'removed': original_count - refined_count
            })
            print(f"✓ {searched_author}: {original_count} → {refined_count} audiobooks "
                  f"(removed {original_count - refined_count})")

            # Show which books were removed
            removed_books = [
                book for book in original_books
                if not names_match(searched_author, book['author'])
            ]
            for book in removed_books:
                print(f"  ✗ Removed: '{book['title']}' by {book['author']}")

    # Summary
    print("\n" + "=" * 70)
    print("REFINEMENT SUMMARY")
    print("=" * 70)
    print(f"Total authors: {len(results)}")
    print(f"Authors with changes: {len(authors_changed)}")
    print(f"Total books before: {total_books_before}")
    print(f"Total books after: {total_books_after}")
    print(f"Books removed: {total_books_before - total_books_after}")
    print("=" * 70)

    if authors_changed:
        print("\nAuthors with most books removed:")
        authors_changed.sort(key=lambda x: x['removed'], reverse=True)
        for i, change in enumerate(authors_changed[:10], 1):
            print(f"{i}. {change['author']}: removed {change['removed']} books "
                  f"({change['before']} → {change['after']})")

    return refined_results


def save_refined_results(results: Dict, output_file: str = "audiobook_search_results_refined.json"):
    """Save refined results to JSON and CSV files."""

    # Save JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        # Create a cleaner version without the original_count and filtered_count
        clean_results = {}
        for author, data in results.items():
            clean_results[author] = {
                'count': data['count'],
                'books': data['books'],
                'url': data['url']
            }
        json.dump(clean_results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Refined JSON saved to {output_file}")

    # Save CSV
    csv_file = output_file.replace('.json', '.csv')
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Author', 'Audiobook Count', 'Book Titles', 'Search URL'])

        for author, data in sorted(results.items(), key=lambda x: (-x[1]['count'], x[0])):
            count = data['count']
            books = data['books']
            book_titles = '; '.join([book['title'] for book in books])
            url = data['url']
            writer.writerow([author, count, book_titles, url])

    print(f"✓ Refined CSV saved to {csv_file}")

    # Save a detailed CSV showing what changed
    changes_csv = output_file.replace('.json', '_changes.csv')
    with open(changes_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Author', 'Original Count', 'Refined Count', 'Books Removed'])

        for author, data in sorted(results.items(), key=lambda x: (-x[1].get('filtered_count', 0), x[0])):
            if data.get('filtered_count', 0) > 0:
                writer.writerow([
                    author,
                    data['original_count'],
                    data['count'],
                    data['filtered_count']
                ])

    print(f"✓ Changes summary saved to {changes_csv}")


def print_refined_results(results: Dict):
    """Print refined results in a formatted way."""
    print("\n" + "=" * 70)
    print("REFINED AUDIOBOOK RESULTS")
    print("=" * 70)

    # Only show authors with books
    authors_with_books = {k: v for k, v in results.items() if v['count'] > 0}

    for author, data in sorted(authors_with_books.items(), key=lambda x: (-x[1]['count'], x[0])):
        count = data['count']
        books = data['books']

        print(f"\n{author:50} {count:3} audiobook(s)")

        for book in books:
            available_text = " [AVAILABLE]" if book.get('available') else ""
            print(f"  • {book['title']}{available_text}")

    print("\n" + "=" * 70)
    print(f"Total authors with audiobooks: {len(authors_with_books)}")
    print(f"Total audiobooks: {sum(r['count'] for r in results.values())}")
    print("=" * 70)


def main():
    """Main function."""
    print("=" * 70)
    print("AUDIOBOOK SEARCH RESULTS REFINEMENT")
    print("=" * 70)
    print("This script filters search results to include only books where")
    print("the author matches the searched author name.")
    print("=" * 70)

    # Refine the results
    refined = refine_results()

    # Save refined results
    save_refined_results(refined)

    # Print refined results
    print_refined_results(refined)


if __name__ == "__main__":
    main()
