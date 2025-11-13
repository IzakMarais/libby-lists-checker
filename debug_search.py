#!/usr/bin/env python3
"""
Debug script to show what the HTML looks like for a search result.
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup


def fetch_and_show_html(author_name: str):
    """Fetch the search page and show relevant HTML sections."""
    encoded_author = urllib.parse.quote(author_name)
    base_url = "https://westerncape.overdrive.com"
    search_url = f"{base_url}/search?query={encoded_author}&format=audiobook-overdrive%2Caudiobook-overdrive-provisional&sortBy=relevance"

    print(f"URL: {search_url}\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(search_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Save full HTML for inspection
    with open('debug_search_results.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Full HTML saved to debug_search_results.html\n")

    # Show first 5000 characters
    print("=" * 70)
    print("FIRST 5000 CHARACTERS OF HTML:")
    print("=" * 70)
    print(response.text[:5000])
    print("\n...")

    # Look for elements that might contain result count
    print("\n" + "=" * 70)
    print("ELEMENTS WITH 'RESULT' OR 'TITLE' IN CLASS/ID:")
    print("=" * 70)
    for elem in soup.find_all(attrs={'class': True}):
        classes = ' '.join(elem['class'])
        if 'result' in classes.lower() or 'title' in classes.lower():
            print(f"\nTag: {elem.name}, Class: {classes}")
            print(f"Text: {elem.get_text(strip=True)[:200]}")

    for elem in soup.find_all(attrs={'id': True}):
        elem_id = elem['id']
        if 'result' in elem_id.lower() or 'title' in elem_id.lower():
            print(f"\nTag: {elem.name}, ID: {elem_id}")
            print(f"Text: {elem.get_text(strip=True)[:200]}")


if __name__ == "__main__":
    fetch_and_show_html("Abdulrazak Gurnah")
