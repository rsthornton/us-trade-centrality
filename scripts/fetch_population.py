#!/usr/bin/env python3
"""Fetch state population data from Census API.

Creates state_population_2017.csv with:
- 2017 ACS 1-Year estimates (matches CFS 2017 vintage)
- 2020 Decennial Census counts (most accurate)

No API key required for basic queries.
"""

import requests
import pandas as pd
from pathlib import Path

# Census API endpoints
ACS_2017_URL = "https://api.census.gov/data/2017/acs/acs1"
DECENNIAL_2020_URL = "https://api.census.gov/data/2020/dec/pl"

# FIPS to state abbreviation mapping (matches thesis codebase)
FIPS_TO_STATE = {
    1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT',
    10: 'DE', 11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID',
    17: 'IL', 18: 'IN', 19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA',
    23: 'ME', 24: 'MD', 25: 'MA', 26: 'MI', 27: 'MN', 28: 'MS',
    29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV', 33: 'NH', 34: 'NJ',
    35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH', 40: 'OK',
    41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN',
    48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV',
    55: 'WI', 56: 'WY'
}

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
    'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
    'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
    'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
    'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
    'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
    'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
}


def fetch_acs_2017():
    """Fetch 2017 ACS 1-Year population estimates."""
    print("Fetching 2017 ACS 1-Year estimates...")

    # B01003_001E = Total Population
    url = f"{ACS_2017_URL}?get=NAME,B01003_001E&for=state:*"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    # First row is header: ['NAME', 'B01003_001E', 'state']
    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)
    df['fips'] = df['state'].astype(int)
    df['pop_2017_acs'] = df['B01003_001E'].astype(int)

    print(f"  Retrieved {len(df)} states")
    return df[['fips', 'pop_2017_acs']]


def fetch_decennial_2020():
    """Fetch 2020 Decennial Census population counts."""
    print("Fetching 2020 Decennial Census counts...")

    # P1_001N = Total Population (PL 94-171 redistricting data)
    url = f"{DECENNIAL_2020_URL}?get=NAME,P1_001N&for=state:*"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)
    df['fips'] = df['state'].astype(int)
    df['pop_2020_decennial'] = df['P1_001N'].astype(int)

    print(f"  Retrieved {len(df)} states")
    return df[['fips', 'pop_2020_decennial']]


def main():
    """Fetch and merge population data, save to CSV."""
    print("=" * 60)
    print("Census Population Data Fetcher")
    print("=" * 60)

    # Fetch both datasets
    acs_df = fetch_acs_2017()
    dec_df = fetch_decennial_2020()

    # Merge on FIPS
    merged = acs_df.merge(dec_df, on='fips', how='outer')

    # Add state abbreviations and names
    merged['state_abbrev'] = merged['fips'].map(FIPS_TO_STATE)
    merged['state_name'] = merged['state_abbrev'].map(STATE_NAMES)

    # Filter to only states in our thesis (51 = 50 states + DC)
    valid_fips = set(FIPS_TO_STATE.keys())
    merged = merged[merged['fips'].isin(valid_fips)].copy()

    # Reorder columns
    final = merged[['fips', 'state_abbrev', 'state_name', 'pop_2017_acs', 'pop_2020_decennial']]
    final = final.sort_values('fips').reset_index(drop=True)

    # Save to data directory
    output_path = Path(__file__).parent.parent / "data" / "state_population_2017.csv"
    final.to_csv(output_path, index=False)

    print()
    print("=" * 60)
    print(f"SUCCESS: Saved {len(final)} states to:")
    print(f"  {output_path}")
    print("=" * 60)
    print()
    print("Sample data:")
    print(final.head(10).to_string(index=False))
    print()
    print(f"Total 2017 ACS population: {final['pop_2017_acs'].sum():,}")
    print(f"Total 2020 Decennial population: {final['pop_2020_decennial'].sum():,}")

    return final


if __name__ == "__main__":
    main()
