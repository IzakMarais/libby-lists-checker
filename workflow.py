#!/usr/bin/env python3
"""
Complete workflow script for finding library audiobooks from multiple sources.
This script orchestrates the entire pipeline from scraping to availability checking.
"""

import argparse
import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"STEP: {description}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n❌ Error: {description} failed with exit code {result.returncode}")
        return False

    print(f"\n✅ {description} completed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Complete workflow for finding library audiobooks from multiple sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow for Hugo awards only
  python workflow.py --source hugo

  # Run complete workflow for both sources
  python workflow.py --source both

  # Run only specific stages
  python workflow.py --stages scrape search

  # Skip certain stages
  python workflow.py --skip-scrape
        """
    )

    parser.add_argument(
        '--source',
        choices=['bbc', 'hugo', 'both'],
        default='both',
        help='Source of authors (default: both)'
    )

    parser.add_argument(
        '--stages',
        nargs='+',
        choices=['scrape', 'search', 'refine', 'availability'],
        help='Run only specified stages (default: all stages)'
    )

    parser.add_argument(
        '--skip-scrape',
        action='store_true',
        help='Skip scraping stage (use existing data)'
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
        help='Limit number of items to process in each stage (default: process all)'
    )

    args = parser.parse_args()

    # Determine which stages to run
    if args.stages:
        stages = set(args.stages)
    else:
        stages = {'scrape', 'search', 'refine', 'availability'}

    if args.skip_scrape:
        stages.discard('scrape')

    print("=" * 60)
    print("LIBRARY AUDIOBOOK FINDER - COMPLETE WORKFLOW")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Stages: {', '.join(sorted(stages))}")
    if args.limit:
        print(f"Limit: {args.limit} items per stage")
    print("=" * 60)

    # Stage 1: Scrape data
    if 'scrape' in stages:
        if args.source in ['bbc', 'both']:
            cmd = [sys.executable, 'scrape_episodes.py']
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if not run_command(cmd, "Scraping BBC World Book Club episodes"):
                return 1

        if args.source in ['hugo', 'both']:
            cmd = [sys.executable, 'scrape_hugo_awards.py']
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if not run_command(cmd, "Scraping Hugo Award nominees"):
                return 1

    # Stage 2: Search for audiobooks
    if 'search' in stages:
        # search_combined.py will automatically use data/{source}_audiobook_search_results.json
        cmd = [sys.executable, 'search_combined.py',
               '--source', args.source,
               '--delay', str(args.delay)]
        if args.limit:
            cmd.extend(['--limit', str(args.limit)])
        if not run_command(cmd, f"Searching library for audiobooks ({args.source})"):
            return 1

    # Stage 3: Refine results
    if 'refine' in stages:
        input_file = f"data/{args.source}_audiobook_search_results.json"

        if os.path.exists(input_file):
            cmd = [sys.executable, 'refine_audiobooks.py',
                   '--input', input_file]
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if not run_command(cmd, f"Refining results ({args.source})"):
                return 1
        else:
            print(f"\n⚠️  Skipping refine stage: {input_file} not found")

    # Stage 4: Check availability
    if 'availability' in stages:
        refined_file = f"data/{args.source}_audiobook_search_results_refined.json"

        if os.path.exists(refined_file):
            cmd = [sys.executable, 'check_availability.py',
                   '--input', refined_file,
                   '--output', f"data/{args.source}_available_audiobooks.json"]
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if not run_command(cmd, f"Checking availability ({args.source})"):
                return 1
        else:
            print(f"\n⚠️  Skipping availability check: {refined_file} not found")
            print(f"   Run refine stage first")

    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nOutput files:")

    if args.source in ['bbc', 'both']:
        print(f"  BBC Episodes: data/bbc_world_book_club_episodes.json")

    if args.source in ['hugo', 'both']:
        print(f"  Hugo Nominees: data/hugo_award_nominees.json")
        print(f"  Hugo Authors: data/hugo_award_authors.json")

    print(f"  Search Results: data/{args.source}_audiobook_search_results.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
