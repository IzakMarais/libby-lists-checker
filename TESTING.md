# End-to-End Testing Guide

## Overview

The Library Audiobook Finder now includes comprehensive end-to-end testing capabilities that allow you to validate the entire workflow with small datasets. This is useful for:

- **Development**: Quickly test changes without processing hundreds of authors
- **Validation**: Ensure all pipeline stages work correctly
- **Debugging**: Isolate issues by testing with minimal data
- **CI/CD**: Run fast smoke tests before deployment

## Quick Start

### Test Both Sources (Recommended for first test)

```bash
# Quick smoke test with 2 items per source
python test_e2e.py --source both --limit 2

# More thorough test with 5 items
python test_e2e.py --source both --limit 5
```

### Test Individual Sources

```bash
# Test BBC World Book Club workflow
python test_e2e.py --source bbc --limit 3

# Test Hugo Awards workflow
python test_e2e.py --source hugo --limit 3
```

## Test Script Options

### `test_e2e.py`

Main end-to-end test script that orchestrates the complete workflow with limited data.

**Arguments:**

- `--source {bbc,hugo,both}` - Which source(s) to test (default: both)
- `--limit N` - Number of items to process per stage (default: 3)
- `--delay SECONDS` - Delay between requests (default: 0.5)

**Examples:**

```bash
# Fast smoke test
python test_e2e.py --limit 2 --delay 0.3

# Test only Hugo workflow with 10 authors
python test_e2e.py --source hugo --limit 10

# Test BBC with slower requests (more respectful)
python test_e2e.py --source bbc --limit 5 --delay 1.0
```

## Manual Testing with Individual Scripts

All core scripts now support a `--limit` parameter for testing purposes:

### Stage 1: Scraping

```bash
# Scrape only 5 BBC episodes
python scrape_episodes.py --limit 5

# Scrape only 10 Hugo award entries
python scrape_hugo_awards.py --limit 10
```

### Stage 2: Searching

```bash
# Search for only 3 authors
python search_combined.py --source hugo --limit 3 --delay 0.5

# Search for 5 BBC authors
python search_combined.py --source bbc --limit 5
```

### Stage 3: Refining

```bash
# Refine only first 5 authors from search results
python refine_audiobooks.py --input data/hugo_audiobook_search_results.json --limit 5
```

### Stage 4: Availability Check

```bash
# Check availability for only 10 books
python check_availability.py --input data/hugo_audiobook_search_results_refined.json --limit 10
```

## Complete Workflow with Limits

The main workflow script also supports limiting:

```bash
# Run complete workflow with limit
python workflow.py --source hugo --limit 5 --delay 0.5

# Run only search and refine stages with limit
python workflow.py --source bbc --stages search refine --limit 3
```

## Testing Strategy

### Smoke Test (Fast - 1-2 minutes)

Validates that all stages can run without errors:

```bash
python test_e2e.py --limit 2 --delay 0.3
```

**What it checks:**

- All scripts execute without errors
- Output files are created
- Data flows correctly between stages

### Integration Test (Medium - 5-10 minutes)

More thorough test with realistic data samples:

```bash
python test_e2e.py --limit 5 --delay 0.5
```

**What it checks:**

- Author name matching works correctly
- Audiobook search returns valid results
- Availability checking handles various states
- Larger sample for edge cases

### Pre-deployment Test (Slower - 15-30 minutes)

Comprehensive test before running full production workflow:

```bash
python test_e2e.py --limit 20 --delay 1.0
```

**What it checks:**

- Full pipeline handles substantial data
- Rate limiting works correctly
- No memory issues with larger datasets
- Output quality is consistent

## Understanding Test Output

### Successful Test

```
==================================================
TESTING HUGO WORKFLOW (LIMIT: 3)
==================================================

Running: python workflow.py --source hugo --limit 3 --delay 0.5

[... workflow output ...]

✅ HUGO test PASSED

Generated files:
  ✓ data/hugo_award_nominees.json (1234 bytes)
  ✓ data/hugo_award_authors.json (567 bytes)
  ✓ data/hugo_audiobook_search_results.json (2345 bytes)
  ✓ data/hugo_audiobook_search_results_refined.json (1890 bytes)
  ✓ data/hugo_available_audiobooks.json (456 bytes)
```

### Failed Test

If a test fails, check:

1. **Network connectivity** - Scripts need internet access
2. **Dependencies** - Ensure `requirements.in` packages are installed
3. **Data files** - Check if required input files exist
4. **API changes** - Website structure may have changed

## Continuous Testing During Development

When making changes to the codebase, use this workflow:

1. **Make your changes** to one or more scripts
2. **Run quick smoke test**:
   ```bash
   python test_e2e.py --limit 2
   ```
3. **If smoke test passes**, run integration test:
   ```bash
   python test_e2e.py --limit 5
   ```
4. **If all tests pass**, your changes are ready!

## Data Files Generated During Testing

Test runs create/overwrite these files in the `data/` directory:

### BBC Test Files

- `bbc_world_book_club_episodes.json` - Limited episodes
- `bbc_audiobook_search_results.json` - Search results for limited authors
- `bbc_audiobook_search_results_refined.json` - Filtered results
- `bbc_available_audiobooks.json` - Available books

### Hugo Test Files

- `hugo_award_nominees.json` - Limited nominations
- `hugo_award_authors.json` - Extracted unique authors
- `hugo_audiobook_search_results.json` - Search results for limited authors
- `hugo_audiobook_search_results_refined.json` - Filtered results
- `hugo_available_audiobooks.json` - Available books

**Note:** Test runs will overwrite these files. If you want to preserve production data, make backups first.

## Best Practices

1. **Start small**: Begin with `--limit 2` to validate basic functionality
2. **Respect rate limits**: Use reasonable `--delay` values (≥0.5s recommended)
3. **Test both sources**: Ensure changes work for BBC and Hugo workflows
4. **Check output quality**: Verify generated files contain expected data
5. **Clean test data**: Consider backing up production data before testing

## Troubleshooting

### Test runs too slowly

```bash
# Reduce limit and delay
python test_e2e.py --limit 2 --delay 0.3
```

### Want to test specific stage

```bash
# Test only search stage
python workflow.py --source hugo --stages search --limit 3
```

### Need to debug a specific author

```bash
# Test with single author using existing data
python check_by_author.py "Isaac Asimov"
```

## Integration with Development Workflow

### Before committing code:

```bash
# Run quick validation
python test_e2e.py --limit 3
```

### Before pushing to main branch:

```bash
# Run thorough validation
python test_e2e.py --limit 10
```

### Before production run:

```bash
# Run comprehensive test
python test_e2e.py --limit 20 --delay 1.0
```

## Future Enhancements

Potential improvements to the testing framework:

- **Unit tests**: Add pytest-based unit tests for individual functions
- **Mock data**: Use pre-recorded API responses for offline testing
- **Automated CI**: GitHub Actions workflow for automated testing
- **Coverage reports**: Track code coverage with pytest-cov
- **Performance benchmarks**: Track execution time and memory usage
- **Validation tests**: Verify data quality and consistency

## Summary

The testing framework provides:

✅ **Fast validation** - Test complete workflow in minutes
✅ **Configurable limits** - Control data volume for each test
✅ **Flexible testing** - Test individual scripts or complete workflow
✅ **Clear feedback** - Visual confirmation of test results
✅ **Development friendly** - Iterate quickly during development

Use `python test_e2e.py --help` for complete usage information.
