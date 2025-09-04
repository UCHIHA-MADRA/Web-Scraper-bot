#!/usr/bin/env python3
"""
Test runner script for web-scraping-bot

This script runs all tests and generates coverage reports.
It can be used to verify that all components are working correctly.
"""
import os
import sys
import subprocess
import argparse

def run_tests(verbose=False, coverage=True, specific_test=None):
    """Run pytest with specified options
    
    Args:
        verbose (bool): Whether to show verbose output
        coverage (bool): Whether to generate coverage reports
        specific_test (str): Run a specific test file or directory
    
    Returns:
        int: Exit code from pytest
    """
    # Construct command
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    
    # Add coverage
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=term', '--cov-report=html'])
    
    # Add specific test if provided
    if specific_test:
        cmd.append(specific_test)
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description='Run tests for web-scraping-bot')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('-t', '--test', help='Run a specific test file or directory')
    args = parser.parse_args()
    
    # Run tests
    exit_code = run_tests(
        verbose=args.verbose,
        coverage=not args.no_coverage,
        specific_test=args.test
    )
    
    # Report results
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if not args.no_coverage:
            print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())