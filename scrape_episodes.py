"""
Script to scrape BBC World Book Club episodes from all pages.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
import time
import argparse

def scrape_page(page_num):
    """
    Scrape episodes from a single page.

    Args:
        page_num: Page number (0 for first page, 1-13 for subsequent pages)

    Returns:
        List of episode dictionaries
    """
    if page_num == 0:
        url = "https://www.bbc.com/audio/brand/p003jhsk"
    else:
        url = f"https://www.bbc.com/audio/brand/p003jhsk?page={page_num}"

    print(f"Scraping page {page_num}: {url}")

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        episodes = []

        # Find all episode card containers using the test id
        episode_cards = soup.find_all('div', {'data-testid': 'york-card'})

        for card in episode_cards:
            # Find the link to the episode
            link = card.find('a', href=lambda x: x and '/audio/play/' in x)
            if not link:
                continue

            episode_url = link.get('href')
            if not episode_url:
                continue

            # Extract episode ID from URL
            episode_id = episode_url.split('/audio/play/')[-1]

            # Get full URL
            if not episode_url.startswith('http'):
                episode_url = f"https://www.bbc.com{episode_url}"

            # Extract title from the span with class sc-4d4e1117-7
            title_elem = card.find('span', class_='sc-4d4e1117-7')
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'

            # Extract date and duration from the div with class sc-4d4e1117-11
            date_duration_div = card.find('div', class_='sc-4d4e1117-11')
            date_text = 'Unknown'
            duration_text = 'Unknown'

            if date_duration_div:
                # Get all text content
                text = date_duration_div.get_text(strip=True)
                # Split by the bullet point
                if '•' in text:
                    parts = text.split('•')
                    if len(parts) >= 2:
                        date_text = parts[0].strip()
                        duration_text = parts[1].strip()

            episode = {
                'id': episode_id,
                'url': episode_url,
                'title': title,
                'date': date_text,
                'duration': duration_text,
                'page': page_num
            }

            episodes.append(episode)

        print(f"  Found {len(episodes)} episodes on page {page_num}")
        return episodes

    except Exception as e:
        print(f"Error scraping page {page_num}: {e}")
        return []


def scrape_all_episodes(start_page=0, end_page=13):
    """
    Scrape all episodes from all pages.

    Args:
        start_page: First page to scrape (default 0)
        end_page: Last page to scrape (default 13)

    Returns:
        List of all episodes
    """
    all_episodes = []

    for page_num in range(start_page, end_page + 1):
        episodes = scrape_page(page_num)
        all_episodes.extend(episodes)

        # Be nice to the server - add a small delay between requests
        if page_num < end_page:
            time.sleep(1)

    return all_episodes


def save_to_json(episodes, filename='data/bbc_world_book_club_episodes.json'):
    """Save episodes to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(episodes)} episodes to {filename}")


def save_to_csv(episodes, filename='data/bbc_world_book_club_episodes.csv'):
    """Save episodes to CSV file."""
    if not episodes:
        print("No episodes to save to CSV")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'date', 'duration', 'url', 'page'])
        writer.writeheader()
        writer.writerows(episodes)
    print(f"Saved {len(episodes)} episodes to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape BBC World Book Club episodes'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of episodes to scrape (default: scrape all)'
    )
    
    parser.add_argument(
        '--pages',
        type=int,
        default=13,
        help='Number of pages to scrape (default: 13, i.e., pages 0-13)'
    )
    
    args = parser.parse_args()
    
    print("Starting to scrape BBC World Book Club episodes...")
    print("=" * 60)

    # Scrape all pages (0 to end_page)
    episodes = scrape_all_episodes(0, args.pages)
    
    # Apply limit if specified
    if args.limit:
        episodes = episodes[:args.limit]
        print(f"\nLimited to {len(episodes)} episodes")

    print("\n" + "=" * 60)
    print(f"Total episodes scraped: {len(episodes)}")

    if episodes:
        # Save to JSON
        save_to_json(episodes)

        # Save to CSV
        save_to_csv(episodes)

        # Print some sample episodes
        print("\nFirst 5 episodes:")
        for i, ep in enumerate(episodes[:5], 1):
            print(f"{i}. {ep['title']}")
            print(f"   Date: {ep['date']} | Duration: {ep['duration']}")
            print(f"   URL: {ep['url']}")
            print()
    else:
        print("\nNo episodes were scraped. Please check the script and try again.")


if __name__ == "__main__":
    main()
