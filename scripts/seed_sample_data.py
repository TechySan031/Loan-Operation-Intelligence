"""
Seed Sample Data Script

Creates mock borrower data and sample loans for testing.

Usage:
    python -m scripts.seed_sample_data
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sample borrowers defined in voice_service.py MOCK_BORROWERS
# This script could populate a proper database table in production


async def main():
    print("Sample data is currently defined in voice_service.py as MOCK_BORROWERS")
    print("In production, this would seed a borrowers/loans table")
    # TODO: Create and seed a borrowers table for production use


if __name__ == "__main__":
    asyncio.run(main())
