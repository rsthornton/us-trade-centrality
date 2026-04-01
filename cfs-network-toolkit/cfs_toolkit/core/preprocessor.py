"""
Transform raw CFS/FAF5 data into weighted edge lists.

Handles survey weighting (WGT_FACTOR x SHIPMT_VALUE), interstate
filtering, and state-pair aggregation for both data sources.
"""

import pandas as pd
import logging

log = logging.getLogger(__name__)


def preprocess_cfs_data(df, interstate_only=True, sctg2_filter=None):
    """
    Clean and filter CFS shipment records.
    
    Args:
        df (pd.DataFrame): Raw CFS data from data_loader
        interstate_only (bool): Filter out intrastate flows
        sctg2_filter (list, optional): 2-digit SCTG codes to include
        
    Returns:
        pd.DataFrame: Cleaned CFS records ready for aggregation
        
    Processing Steps:
        1. Create weighted_value (survey weight × shipment value)
        2. Filter by commodity codes (optional)
        3. Filter interstate vs intrastate flows
        4. Validate data quality
    """
    
    df = df.copy()
    
    # float64 avoids accumulation errors on 5.9M rows
    df['SHIPMT_VALUE'] = df['SHIPMT_VALUE'].astype('float64')
    df['WGT_FACTOR'] = df['WGT_FACTOR'].astype('float64')
    df['weighted_value'] = df['SHIPMT_VALUE'] * df['WGT_FACTOR']
    
    log.info(f"CFS preprocessing started: {len(df):,} raw records")
    
    if sctg2_filter:
        # Extract and normalize SCTG codes to 2-digit format, handling nulls
        sctg_series = (df['SCTG'].astype('string')
                      .str.extract(r'^(\d{1,2})', expand=False)
                      .fillna(''))
        sctg2_set = set(str(code).zfill(2) for code in sctg2_filter)
        df = df[sctg_series.isin(sctg2_set)]
        log.info(f"After commodity filter: {len(df):,} records")
    
    if interstate_only:
        df = df[df['ORIG_STATE'] != df['DEST_STATE']]
        log.info(f"After interstate filter: {len(df):,} records")
    
    # Remove records with missing or invalid state codes
    df = df[
        (df['ORIG_STATE'].between(1, 56)) & 
        (df['DEST_STATE'].between(1, 56)) &
        (df['weighted_value'] > 0)
    ]
    
    # Remove any remaining null values
    df = df.dropna(subset=['ORIG_STATE', 'DEST_STATE', 'weighted_value'])
    
    log.info(f"After quality validation: {len(df):,} records")
    log.info(f"Total weighted value: ${df['weighted_value'].sum():,.0f}")
    
    return df


def aggregate_cfs_to_edges(df):
    """
    Aggregate CFS records to state-to-state edge list.
    
    Args:
        df (pd.DataFrame): Preprocessed CFS data
        
    Returns:
        pd.DataFrame: Edge list with columns ['ORIG_STATE', 'DEST_STATE', 'SHIPMT_VALUE']
        
    Note: Aggregates multiple shipments between same state pairs,
          properly handling survey weights.
    """
    
    log.info(f"Aggregating {len(df):,} CFS records to edge list")
    
    edges = (
        df.groupby(['ORIG_STATE', 'DEST_STATE'], as_index=False)
        .agg({'weighted_value': 'sum'})
        .rename(columns={'weighted_value': 'SHIPMT_VALUE'})
    )
    
    edges['ORIG_STATE'] = edges['ORIG_STATE'].astype('int16')
    edges['DEST_STATE'] = edges['DEST_STATE'].astype('int16')  
    edges['SHIPMT_VALUE'] = edges['SHIPMT_VALUE'].astype('float64')
    
    log.info(f"CFS edge aggregation complete:")
    log.info(f"   Output edges: {len(edges):,}")
    log.info(f"   Total value: ${edges['SHIPMT_VALUE'].sum():,.0f}")
    log.info(f"   Value range: ${edges['SHIPMT_VALUE'].min():,.0f} - ${edges['SHIPMT_VALUE'].max():,.0f}")
    
    return edges


def preprocess_faf_edges(edges):
    """
    Minimal preprocessing for FAF5 edges (already clean from loader).
    
    Args:
        edges (pd.DataFrame): Clean edge list from FAF5 loader
        
    Returns:
        pd.DataFrame: Validated edge list (schema already correct)
        
    Note: FAF5 loader already outputs clean, aggregated edges.
          This function provides validation and consistency checking.
    """
    
    log.info(f"Validating {len(edges):,} FAF5 edges")
    
    # Validate schema
    required_cols = ['ORIG_STATE', 'DEST_STATE', 'SHIPMT_VALUE']
    missing_cols = set(required_cols) - set(edges.columns)
    if missing_cols:
        raise ValueError(f"FAF5 edges missing required columns: {missing_cols}")
    
    # Validate data types and ranges
    edges = edges.copy()
    
    # Check state code ranges (1-56 for states, 52 for RoW)
    valid_codes = set(range(1, 57)) | {52}  # States 1-56 + Rest of World 52
    invalid_orig = ~edges['ORIG_STATE'].isin(valid_codes)
    invalid_dest = ~edges['DEST_STATE'].isin(valid_codes)
    
    if invalid_orig.any() or invalid_dest.any():
        log.warning(f"Dropping {(invalid_orig | invalid_dest).sum()} edges with invalid state codes")
        edges = edges[~(invalid_orig | invalid_dest)]
    
    # Check for negative values
    negative_values = edges['SHIPMT_VALUE'] < 0
    if negative_values.any():
        log.warning(f"Dropping {negative_values.sum()} edges with negative values")
        edges = edges[~negative_values]
    
    log.info(f"FAF5 edge validation complete:")
    log.info(f"   Valid edges: {len(edges):,}")
    log.info(f"   Total value: ${edges['SHIPMT_VALUE'].sum():,.0f}")
    
    return edges


def combine_domestic_international_edges(cfs_edges, faf_edges):
    """
    Combine CFS domestic flows with FAF5 international flows.
    
    Args:
        cfs_edges (pd.DataFrame): Domestic state-to-state flows (51×51)
        faf_edges (pd.DataFrame): International flows (51↔1, node 52)
        
    Returns:
        pd.DataFrame: Combined edge list for 52×52 network
        
    Note: Ensures no overlap between domestic and international flows.
          CFS covers states 1-51, FAF5 adds node 52 (Rest of World).
    """
    
    log.info("Combining domestic and international edges")
    
    # Validate no overlap (CFS should not have node 52)
    cfs_has_52 = ((cfs_edges['ORIG_STATE'] == 52) | 
                  (cfs_edges['DEST_STATE'] == 52)).any()
    if cfs_has_52:
        log.warning("Removing node 52 from CFS edges (should be domestic only)")
        cfs_edges = cfs_edges[
            (cfs_edges['ORIG_STATE'] != 52) & 
            (cfs_edges['DEST_STATE'] != 52)
        ]
    
    # Combine edge lists
    combined = pd.concat([cfs_edges, faf_edges], ignore_index=True)
    
    # Re-aggregate in case of any overlaps (shouldn't happen, but defensive)
    combined = (
        combined.groupby(['ORIG_STATE', 'DEST_STATE'], as_index=False)
        ['SHIPMT_VALUE'].sum()
    )
    
    # Ensure consistent dtypes
    combined['ORIG_STATE'] = combined['ORIG_STATE'].astype('int16')
    combined['DEST_STATE'] = combined['DEST_STATE'].astype('int16')
    combined['SHIPMT_VALUE'] = combined['SHIPMT_VALUE'].astype('float64')
    
    domestic_flows = combined[
        (combined['ORIG_STATE'] <= 51) & 
        (combined['DEST_STATE'] <= 51)
    ]
    international_flows = combined[
        (combined['ORIG_STATE'] == 52) | 
        (combined['DEST_STATE'] == 52)
    ]
    
    log.info(f"Edge combination complete:")
    log.info(f"   Total edges: {len(combined):,}")
    log.info(f"   Domestic edges: {len(domestic_flows):,}")
    log.info(f"   International edges: {len(international_flows):,}")
    log.info(f"   Total value: ${combined['SHIPMT_VALUE'].sum():,.0f}")
    log.info(f"   Network size: {combined['ORIG_STATE'].nunique()}×{combined['DEST_STATE'].nunique()}")
    
    return combined


def validate_edge_list(edges, expected_network_size=None):
    """
    Final validation of edge list before network construction.
    
    Args:
        edges (pd.DataFrame): Edge list to validate
        expected_network_size (int, optional): Expected nodes (51 or 52)
        
    Returns:
        dict: Validation report
        
    Raises:
        ValueError: If critical validation checks fail
    """
    
    validation = {
        'total_edges': len(edges),
        'unique_origins': edges['ORIG_STATE'].nunique(),
        'unique_destinations': edges['DEST_STATE'].nunique(),
        'total_value': edges['SHIPMT_VALUE'].sum(),
        'zero_values': (edges['SHIPMT_VALUE'] == 0).sum(),
        'negative_values': (edges['SHIPMT_VALUE'] < 0).sum(),
        'value_range': {
            'min': edges['SHIPMT_VALUE'].min(),
            'max': edges['SHIPMT_VALUE'].max(),
            'median': edges['SHIPMT_VALUE'].median()
        }
    }
    
    # Critical validations
    if validation['negative_values'] > 0:
        raise ValueError(f"Edge list contains {validation['negative_values']} negative values")
    
    if validation['total_edges'] == 0:
        raise ValueError("Edge list is empty")
    
    # Check expected network size (informational, not restrictive)
    max_node = max(edges['ORIG_STATE'].max(), edges['DEST_STATE'].max())
    actual_nodes = max(validation['unique_origins'], validation['unique_destinations'])
    if expected_network_size and actual_nodes != expected_network_size:
        log.warning(f"Network size mismatch: expected {expected_network_size} nodes, found {actual_nodes} (max node ID: {max_node})")
    
    # Log validation summary
    log.info(f"Edge list validation:")
    log.info(f"   Total edges: {validation['total_edges']:,}")
    log.info(f"   Unique nodes: {max(validation['unique_origins'], validation['unique_destinations'])}")
    log.info(f"   Total value: ${validation['total_value']:,.0f}")
    log.info(f"   Zero values: {validation['zero_values']}")
    log.info(f"   Value range: ${validation['value_range']['min']:,.0f} - ${validation['value_range']['max']:,.0f}")
    
    return validation