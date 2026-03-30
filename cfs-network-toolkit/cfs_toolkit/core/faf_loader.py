"""
Stream and aggregate FAF5 international flows into state-level edge lists.

Reads large FAF5 files in chunks, aggregates by state pairs, and converts
from millions USD to dollars. Supports optional mode/commodity filtering.
"""

import pandas as pd
import logging
from pathlib import Path

# Configuration constants
ROW_CODE = 52  # Rest of World node ID
FOREIGN_CODES = set(str(x) for x in range(801, 809))  # Valid foreign region codes

# Setup logging
log = logging.getLogger(__name__)


def load_faf5_international_edges(
    filepath: str,
    year: int = 2017,
    mode_filter: set[int] | None = None,     # e.g., {1,2,3,4,5} for specific modes
    sctg2_filter: set[str] | None = None,    # e.g., {'15','16','17','18','19'} for energy
    chunksize: int = 250_000,
    max_chunks: int | None = None,           # Optional limit for testing
    progress: bool = False,                  # Show progress bar for long runs
) -> pd.DataFrame:
    """
    Load and aggregate FAF5 international trade flows into state-level edges.
    
    Streams FAF5 data in chunks, aggregates by state pairs, and returns compact
    edge list suitable for network construction.
    
    Args:
        filepath (str): Path to FAF5.7.1_State.csv
        year (int): Year to extract (default: 2017)
        mode_filter (set[int], optional): Filter by transport modes
        sctg2_filter (set[str], optional): Filter by commodity codes
        chunksize (int): Chunk size for streaming (default: 250k)
        max_chunks (int, optional): Limit number of chunks for testing
        progress (bool): Show progress bar with tqdm
        
    Returns:
        pd.DataFrame: Edge list with columns ['ORIG_STATE','DEST_STATE','SHIPMT_VALUE']:
            - ORIG_STATE (int16): Origin state code (52 = Rest of World)
            - DEST_STATE (int16): Destination state code (52 = Rest of World) 
            - SHIPMT_VALUE (float64): Flow value in USD (individual dollars, not millions)
            
    Note: 
        - Imports: Foreign regions (801-808) → State (origin=52, dest=state)
        - Exports: State → Foreign regions (801-808) (origin=state, dest=52)
        - Values converted from millions USD to individual USD
        - Only valid foreign regions (801-808) and state codes (1-56) processed
    """
    
    # Validate file exists
    if not Path(filepath).exists():
        raise FileNotFoundError(f"FAF5 data file not found: {filepath}")
    
    # Normalize filters for robustness
    if sctg2_filter is not None:
        sctg2_filter = {str(s).zfill(2) for s in sctg2_filter}
    if mode_filter is not None:
        mode_filter = {int(m) for m in mode_filter}
    
    log.info(f"Loading FAF5 international flows from: {filepath}")
    log.info(f"Target year: {year}, Chunk size: {chunksize:,}")
    if max_chunks:
        log.info(f"Limited to {max_chunks} chunks for testing")
    
    # Column configuration
    value_col = f"value_{year}"
    usecols = [
        "fr_orig", "dms_origst", "dms_destst", "fr_dest",
        "sctg2", "trade_type", "dms_mode", value_col
    ]
    
    # Handle string fields that may have blanks/leading zeros
    dtypes = {
        "fr_orig": "string",
        "fr_dest": "string", 
        "dms_origst": "string",
        "dms_destst": "string",
        "sctg2": "string",
        "trade_type": "int8",
        "dms_mode": "int8",
        value_col: "float32",
    }
    
    def _parse_state_codes(state_series):
        """Parse state codes, handling leading zeros and invalid entries."""
        parsed = pd.to_numeric(state_series.str.strip(), errors='coerce')
        # Filter to valid state codes (1-56, includes DC=11)
        valid_mask = (parsed >= 1) & (parsed <= 56) & parsed.notna()
        return parsed.where(valid_mask).astype('Int16')
    
    # Vectorized aggregation using pandas Series
    agg = None  # Will be pandas Series indexed by (ORIG_STATE, DEST_STATE)
    total_chunks = 0
    total_import_rows = 0
    total_export_rows = 0
    
    try:
        # Stream through file in chunks
        iterator = pd.read_csv(
            filepath,
            usecols=usecols,
            dtype=dtypes,
            chunksize=chunksize,
            low_memory=False,
        )
        
        # Add progress bar if requested
        if progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterator, desc="FAF5 chunks", unit="chunk")
            except ImportError:
                log.warning("tqdm not available, skipping progress bar")
        
        for chunk in iterator:
            total_chunks += 1
            
            # Limit chunks for testing if specified
            if max_chunks and total_chunks > max_chunks:
                log.info(f"Stopping at {total_chunks-1} chunks (max_chunks={max_chunks})")
                break
            
            # Apply optional filters
            if mode_filter is not None:
                chunk = chunk[chunk["dms_mode"].isin(mode_filter)]
            if sctg2_filter is not None:
                chunk = chunk[chunk["sctg2"].isin(sctg2_filter)]
            
            # Process IMPORTS (trade_type == 2)
            # Only valid foreign origins and destination states
            imports = chunk[
                (chunk["trade_type"] == 2) & 
                (chunk["fr_orig"].isin(FOREIGN_CODES))
            ].copy()
            
            if not imports.empty:
                imports["DEST_STATE"] = _parse_state_codes(imports["dms_destst"])
                imports = imports[imports["DEST_STATE"].notna()]
                imports["ORIG_STATE"] = ROW_CODE
                imports["SHIPMT_VALUE"] = imports[value_col].astype("float64") * 1_000_000
                
                # Aggregate imports by state pairs
                imp_edges = imports.groupby(
                    ["ORIG_STATE", "DEST_STATE"], sort=False
                )["SHIPMT_VALUE"].sum()
                
                total_import_rows += len(imports)
            else:
                # Create empty Series with correct MultiIndex
                empty_index = pd.MultiIndex.from_tuples([], names=['ORIG_STATE', 'DEST_STATE'])
                imp_edges = pd.Series([], dtype='float64', name='SHIPMT_VALUE', index=empty_index)
            
            # Process EXPORTS (trade_type == 3)  
            # Only valid foreign destinations and origin states
            exports = chunk[
                (chunk["trade_type"] == 3) & 
                (chunk["fr_dest"].isin(FOREIGN_CODES))
            ].copy()
            
            if not exports.empty:
                exports["ORIG_STATE"] = _parse_state_codes(exports["dms_origst"])
                exports = exports[exports["ORIG_STATE"].notna()]
                exports["DEST_STATE"] = ROW_CODE
                exports["SHIPMT_VALUE"] = exports[value_col].astype("float64") * 1_000_000
                
                # Aggregate exports by state pairs
                exp_edges = exports.groupby(
                    ["ORIG_STATE", "DEST_STATE"], sort=False
                )["SHIPMT_VALUE"].sum()
                
                total_export_rows += len(exports)
            else:
                # Create empty Series with correct MultiIndex
                empty_index = pd.MultiIndex.from_tuples([], names=['ORIG_STATE', 'DEST_STATE'])
                exp_edges = pd.Series([], dtype='float64', name='SHIPMT_VALUE', index=empty_index)
            
            # Combine import and export edges for this chunk
            chunk_edges = imp_edges.add(exp_edges, fill_value=0.0)
            
            # Add to main aggregator using vectorized pandas operations
            if agg is None:
                agg = chunk_edges
            else:
                agg = agg.add(chunk_edges, fill_value=0.0)
    
    except Exception as e:
        log.error(f"Error processing FAF5 data: {e}")
        raise
    
    # Convert aggregated Series to DataFrame
    if agg is None or agg.empty:
        log.info("No international trade flows found matching criteria")
        return pd.DataFrame(columns=["ORIG_STATE", "DEST_STATE", "SHIPMT_VALUE"])
    
    # Convert Series with MultiIndex to DataFrame
    result_df = agg.rename("SHIPMT_VALUE").reset_index()
    
    # Optimize data types for output
    result_df["ORIG_STATE"] = result_df["ORIG_STATE"].astype("int16")
    result_df["DEST_STATE"] = result_df["DEST_STATE"].astype("int16") 
    result_df["SHIPMT_VALUE"] = result_df["SHIPMT_VALUE"].astype("float64")
    
    # Log summary statistics
    total_value = result_df["SHIPMT_VALUE"].sum()
    import_flows = result_df[result_df["ORIG_STATE"] == ROW_CODE]
    export_flows = result_df[result_df["DEST_STATE"] == ROW_CODE]
    
    log.info("FAF5 Processing Summary:")
    log.info(f"   Chunks processed: {total_chunks}")
    log.info(f"   Import records: {total_import_rows:,}")
    log.info(f"   Export records: {total_export_rows:,}")
    log.info(f"   Unique import edges: {len(import_flows)} (RoW → States)")
    log.info(f"   Unique export edges: {len(export_flows)} (States → RoW)")
    log.info(f"   Total trade value: ${total_value:,.0f}")
    log.info(f"   Output size: {len(result_df)} edges")
    log.info(f"   Memory usage: {result_df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    return result_df


def validate_faf5_edges(edges_df):
    """
    Validate FAF5 edge list for integration compatibility.
    
    Args:
        edges_df (pd.DataFrame): Output from load_faf5_international_edges()
        
    Returns:
        dict: Validation report
    """
    
    validation = {
        'total_edges': len(edges_df),
        'total_value': edges_df['SHIPMT_VALUE'].sum(),
        'import_edges': len(edges_df[edges_df['ORIG_STATE'] == ROW_CODE]),
        'export_edges': len(edges_df[edges_df['DEST_STATE'] == ROW_CODE]),
        'state_coverage': {
            'import_states': sorted(edges_df[edges_df['ORIG_STATE'] == ROW_CODE]['DEST_STATE'].unique()),
            'export_states': sorted(edges_df[edges_df['DEST_STATE'] == ROW_CODE]['ORIG_STATE'].unique()),
        },
        'value_range': {
            'min': edges_df['SHIPMT_VALUE'].min(),
            'max': edges_df['SHIPMT_VALUE'].max(),
            'median': edges_df['SHIPMT_VALUE'].median(),
        }
    }
    
    print(f"\nFAF5 Edge Validation:")
    print(f"   Total edges: {validation['total_edges']}")
    print(f"   Import edges (RoW→State): {validation['import_edges']}")
    print(f"   Export edges (State→RoW): {validation['export_edges']}")
    print(f"   States with imports: {len(validation['state_coverage']['import_states'])}")
    print(f"   States with exports: {len(validation['state_coverage']['export_states'])}")
    print(f"   Value range: ${validation['value_range']['min']:,.0f} - ${validation['value_range']['max']:,.0f}")
    
    return validation