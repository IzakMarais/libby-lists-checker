#!/usr/bin/env python3
"""
End-to-end test script for the Library Audiobook Finder workflow.

This script runs quick tests with a small number of items to validate
the entire pipeline works correctly for both BBC and Hugo sources.
"""

import argparse
import subprocess
import sys
import os


def run_test(source, limit, delay=0.5):
    """
    Run an end-to-end test for a specific source.

    Args:
        source: 'bbc', 'hugo', 'booker', or 'nobel'
        limit: Number of items to process
        delay: Delay between requests

    Returns:
        Boolean indicating success
    """
    print("\n" + "=" * 70)
    print(f"TESTING {source.upper()} WORKFLOW (LIMIT: {limit})")
    print("=" * 70)

    # Run the workflow with limit
    cmd = [
        sys.executable, 'workflow.py',
        '--source', source,
        '--limit', str(limit),
        '--delay', str(delay)
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n❌ {source.upper()} test FAILED")
        return False

    print(f"\n✅ {source.upper()} test PASSED")

    # Print output file locations
    print("\nGenerated files:")

    if source == 'bbc':
        files = [
            'data/bbc_world_book_club_episodes.json',
            'data/bbc_audiobook_search_results.json',
            'data/bbc_audiobook_search_results_refined.json',
            'data/bbc_available_audiobooks.json'
        ]
    elif source == 'hugo':
        files = [
            'data/hugo_award_nominees.json',
            'data/hugo_award_authors.json',
            'data/hugo_audiobook_search_results.json',
            'data/hugo_audiobook_search_results_refined.json',
            'data/hugo_available_audiobooks.json'
        ]
    elif source == 'booker':
        files = [
            'data/booker_prize_nominees.json',
            'data/booker_prize_authors.json',
            'data/booker_audiobook_search_results.json',
            'data/booker_audiobook_search_results_refined.json',
            'data/booker_available_audiobooks.json'
        ]
    else:  # nobel
        files = [
            'data/nobel_literature_laureates.json',
            'data/nobel_literature_authors.json',
            'data/nobel_audiobook_search_results.json',
            'data/nobel_audiobook_search_results_refined.json',
            'data/nobel_available_audiobooks.json'
        ]

    for file_path in files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            print(f"  ✗ {file_path} (missing)")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Run end-to-end tests of the audiobook finder workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test BBC workflow with 3 episodes
  python test_e2e.py --source bbc --limit 3

  # Test Hugo workflow with 5 authors
  python test_e2e.py --source hugo --limit 5

  # Test Booker workflow with 5 authors
  python test_e2e.py --source booker --limit 5

  # Test Nobel workflow with 5 authors
  python test_e2e.py --source nobel --limit 5

  # Test all workflows with 2 items each (quick smoke test)
  python test_e2e.py --source all --limit 2

  # Test with faster delays (less respectful to servers)
  python test_e2e.py --source hugo --limit 3 --delay 0.3
        """
    )

    parser.add_argument(
        '--source',
        choices=['bbc', 'hugo', 'booker', 'nobel', 'all'],
        default='all',
        help='Source to test (default: all)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=3,
        help='Number of items to process in each stage (default: 3)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("LIBRARY AUDIOBOOK FINDER - END-TO-END TESTS")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  Source(s): {args.source}")
    print(f"  Limit per stage: {args.limit}")
    print(f"  Request delay: {args.delay}s")
    print("=" * 70)

    success = True

    if args.source in ['bbc', 'all']:
        if not run_test('bbc', args.limit, args.delay):
            success = False

    if args.source in ['hugo', 'all']:
        if not run_test('hugo', args.limit, args.delay):
            success = False

    if args.source in ['booker', 'all']:
        if not run_test('booker', args.limit, args.delay):
            success = False

    if args.source in ['nobel', 'all']:
        if not run_test('nobel', args.limit, args.delay):
            success = False

    # Final summary
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
