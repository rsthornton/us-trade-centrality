# Data Directory

## Included (redistributable)

| File | Description | Source |
|------|-------------|--------|
| `state_gdp_2017.csv` | State-level GDP for 2017 | Bureau of Economic Analysis |
| `state_population_2017.csv` | State population estimates for 2017 | U.S. Census Bureau |

## Required (must be obtained separately)

Two datasets must be downloaded before running the pipeline. Neither can be redistributed due to size and licensing.

### 1. CFS 2017 Public Use File (primary dataset)

- **Source**: U.S. Census Bureau, 2017 Commodity Flow Survey
- **URL**: <https://www.census.gov/data/datasets/2017/econ/cfs/historical-datasets.html>
- **File**: `cfs_2017_puf.csv`
- **Place at**: `data/cfs_2017_puf.csv`
- **Size**: ~477 MB
- **Records**: 5,978,523 shipment records from ~60,000 responding establishments
- **Documentation**: [CFS 2017 PUF Data Users Guide](https://www.census.gov/programs-surveys/cfs/technical-documentation/users-guide.html)

The pipeline uses columns: `ORIG_STATE`, `DEST_STATE`, `SHIPMT_VALUE`, `WGT_FACTOR`, `SCTG`. All other columns are ignored.

Trade values are computed as `SHIPMT_VALUE × WGT_FACTOR` per Census Bureau methodology (see PUF Users Guide §5).

### 2. FAF 5.7.1 State-Level Data (for 52×52 international network)

- **Source**: Bureau of Transportation Statistics, Freight Analysis Framework
- **URL**: <https://www.bts.gov/faf>
- **File**: `FAF5.7.1_State.csv`
- **Place at**: `data/FAF5.7.1_State.csv`
- **Size**: ~504 MB
- **Note**: Only required for `--international` (52×52) network runs. The domestic 51×51 analysis runs without this file.

## Setup

After downloading, verify your data files are in place:

```bash
python scripts/setup_data.py
```

Then install the toolkit and run the pipeline:

```bash
pip install -e cfs-network-toolkit/
python main.py                    # 51×51 domestic (default)
python main.py --international    # 52×52 with Rest of World node
```

## Pipeline data flow

```
cfs_2017_puf.csv
  → load (data_loader.py: 5,978,523 records, 5 columns)
  → preprocess (preprocessor.py: weighted_value = SHIPMT_VALUE × WGT_FACTOR, interstate filter)
  → aggregate (preprocessor.py: group by state pairs → edge list)
  → build network (network_builder.py: 51×51 weighted DiGraph)
  → compute centralities (centralities.py: betweenness, eigenvector, out-degree)
  → save (results/)
```

For the 52×52 network, FAF5 international edges are combined with CFS domestic edges before network construction.
