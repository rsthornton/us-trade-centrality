"""
Edge weight distribution analysis and threshold recommendations.
"""

import logging
import numpy as np

log = logging.getLogger(__name__)


def calculate_distribution_stats(weights, network_label):
    """
    Calculate comprehensive distribution statistics.

    Args:
        weights (np.array): Edge weights
        network_label (str): Network identifier (e.g., "51x51", "52x52")

    Returns:
        dict: Distribution statistics
    """
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    percentile_values = np.percentile(weights, percentiles)

    stats = {
        'network': network_label,
        'edge_count': len(weights),
        'min': weights.min(),
        'max': weights.max(),
        'mean': weights.mean(),
        'median': np.median(weights),
        'std': weights.std(),
        'q1': np.percentile(weights, 25),
        'q2': np.percentile(weights, 50),
        'q3': np.percentile(weights, 75),
    }

    # Add percentiles
    for pct, val in zip(percentiles, percentile_values):
        stats[f'p{pct}'] = val

    # Calculate IQR and outlier bounds
    iqr = stats['q3'] - stats['q1']
    stats['iqr'] = iqr
    stats['outlier_lower'] = stats['q1'] - 1.5 * iqr
    stats['outlier_upper'] = stats['q3'] + 1.5 * iqr

    return stats


def recommend_thresholds(stats_51, stats_52):
    """
    Recommend filtration thresholds based on distribution analysis.

    Args:
        stats_51 (dict): 51×51 statistics
        stats_52 (dict): 52×52 statistics

    Returns:
        dict: Recommended thresholds for both networks
    """
    recommendations = {
        '51x51': {
            'conservative': stats_51['p25'],  # Keep 75% of edges
            'moderate': stats_51['p50'],      # Keep 50% of edges
            'aggressive': stats_51['p75'],    # Keep 25% of edges
            'extreme': stats_51['p90']        # Keep 10% of edges (backbone)
        },
        '52x52': {
            'conservative': stats_52['p25'],
            'moderate': stats_52['p50'],
            'aggressive': stats_52['p75'],
            'extreme': stats_52['p90']
        }
    }

    log.info("\n=== Recommended Filtration Thresholds ===")
    log.info("\n51×51 Domestic Network:")
    for level, value in recommendations['51x51'].items():
        log.info(f"  {level.capitalize():12s}: ${value:>15,.2f}")

    log.info("\n52×52 International Network:")
    for level, value in recommendations['52x52'].items():
        log.info(f"  {level.capitalize():12s}: ${value:>15,.2f}")

    return recommendations
