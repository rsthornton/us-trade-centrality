"""
Comparison Utilities
====================
Helper functions for loading and preparing comparison data between
51×51 (domestic) and 52×52 (international) network results.

Used to enable creative visualizations that require comparison data.
"""

import logging

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from scipy.stats import spearmanr, kendalltau

log = logging.getLogger(__name__)


def load_comparison_data_from_results(
    domestic_dir: Path,
    international_dir: Path
) -> Optional[Dict]:
    """
    Load comparison data from pipeline results directories.
    
    Args:
        domestic_dir: Path to 51×51 domestic results
        international_dir: Path to 52×52 international results
        
    Returns:
        Dictionary with comparison datasets or None if loading fails
    """
    
    try:
        comparison_data = {}
        
        # Load centrality results from the actual file format
        file_51 = domestic_dir / "centralities_51x51_domestic.csv"
        file_52 = international_dir / "centralities_52x52_intl.csv"
        
        if not file_51.exists() or not file_52.exists():
            log.warning(f"Centrality files not found: 51x51={file_51.exists()}, 52x52={file_52.exists()}")
            return None
        
        df_51_full = pd.read_csv(file_51)
        df_52_full = pd.read_csv(file_52)
        
        log.info(f"Loaded centrality data: 51x51 ({len(df_51_full)} states), 52x52 ({len(df_52_full)} states)")
        
        # Extract each measure
        for measure in ['betweenness', 'eigenvector', 'out_degree']:
            if measure in df_51_full.columns and measure in df_52_full.columns:
                # 51×51 data
                df_51 = df_51_full[['label', measure]].copy()
                df_51 = df_51.rename(columns={'label': 'state', measure: 'value'})
                df_51 = df_51.sort_values('value', ascending=False).reset_index(drop=True)
                df_51['rank'] = range(1, len(df_51) + 1)
                comparison_data[f'{measure}_51'] = df_51
                
                # 52×52 data (filter out RoW if present)
                df_52 = df_52_full[['label', measure]].copy()
                df_52 = df_52[df_52['label'] != 'RoW']  # Remove Rest of World
                df_52 = df_52.rename(columns={'label': 'state', measure: 'value'})
                df_52 = df_52.sort_values('value', ascending=False).reset_index(drop=True)
                df_52['rank'] = range(1, len(df_52) + 1)
                comparison_data[f'{measure}_52'] = df_52
        
        log.info(f"Prepared {len(comparison_data)} comparison datasets")
        return comparison_data
        
    except Exception as e:
        log.warning(f"Error loading comparison data: {e}")
        return None


def find_recent_results(
    results_dir: Path,
    domestic_pattern: str = "51x51_domestic_*",
    international_pattern: str = "52x52_intl_*"
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Find most recent domestic and international result directories.
    
    Args:
        results_dir: Results directory to search
        domestic_pattern: Glob pattern for domestic results
        international_pattern: Glob pattern for international results
        
    Returns:
        Tuple of (domestic_dir, international_dir) or (None, None) if not found
    """
    
    # Look for recent 51×51 and 52×52 runs
    domestic_dirs = list(results_dir.glob(domestic_pattern))
    international_dirs = list(results_dir.glob(international_pattern))
    
    if not domestic_dirs or not international_dirs:
        return None, None
    
    # Use most recent runs (sorted by name which includes timestamp)
    domestic_dir = max(domestic_dirs, key=lambda x: x.name)
    international_dir = max(international_dirs, key=lambda x: x.name)
    
    return domestic_dir, international_dir


def prepare_comparison_data_for_pipeline(results_dir: Path) -> Optional[Dict]:
    """
    Auto-detect and prepare comparison data for pipeline integration.
    
    Args:
        results_dir: Path to results directory
        
    Returns:
        Comparison data dictionary or None if unavailable
    """
    
    log.info("Searching for comparison data from recent pipeline runs")
    
    # Find recent results
    domestic_dir, international_dir = find_recent_results(results_dir)
    
    if domestic_dir is None or international_dir is None:
        log.warning(f"Could not find both result sets: domestic={'found' if domestic_dir else 'missing'}, international={'found' if international_dir else 'missing'}")
        return None
    
    log.info(f"Using results: 51x51={domestic_dir.name}, 52x52={international_dir.name}")
    
    # Load comparison data
    return load_comparison_data_from_results(domestic_dir, international_dir)


# =============================================================================
# Statistical Comparison Functions
# =============================================================================

def align_measures(df51: pd.DataFrame, df52: pd.DataFrame,
                  measures: List[str], key_col: str = "label") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align dataframes for comparative analysis, excluding RoW node.

    Args:
        df51: 51×51 centrality results
        df52: 52×52 centrality results
        measures: List of centrality measures to align
        key_col: Column name for joining

    Returns:
        Tuple of aligned dataframes with consistent nodes and measures
    """
    # Exclude RoW node from 52x52 results for fair comparison
    df52_states = df52[df52[key_col] != "RoW"].copy()

    # Ensure both have required columns
    df51_aligned = df51[[key_col] + measures].copy()
    df52_aligned = df52_states[[key_col] + measures].copy()

    # Inner join to ensure consistent nodes
    merged = df51_aligned.merge(df52_aligned, on=key_col, suffixes=("_51", "_52"))

    # Split back into aligned dataframes
    df51_cols = [key_col] + [f"{m}_51" for m in measures]
    df52_cols = [key_col] + [f"{m}_52" for m in measures]

    df51_result = merged[df51_cols].copy()
    df52_result = merged[df52_cols].copy()

    # Rename columns back to original names
    df51_result.columns = [key_col] + measures
    df52_result.columns = [key_col] + measures

    return df51_result, df52_result


def rank_columns(df: pd.DataFrame, measures: List[str]) -> pd.DataFrame:
    """
    Add rank columns for centrality measures (1 = best).

    Args:
        df: DataFrame with centrality measures
        measures: List of measure columns to rank

    Returns:
        DataFrame with added rank_<measure> columns
    """
    df_ranked = df.copy()

    for measure in measures:
        df_ranked[f"rank_{measure}"] = df[measure].rank(ascending=False, method="min")

    return df_ranked


def compute_rank_correlations(df51: pd.DataFrame, df52: pd.DataFrame,
                            measures: List[str], key: str = "label") -> Dict:
    """
    Compute rank correlations between 51×51 and 52×52 centrality measures.

    Args:
        df51: 51×51 centrality results
        df52: 52×52 centrality results
        measures: List of centrality measures
        key: Column name for joining

    Returns:
        Dictionary with correlation statistics per measure
    """
    df1 = df51[[key] + measures].copy()
    df2 = df52[[key] + measures].copy()
    df = df1.merge(df2, on=key, suffixes=("_51", "_52"))

    correlations = {}

    for measure in measures:
        col_51 = f"{measure}_51"
        col_52 = f"{measure}_52"

        # Compute correlations
        r_s, p_s = spearmanr(df[col_51], df[col_52])
        t_k, p_k = kendalltau(df[col_51], df[col_52])

        correlations[measure] = {
            "spearman": float(r_s),
            "spearman_p": float(p_s),
            "kendall": float(t_k),
            "kendall_p": float(p_k),
            "n": int(len(df))
        }

    return correlations


def compute_rank_changes(df51: pd.DataFrame, df52: pd.DataFrame,
                        measures: List[str], key: str = "label") -> pd.DataFrame:
    """
    Compute per-state rank changes between 51×51 and 52×52 networks.

    Args:
        df51: 51×51 centrality results
        df52: 52×52 centrality results
        measures: List of centrality measures
        key: Column name for joining

    Returns:
        Long-form DataFrame with per-state rank changes
    """
    # Add ranks to both dataframes
    r1 = rank_columns(df51[[key] + measures], measures)
    r2 = rank_columns(df52[[key] + measures], measures)

    # Merge on ranks
    rank_cols_51 = [f"rank_{m}" for m in measures]
    rank_cols_52 = [f"rank_{m}" for m in measures]

    merged = r1[[key] + rank_cols_51].merge(
        r2[[key] + rank_cols_52], on=key, suffixes=("_51", "_52")
    )

    # Convert to long format with rank changes
    rows = []
    for _, row in merged.iterrows():
        for measure in measures:
            rank_51 = int(row[f"rank_{measure}_51"])
            rank_52 = int(row[f"rank_{measure}_52"])
            delta_rank = rank_52 - rank_51  # positive = worse rank in 52x52

            rows.append({
                key: row[key],
                "measure": measure,
                "rank_51": rank_51,
                "rank_52": rank_52,
                "delta_rank": delta_rank,
                "abs_delta_rank": abs(delta_rank)
            })

    return pd.DataFrame(rows)


def compute_topk_overlap(df51: pd.DataFrame, df52: pd.DataFrame,
                        measures: List[str], ks: List[int], key: str = "label") -> Dict:
    """
    Compute top-k overlap between 51×51 and 52×52 rankings.

    Args:
        df51: 51×51 centrality results
        df52: 52×52 centrality results
        measures: List of centrality measures
        ks: List of k values for top-k analysis
        key: Column name for joining

    Returns:
        Dictionary with overlap statistics per measure and k
    """
    # Add ranks
    r1 = rank_columns(df51[[key] + measures], measures)
    r2 = rank_columns(df52[[key] + measures], measures)

    overlaps = {}

    for measure in measures:
        overlaps[measure] = {}

        for k in ks:
            # Get top-k states for each network
            top_k_51 = set(r1.nsmallest(k, f"rank_{measure}")[key])
            top_k_52 = set(r2.nsmallest(k, f"rank_{measure}")[key])

            # Compute overlap metrics
            intersection = top_k_51.intersection(top_k_52)
            union = top_k_51.union(top_k_52)

            jaccard = len(intersection) / len(union) if union else 0
            overlap_count = len(intersection)
            overlap_pct = overlap_count / k if k > 0 else 0

            overlaps[measure][k] = {
                "jaccard": float(jaccard),
                "overlap_count": int(overlap_count),
                "overlap_percentage": float(overlap_pct),
                "k": int(k)
            }

    return overlaps


def summarize_effect_sizes(rank_changes: pd.DataFrame) -> Dict:
    """
    Summarize effect sizes from rank changes.

    Args:
        rank_changes: DataFrame from compute_rank_changes()

    Returns:
        Dictionary with summary statistics per measure
    """
    summary = {}

    for measure in rank_changes['measure'].unique():
        measure_data = rank_changes[rank_changes['measure'] == measure]
        abs_deltas = measure_data['abs_delta_rank']
        deltas = measure_data['delta_rank']

        summary[measure] = {
            "mean_abs_change": float(abs_deltas.mean()),
            "median_abs_change": float(abs_deltas.median()),
            "max_abs_change": int(abs_deltas.max()),
            "std_abs_change": float(abs_deltas.std()),
            "pct_95_abs_change": float(abs_deltas.quantile(0.95)),
            "mean_change": float(deltas.mean()),
            "states_changed": int((abs_deltas > 0).sum()),
            "total_states": int(len(measure_data))
        }

    return summary