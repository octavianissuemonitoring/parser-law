"""
Script to run import from command line.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services import run_import


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Import legislative acts from CSV files")
    parser.add_argument(
        "--dir",
        default="../rezultate",
        help="Path to rezultate directory (default: ../rezultate)",
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_import(args.dir))
