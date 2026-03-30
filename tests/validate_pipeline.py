#!/usr/bin/env python3
"""
Pipeline Validation Suite
=========================
Comprehensive validation of the complete CFS+FAF5 network analysis pipeline.

Usage:
    python3 validate_pipeline.py                    # Quick validation
    python3 validate_pipeline.py --full            # Full dataset test
    python3 validate_pipeline.py --sample 5000     # Custom sample size
"""

import sys
import logging
import argparse
from pathlib import Path

# Configure clean logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

from cfs_toolkit.core import (
    load_cfs_data,
    load_faf5_international_edges,
    build_trade_network,
    validate_network_structure
)
from cfs_toolkit.core.preprocessor import (
    preprocess_cfs_data,
    aggregate_cfs_to_edges,
    preprocess_faf_edges,
    combine_domestic_international_edges
)


def validate_complete_pipeline(sample_size=1000, include_international=True):
    """
    Single comprehensive test of the entire pipeline.
    
    Args:
        sample_size (int): CFS records to sample (None for full dataset)
        include_international (bool): Test 52×52 international network
        
    Returns:
        dict: Validation results
    """
    
    results = {
        'domestic_network': None,
        'international_network': None,
        'validation_passed': True,
        'errors': []
    }
    
    try:
        print("Pipeline Validation Starting...")
        
        # Load and preprocess CFS domestic data
        print(f"   Loading CFS data ({sample_size:,} sample)...")
        cfs_raw = load_cfs_data('data/cfs_2017_puf.csv', sample_size=sample_size)
        cfs_clean = preprocess_cfs_data(cfs_raw, interstate_only=True)
        cfs_edges = aggregate_cfs_to_edges(cfs_clean)
        
        # Build 51×51 domestic network
        print("   Building 51×51 domestic network...")
        G_domestic = build_trade_network(cfs_edges)
        validation_domestic = validate_network_structure(G_domestic)
        
        if not validation_domestic['is_valid']:
            results['errors'].extend(validation_domestic['issues'])
            results['validation_passed'] = False
        
        results['domestic_network'] = {
            'nodes': len(G_domestic.nodes()),
            'edges': len(G_domestic.edges()),
            'density': G_domestic.graph.get('network_type'),
            'total_value': G_domestic.graph.get('total_trade_value', 0),
            'validation': validation_domestic['is_valid']
        }
        
        # Optionally test international integration
        if include_international:
            print("   Loading FAF5 international data...")
            faf_edges = load_faf5_international_edges(
                'data/FAF5.7.1_State.csv',
                max_chunks=3  # Fast test
            )
            faf_clean = preprocess_faf_edges(faf_edges)
            
            print("   Building 52×52 international network...")
            combined_edges = combine_domestic_international_edges(cfs_edges, faf_clean)
            G_international = build_trade_network(combined_edges)
            validation_international = validate_network_structure(G_international)
            
            if not validation_international['is_valid']:
                results['errors'].extend(validation_international['issues'])
                results['validation_passed'] = False
            
            results['international_network'] = {
                'nodes': len(G_international.nodes()),
                'edges': len(G_international.edges()),
                'density': G_international.graph.get('network_type'),
                'total_value': G_international.graph.get('total_trade_value', 0),
                'validation': validation_international['is_valid'],
                'has_row_node': 52 in G_international.nodes()
            }
        
        return results
        
    except Exception as e:
        results['validation_passed'] = False
        results['errors'].append(f"Pipeline error: {str(e)}")
        return results


def print_validation_report(results):
    """Print formatted validation report"""
    
    print("\n" + "="*60)
    print("PIPELINE VALIDATION REPORT")
    print("="*60)
    
    # Overall status
    status = "PASSED" if results['validation_passed'] else "FAILED"
    print(f"\nOverall Status: {status}")
    
    if results['errors']:
        print(f"\nErrors Found:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Domestic network results
    if results['domestic_network']:
        dom = results['domestic_network']
        print(f"\n51x51 Domestic Network:")
        print(f"   Nodes: {dom['nodes']}")
        print(f"   Edges: {dom['edges']:,}")
        print(f"   Trade Value: ${dom['total_value']:,.0f}")
        print(f"   Validation: {'✓' if dom['validation'] else '✗'}")
    
    # International network results
    if results['international_network']:
        intl = results['international_network']
        print(f"\n52x52 International Network:")
        print(f"   Nodes: {intl['nodes']}")
        print(f"   Edges: {intl['edges']:,}")
        print(f"   Trade Value: ${intl['total_value']:,.0f}")
        print(f"   RoW Node Present: {'✓' if intl['has_row_node'] else '✗'}")
        print(f"   Validation: {'✓' if intl['validation'] else '✗'}")
        
        # Comparative insight
        dom_edges = results['domestic_network']['edges']
        edge_increase = intl['edges'] - dom_edges
        print(f"   Edge Increase: +{edge_increase} ({edge_increase/dom_edges*100:.1f}%)")
    
    print(f"\nPipeline Status: Ready for comparative analysis")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Validate CFS+FAF5 pipeline')
    parser.add_argument('--sample', type=int, default=1000,
                       help='CFS sample size (default: 1000)')
    parser.add_argument('--full', action='store_true',
                       help='Use full CFS dataset (slow)')
    parser.add_argument('--domestic-only', action='store_true',
                       help='Skip international network test')
    
    args = parser.parse_args()
    
    sample_size = None if args.full else args.sample
    include_international = not args.domestic_only
    
    # Run validation
    results = validate_complete_pipeline(
        sample_size=sample_size,
        include_international=include_international
    )
    
    # Print report
    print_validation_report(results)
    
    # Exit with error code if validation failed
    sys.exit(0 if results['validation_passed'] else 1)


if __name__ == "__main__":
    main()