"""
Load CFS 2017 and FAF5 data for network construction.

Reads the raw Census Bureau microdata, keeping only the columns
needed for trade network construction (origin, destination, value, weight).
"""

import pandas as pd
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def load_cfs_data(filepath, sample_size=None):
    """
    Load essential CFS 2017 columns with optional sampling.
    
    Args:
        filepath (str): Path to cfs_2017_puf.csv
        sample_size (int, optional): Number of records to sample for testing
        
    Returns:
        pd.DataFrame: Essential columns for network analysis
            - ORIG_STATE: Origin state code
            - DEST_STATE: Destination state code  
            - SHIPMT_VALUE: Shipment value ($)
            - WGT_FACTOR: Survey weight factor
            - SCTG: Commodity code (for sector analysis)
            
    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If required columns missing
    """
    
    # Essential columns only (memory efficient)
    required_columns = ['ORIG_STATE', 'DEST_STATE', 'SHIPMT_VALUE', 'WGT_FACTOR', 'SCTG']
    
    # Validate file exists
    if not Path(filepath).exists():
        raise FileNotFoundError(f"CFS data file not found: {filepath}")
    
    log.info(f"Loading CFS data from: {filepath}")
    
    try:
        # Load with optimal settings
        df = pd.read_csv(
            filepath,
            usecols=required_columns,  # Memory efficient - only load needed columns
            nrows=sample_size if sample_size else None,
            dtype={
                'ORIG_STATE': 'int8',      # State codes 1-56, fits in int8
                'DEST_STATE': 'int8', 
                'SHIPMT_VALUE': 'float32',  # Sufficient precision for currency
                'WGT_FACTOR': 'float32',
                'SCTG': 'category'          # Commodity codes - categorical saves memory
            }
        )
        
        # Validate all required columns present
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Report loading success
        total_records = len(df)
        if sample_size:
            log.info(f"Loaded {total_records:,} records (sample)")
        else:
            log.info(f"Loaded {total_records:,} records (complete dataset)")
            
        log.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        return df
        
    except Exception as e:
        log.error(f"Error loading CFS data: {e}")
        raise


def validate_data_structure(df):
    """
    Perform basic validation on loaded CFS data.
    
    Args:
        df (pd.DataFrame): Loaded CFS data
        
    Returns:
        dict: Validation report with summary statistics
    """
    
    validation = {
        'total_records': len(df),
        'null_values': df.isnull().sum().to_dict(),
        'state_code_range': {
            'orig_min': df['ORIG_STATE'].min(),
            'orig_max': df['ORIG_STATE'].max(),
            'dest_min': df['DEST_STATE'].min(), 
            'dest_max': df['DEST_STATE'].max()
        },
        'value_stats': {
            'total_shipment_value': df['SHIPMT_VALUE'].sum(),
            'zero_values': (df['SHIPMT_VALUE'] == 0).sum(),
            'negative_values': (df['SHIPMT_VALUE'] < 0).sum()
        }
    }
    
    # Print validation summary
    print("\nData Validation Summary:")
    print(f"   Records: {validation['total_records']:,}")
    print(f"   Null values: {sum(validation['null_values'].values())}")
    print(f"   State codes: {validation['state_code_range']['orig_min']}-{validation['state_code_range']['orig_max']}")
    print(f"   Total value: ${validation['value_stats']['total_shipment_value']:,.0f}")
    
    return validation


def load_data(config):
    """
    Unified data loader dispatcher - supports both CFS and FAF5 sources.
    
    Args:
        config (dict): Configuration with data source specification
        
    Returns:
        pd.DataFrame: Loaded data ready for network construction
            - CFS source: Returns row-level records for preprocessing
            - FAF source: Returns aggregated edge list ready for network building
        
    Config Format:
        {
            'data': {
                'source': 'cfs' | 'faf',
                'source_file': 'path/to/cfs.csv',    # for CFS
                'faf_path': 'path/to/faf5.csv',      # for FAF5
                'sample_size': int,                   # optional for CFS
                'year': int                           # optional for FAF5
            },
            'filters': {                              # optional for FAF5
                'modes': [1,2,3],                     # transport modes
                'sctg2': ['15','16','17']             # commodity codes
            }
        }
    """
    
    source = config['data'].get('source', 'cfs')
    
    # Validate required config keys and file paths per source
    if source == 'cfs':
        if 'source_file' not in config['data']:
            raise ValueError("config['data']['source_file'] is required for source='cfs'")
        
        cfs_path = Path(config['data']['source_file'])
        if not cfs_path.exists():
            raise FileNotFoundError(f"CFS file not found: {cfs_path}")
        
        return load_cfs_data(
            config['data']['source_file'],
            config['data'].get('sample_size')
        )
    
    elif source == 'faf':
        if 'faf_path' not in config['data']:
            raise ValueError("config['data']['faf_path'] is required for source='faf'")
        
        faf_path = Path(config['data']['faf_path'])
        if not faf_path.exists():
            raise FileNotFoundError(f"FAF5 file not found: {faf_path}")
        
        # Import FAF5 loader
        try:
            from .faf_loader import load_faf5_international_edges
        except ImportError:
            raise ImportError("FAF5 loader not available. Check faf_loader.py module.")
        
        # Extract filter sets if provided
        mode_filter = None
        sctg2_filter = None
        if 'filters' in config:
            if 'modes' in config['filters']:
                mode_filter = set(config['filters']['modes'])
            if 'sctg2' in config['filters']:
                sctg2_filter = set(str(s) for s in config['filters']['sctg2'])
        
        return load_faf5_international_edges(
            filepath=config['data']['faf_path'],
            year=config['data'].get('year', 2017),
            mode_filter=mode_filter,
            sctg2_filter=sctg2_filter,
        )
    
    else:
        raise ValueError(f"Unknown data source: {source}. Must be 'cfs' or 'faf'")