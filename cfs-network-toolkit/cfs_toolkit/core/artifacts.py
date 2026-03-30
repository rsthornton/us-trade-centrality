"""
Save pipeline results to timestamped directories.

Creates result packages with network graphs, centrality CSVs,
configuration snapshots, and optional comparative statistics.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
import networkx as nx


def save_core_artifacts(config, G, centralities_df):
    """
    Save minimal core artifacts (network, centralities, config).

    This is the streamlined output for rapid iteration.
    For full artifacts including summaries and comparisons, use save_pipeline_artifacts().

    Args:
        config: Pipeline configuration dict
        G: NetworkX graph
        centralities_df: DataFrame with centrality scores

    Returns:
        dict: Artifact info with run_dir, files saved
    """
    import pickle
    import yaml

    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    network_type = "52x52_intl" if config['network']['include_international'] else "51x51_domestic"
    run_name = f"{network_type}_{timestamp}"

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    run_dir = results_dir / run_name
    run_dir.mkdir(exist_ok=True)

    artifact_files = []

    # 1. Network graph (.gpickle)
    graph_file = run_dir / f"network_{network_type}.gpickle"
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
    artifact_files.append(graph_file)

    # 2. Centralities (CSV)
    centralities_file = run_dir / f"centralities_{network_type}.csv"
    ranked_df = centralities_df.copy()
    ranked_df['rank_betweenness'] = ranked_df['betweenness'].rank(ascending=False, method='min').astype(int)
    ranked_df['rank_eigenvector'] = ranked_df['eigenvector'].rank(ascending=False, method='min').astype(int)
    ranked_df['rank_out_degree'] = ranked_df['out_degree'].rank(ascending=False, method='min').astype(int)
    ranked_df = ranked_df.sort_values('rank_betweenness')
    ranked_df.to_csv(centralities_file, index=False, float_format='%.6f')
    artifact_files.append(centralities_file)

    # 3. Run configuration (YAML)
    config_file = run_dir / "run_config.yaml"
    with open(config_file, 'w') as f:
        yaml.safe_dump(config, f, sort_keys=False)
    artifact_files.append(config_file)

    # Update results/latest symlink
    latest_link = results_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(run_name)

    total_size_mb = sum(f.stat().st_size for f in artifact_files) / (1024 * 1024)

    return {
        "run_dir": str(run_dir),
        "artifact_count": len(artifact_files),
        "total_size_mb": total_size_mb,
        "network_type": network_type,
        "timestamp": timestamp,
        "files": [str(f) for f in artifact_files]
    }


def save_pipeline_artifacts(config, G, centralities_df, edges, comparative_results=None):
    """
    Create comprehensive artifacts package from pipeline results.

    For minimal output (network + centralities + config only), use save_core_artifacts().

    Returns:
        dict: Artifact information including paths and sizes
    """

    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    network_type = "52x52_intl" if config['network']['include_international'] else "51x51_domestic"
    run_name = f"{network_type}_{timestamp}"

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    run_dir = results_dir / run_name
    run_dir.mkdir(exist_ok=True)

    artifact_files = []

    # 1. Centrality Rankings (CSV)
    centralities_file = run_dir / f"centralities_{network_type}.csv"
    
    # Add rankings to centralities
    ranked_df = centralities_df.copy()
    ranked_df['rank_betweenness'] = ranked_df['betweenness'].rank(ascending=False, method='min').astype(int)
    ranked_df['rank_eigenvector'] = ranked_df['eigenvector'].rank(ascending=False, method='min').astype(int)
    ranked_df['rank_out_degree'] = ranked_df['out_degree'].rank(ascending=False, method='min').astype(int)
    
    # Sort by betweenness ranking for readability
    ranked_df = ranked_df.sort_values('rank_betweenness')
    
    ranked_df.to_csv(centralities_file, index=False, float_format='%.6f')
    artifact_files.append(centralities_file)
    
    # 2. Network Summary Stats (JSON)
    total_value = edges['SHIPMT_VALUE'].sum()
    top_betweenness = ranked_df.nsmallest(3, 'rank_betweenness')['label'].tolist()
    
    network_summary = {
        "pipeline_info": {
            "timestamp": timestamp,
            "network_type": network_type,
            "config_source": config['data']['source'],
            "sample_size": config['data']['sample_size'],
            "records_processed": len(edges)
        },
        "network_stats": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(), 
            "total_value_usd": int(total_value),
            "total_value_formatted": f"${total_value/1e12:.1f}T",
            "is_strongly_connected": nx.is_strongly_connected(G),
            "density": nx.density(G)
        },
        "centrality_leaders": {
            "top_betweenness": top_betweenness,
            "top_eigenvector": ranked_df.nsmallest(3, 'rank_eigenvector')['label'].tolist(),
            "top_out_degree": ranked_df.nsmallest(3, 'rank_out_degree')['label'].tolist()
        },
        "key_insights": {
            "analysis_type": "weighted_centrality",
            "geographic_isolation_effect": "DC/HI/AK high betweenness due to administrative/geographic bottlenecks",
            "methodology_note": "Survey-weighted flows (WGT_FACTOR × SHIPMT_VALUE)"
        }
    }
    
    summary_file = run_dir / f"network_summary_{network_type}.json"
    with open(summary_file, 'w') as f:
        json.dump(network_summary, f, indent=2)
    artifact_files.append(summary_file)
    
    # 3. Top Trade Flows (CSV)
    top_flows = edges.nlargest(100, 'SHIPMT_VALUE').copy()
    
    # Add state labels for readability
    state_labels = dict(zip(centralities_df['state_id'], centralities_df['label']))
    top_flows['ORIG_LABEL'] = top_flows['ORIG_STATE'].map(state_labels).fillna('Unknown')
    top_flows['DEST_LABEL'] = top_flows['DEST_STATE'].map(state_labels).fillna('Unknown')
    
    # Reorder columns for readability
    cols = ['ORIG_STATE', 'ORIG_LABEL', 'DEST_STATE', 'DEST_LABEL', 'SHIPMT_VALUE'] 
    other_cols = [c for c in top_flows.columns if c not in cols]
    top_flows = top_flows[cols + other_cols]
    
    flows_file = run_dir / f"top_flows_{network_type}.csv"
    top_flows.to_csv(flows_file, index=False)
    artifact_files.append(flows_file)
    
    # 4. Critical Bridge Connections (edges involving top betweenness states)
    top_betweenness_ids = ranked_df.nsmallest(5, 'rank_betweenness')['state_id'].tolist()
    
    bridge_edges = edges[
        (edges['ORIG_STATE'].isin(top_betweenness_ids)) | 
        (edges['DEST_STATE'].isin(top_betweenness_ids))
    ].copy()
    
    # Add labels
    bridge_edges['ORIG_LABEL'] = bridge_edges['ORIG_STATE'].map(state_labels).fillna('Unknown')
    bridge_edges['DEST_LABEL'] = bridge_edges['DEST_STATE'].map(state_labels).fillna('Unknown')
    bridge_edges = bridge_edges[cols + [c for c in bridge_edges.columns if c not in cols]]
    
    # Sort by value
    bridge_edges = bridge_edges.sort_values('SHIPMT_VALUE', ascending=False)
    
    bridges_file = run_dir / f"critical_bridges_{network_type}.csv"
    bridge_edges.to_csv(bridges_file, index=False)
    artifact_files.append(bridges_file)
    
    # 5. NetworkX Graph Object (complete network for flexible analysis)
    graph_file = run_dir / f"network_{network_type}.gpickle"
    
    import pickle
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
    
    artifact_files.append(graph_file)
    print(f"   Saved complete network graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
    
    # 6. Run Configuration (exact config used)
    import yaml
    config_file = run_dir / "run_config.yaml"
    with open(config_file, 'w') as dest:
        yaml.safe_dump(config, dest, sort_keys=False)
    artifact_files.append(config_file)
    
    # 7. Key Findings Report (Markdown) - Dynamic based on actual results
    
    # Extract actual top states for dynamic insights
    top_betweenness_states = ranked_df.nsmallest(3, 'rank_betweenness')
    top_eigenvector_states = ranked_df.nsmallest(3, 'rank_eigenvector') 
    top_outdegree_states = ranked_df.nsmallest(3, 'rank_out_degree')
    
    # Generate geographic insight based on actual top betweenness states
    geographic_insight = _generate_geographic_insight(top_betweenness_states['label'].tolist())
    
    # Generate sample size warning if applicable
    sample_warning = ""
    if config['data']['sample_size'] is not None:
        sample_warning = f"""
### Sample Size Impact
**Note**: Results based on {config['data']['sample_size']:,} record sample. 
Small samples can create sampling bias in centrality rankings. 
Full dataset recommended for publication-quality results.
"""
    
    findings_content = f"""# Network Analysis Results: {network_type.upper()}
*Generated: {timestamp}*

## Executive Summary

**Network**: {G.number_of_nodes()} states/jurisdictions, {G.number_of_edges():,} trade routes
**Total Value**: ${total_value/1e12:.1f} trillion in {'interstate' if network_type.startswith('51x51') else 'interstate + international'} commerce
**Analysis**: Weighted centrality using survey-adjusted flows

## Top States by Centrality

### Betweenness Centrality (Bridge States)
{_format_top_states(ranked_df, 'rank_betweenness', 'betweenness')}

### Eigenvector Centrality (Influence States) 
{_format_top_states(ranked_df, 'rank_eigenvector', 'eigenvector')}

### Out-Degree Centrality (Distribution States)
{_format_top_states(ranked_df, 'rank_out_degree', 'out_degree')}

## Key Insights

### Network Bridge Analysis
{geographic_insight}

### Economic Influence Patterns
**Top eigenvector centrality states** ({', '.join(top_eigenvector_states['label'].tolist()[:3])}) represent economic influence hubs - states whose trading partners are themselves highly connected, amplifying their network importance.

### Distribution Power Centers  
**Top out-degree centrality states** ({', '.join(top_outdegree_states['label'].tolist()[:3])}) serve as major distribution hubs, with high-volume outbound trade flows reaching many destinations.

### Methodology Validation
- **Weighted Analysis**: Edge weights represent survey-adjusted trade values (WGT_FACTOR × SHIPMT_VALUE)
- **Network Type**: {network_type} - {'Domestic US interstate flows only' if network_type.startswith('51x51') else 'US interstate + international flows via Rest of World node'}
- **Centrality Measures**: Normalized betweenness, eigenvector (PageRank fallback), weighted out-degree{sample_warning}

### Network Properties
- **Connectivity**: {"Strongly connected" if nx.is_strongly_connected(G) else "Not strongly connected"}
- **Density**: {nx.density(G):.6f} (actual connections / possible connections)
- **Trade Volume**: Top 100 flows represent ${top_flows['SHIPMT_VALUE'].sum()/1e9:.1f}B

## Reproducibility

**Configuration**: `run_config.yaml`
**Environment**: Python NetworkX with survey-weighted centrality
**Validation**: {network_type} network with {len(edges):,} processed records

## Files Generated

{chr(10).join([f"- `{f.name}`: {_get_file_description(f)}" for f in artifact_files])}

---
*Analysis conducted using consolidated thesis pipeline*
*Data source: U.S. Census Bureau CFS 2017 Public Use File*
"""
    
    findings_file = run_dir / f"key_findings_{network_type}.md"
    with open(findings_file, 'w') as f:
        f.write(findings_content)
    artifact_files.append(findings_file)
    
    # 8. Artifacts Manifest (what was generated)
    manifest = {
        "run_info": {
            "timestamp": timestamp,
            "network_type": network_type,
            "pipeline_version": "consolidated_v1.0"
        },
        "files": [
            {
                "name": f.name,
                "description": _get_file_description(f),
                "size_kb": round(f.stat().st_size / 1024, 1)
            }
            for f in artifact_files
        ],
        "totals": {
            "file_count": len(artifact_files),
            "total_size_mb": sum(f.stat().st_size for f in artifact_files) / (1024 * 1024)
        }
    }
    
    manifest_file = run_dir / "artifacts_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    artifact_files.append(manifest_file)
    
    # 9. Legacy comparative analysis - DEPRECATED
    # Note: Comparative analysis now handled in main.py via comparison_utils module
    # This entire section can be removed in future cleanup
    comparative_analysis = None
    # Old code attempted to import deleted comparative_analysis.py module
    # Now comparison happens in main.py Step 8 using comparison_utils

    # 10. Save comparative statistics (if provided)
    has_comparative = False
    if comparative_results is not None:
        try:
            print("Saving comparative statistics...")

            # Save main statistics as JSON
            comp_stats_file = run_dir / "comparative_stats.json"
            stats_to_save = {
                'correlations': comparative_results['correlations'],
                'overlaps': comparative_results['overlaps'],
                'effect_sizes': comparative_results['effect_sizes'],
                'metadata': comparative_results['metadata']
            }

            with open(comp_stats_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2)
            artifact_files.append(comp_stats_file)

            # Save rank changes as CSV
            rank_changes_file = run_dir / "rank_changes.csv"
            comparative_results['rank_changes'].to_csv(rank_changes_file, index=False)
            artifact_files.append(rank_changes_file)

            # Create summary markdown
            comp_summary_file = run_dir / f"comparative_summary_{network_type}.md"
            _create_comparative_summary(comparative_results, comp_summary_file)
            artifact_files.append(comp_summary_file)

            # Save committee-friendly visualizations (if generated)
            if 'committee_visualizations' in comparative_results:
                print("   Copying committee-friendly visualizations...")
                temp_dir = comparative_results['committee_visualizations']['temp_dir']
                committee_files = comparative_results['committee_visualizations']['files']

                # Ensure figures directory exists
                figures_dir = run_dir / 'figures'
                figures_dir.mkdir(exist_ok=True)

                # Copy committee visualization files to figures directory
                import shutil
                for file_name in committee_files:
                    src_file = temp_dir / file_name
                    if src_file.exists():
                        dst_file = figures_dir / file_name
                        shutil.copy2(src_file, dst_file)
                        artifact_files.append(dst_file)

                # Clean up temporary directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass  # Best effort cleanup

                print(f"   ✓ Saved {len(committee_files)} committee-friendly visualizations")

            has_comparative = True
            print("Comparative statistics saved")

        except Exception as e:
            print(f"Error saving comparative results: {e}")

    # Update results/latest symlink
    latest_link = results_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(run_name)
    
    # Calculate final stats
    total_size_mb = sum(f.stat().st_size for f in artifact_files) / (1024 * 1024)
    
    return {
        "run_dir": str(run_dir),
        "artifact_count": len(artifact_files),
        "total_size_mb": total_size_mb,
        "network_type": network_type,
        "timestamp": timestamp,
        "comparative_analysis": comparative_analysis is not None,
        "comparative_stats": has_comparative
    }


def _format_top_states(df, rank_col, value_col, n=5):
    """Format top N states for markdown report."""
    top = df.nsmallest(n, rank_col)
    lines = []
    for _, row in top.iterrows():
        lines.append(f"{int(row[rank_col])}. **{row['label']}**: {row[value_col]:.4f}")
    return "\n".join(lines)


def _generate_geographic_insight(top_betweenness_states):
    """Generate geographic insight based on actual top betweenness centrality states."""
    
    # Geographic isolation patterns - known geographic bottlenecks
    geographic_isolates = {'DC', 'HI', 'AK', 'DE', 'VT', 'NH', 'RI', 'WV', 'MT', 'WY', 'ND', 'SD'}
    
    # Border/coastal states that can act as bridges
    border_coastal = {'WA', 'CA', 'TX', 'FL', 'NY', 'ME', 'LA', 'WV', 'ND', 'MT'}
    
    # Resource/commodity states
    resource_states = {'AK', 'WV', 'WY', 'ND', 'TX', 'LA', 'OK', 'KS'}
    
    # Administrative/financial centers
    admin_centers = {'DC', 'NY', 'IL', 'CA'}
    
    # Analyze the actual top states
    insights = []
    
    for state in top_betweenness_states[:3]:  # Top 3 only
        
        explanations = []
        
        if state in geographic_isolates:
            if state == 'DC':
                explanations.append("administrative hub with specialized federal/regulatory flows")
            elif state in ['HI', 'AK']:
                explanations.append("geographic isolation creates trade bottlenecks")
            elif state in ['WV', 'VT', 'NH']:
                explanations.append("mountainous geography creates natural trade corridors")
            elif state in ['DE', 'RI']:
                explanations.append("small size concentrates flows through limited routes")
            else:
                explanations.append("geographic constraints create bottleneck effects")
        
        if state in resource_states:
            if state in ['AK', 'WY']:
                explanations.append("energy/mineral resource flows")
            elif state == 'WV':
                explanations.append("coal and energy distribution hub")
            elif state in ['ND', 'TX']:
                explanations.append("oil and agricultural commodity flows")
            elif state == 'LA':
                explanations.append("Gulf Coast energy and petrochemical hub")
            else:
                explanations.append("resource-based trade specialization")
        
        if state in border_coastal:
            explanations.append("strategic border/coastal position")
        
        if state in admin_centers:
            explanations.append("major economic/administrative center")
        
        # Default explanation if no specific pattern matches
        if not explanations:
            explanations.append("acts as critical intermediary in interstate trade network")
        
        # Format the explanation
        explanation = " and ".join(explanations)
        insights.append(f"- **{state}**: {explanation.capitalize()}")
    
    # Create the insight section
    result = f"""**Top betweenness centrality states** ({', '.join(top_betweenness_states[:3])}) serve as critical bridges in the trade network:

{chr(10).join(insights)}

These states occupy strategic positions where disruption would significantly impact overall network connectivity."""
    
    return result


def _create_comparison_summary(analysis, output_file):
    """Create markdown summary of the comparison analysis."""
    
    metadata = analysis['analysis_metadata']
    centrality = analysis['centrality_measures']
    
    summary = f"""# US State Centrality Comparison: Domestic vs International Networks

**Research Question**: {metadata['research_question']}

**Methodology**: {metadata['methodology']}

## Executive Summary

Comparing centrality patterns among {metadata['n_states']} US jurisdictions between domestic-only (51×51) and international-inclusive (52×52) networks.

## Key Findings by Centrality Measure

"""
    
    for measure, results in centrality.items():
        summary += f"### {measure.title()} Centrality\n\n"
        summary += f"- **States with ranking changes**: {results['states_changed']}/51\n"
        summary += f"- **Network correlation**: {results['correlation']:.3f}\n\n"
        
        if results['top_gainers']:
            summary += "**Top Gainers** (better ranking with international):\n"
            for gainer in results['top_gainers']:
                summary += f"- {gainer['state']}: #{gainer['old_rank']} → #{gainer['new_rank']} (+{gainer['positions_gained']} positions)\n"
            summary += "\n"
        
        if results['top_losers']:
            summary += "**Top Losers** (worse ranking with international):\n"
            for loser in results['top_losers']:
                summary += f"- {loser['state']}: #{loser['old_rank']} → #{loser['new_rank']} (-{loser['positions_lost']} positions)\n"
            summary += "\n"
        
        summary += "**Top 5 Rankings Comparison**:\n\n"
        summary += "| Rank | Domestic Only | With International |\n"
        summary += "|------|---------------|--------------------|\n"
        
        for i in range(5):
            dom = results['top_5_domestic'][i]
            intl = results['top_5_international'][i]
            summary += f"| {i+1} | {dom['state']} ({dom['value']:.3f}) | {intl['state']} ({intl['value']:.3f}) |\n"
        
        summary += "\n"
    
    summary += """## Research Implications

This corrected analysis addresses the meaningful research question: how does international integration change the economic geography of US interstate commerce? 

By treating Rest of World as network infrastructure rather than a competing jurisdiction, we can identify which US states gain or lose centrality when international flows are considered.

## Methodology Notes

- RoW (Rest of World) excluded from centrality rankings 
- Analysis focuses on relative position changes among US jurisdictions
- Both networks use identical centrality calculation methods
- Survey-weighted trade flows (WGT_FACTOR × SHIPMT_VALUE)

---
*Generated by consolidated thesis pipeline comparative analysis module*
"""
    
    with open(output_file, 'w') as f:
        f.write(summary)


def _create_comparative_summary(comparative_results, output_file):
    """Create markdown summary for comparative statistics."""

    metadata = comparative_results['metadata']
    correlations = comparative_results['correlations']
    effect_sizes = comparative_results['effect_sizes']
    overlaps = comparative_results['overlaps']

    summary = f"""# Comparative Network Analysis: {metadata['current_type']} vs {metadata['counterpart_type']}

## Statistical Overview

**Analysis Type**: Formal comparative statistics between {metadata['current_type']} and {metadata['counterpart_type']} networks
**States Compared**: {metadata['n_states_compared']} US jurisdictions
**Measures**: {', '.join(metadata['measures_compared'])}
**Counterpart Data**: `{Path(metadata['counterpart_file']).name}`

---

## Rank Correlations

**Interpretation**: How similar are the rankings between networks? (1.0 = identical, 0.0 = no correlation)

"""

    for measure in metadata['measures_compared']:
        corr = correlations[measure]
        summary += f"### {measure.title()} Centrality\n"
        summary += f"- **Spearman ρ**: {corr['spearman']:.3f} (p={corr['spearman_p']:.3f})\n"
        summary += f"- **Kendall τ**: {corr['kendall']:.3f} (p={corr['kendall_p']:.3f})\n"
        summary += f"- **Sample size**: {corr['n']} states\n\n"

    summary += "---\n\n## Effect Sizes\n\n**Interpretation**: How much do rankings actually change?\n\n"

    for measure in metadata['measures_compared']:
        es = effect_sizes[measure]
        summary += f"### {measure.title()} Centrality\n"
        summary += f"- **States with rank changes**: {es['states_changed']}/{es['total_states']}\n"
        summary += f"- **Mean absolute change**: {es['mean_abs_change']:.1f} positions\n"
        summary += f"- **Median absolute change**: {es['median_abs_change']:.1f} positions\n"
        summary += f"- **Maximum change**: {es['max_abs_change']} positions\n"
        summary += f"- **95th percentile**: {es['pct_95_abs_change']:.1f} positions\n\n"

    summary += "---\n\n## Top-K Overlap Analysis\n\n**Interpretation**: How consistent are the top performers?\n\n"

    for k in [5, 10, 20]:
        if k in overlaps[metadata['measures_compared'][0]]:  # Check if this k exists
            summary += f"### Top {k} States\n\n"
            summary += "| Measure | Overlap Count | Overlap % | Jaccard Index |\n"
            summary += "|---------|---------------|-----------|---------------|\n"

            for measure in metadata['measures_compared']:
                if k in overlaps[measure]:
                    ov = overlaps[measure][k]
                    summary += f"| {measure.title()} | {ov['overlap_count']}/{k} | {ov['overlap_percentage']:.1%} | {ov['jaccard']:.3f} |\n"
            summary += "\n"

    summary += """---

## Methodology Notes

- **Alignment**: RoW node excluded from comparative analysis
- **Ranking**: 1 = highest centrality (best position)
- **Delta Rank**: Positive = worse ranking in 52×52 network
- **Statistical Tests**: Spearman (monotonic) and Kendall (concordance) correlations
- **Effect Sizes**: Focus on practical significance, not just statistical significance

---

*Generated by cfs-network-toolkit comparative statistics module*
"""

    with open(output_file, 'w') as f:
        f.write(summary)


def _get_file_description(file_path):
    """Get description for each file type."""
    name = file_path.name.lower()

    if "centralities" in name:
        return "State centrality rankings with all three measures"
    elif "network_summary" in name:
        return "Network statistics and key insights (JSON)"
    elif "top_flows" in name:
        return "100 highest-value interstate trade routes" 
    elif "critical_bridges" in name:
        return "Trade routes involving top betweenness states"
    elif "run_config" in name:
        return "Exact pipeline configuration used"
    elif "key_findings" in name:
        return "Executive summary and analytical insights"
    elif "us_state_comparison" in name and name.endswith('.json'):
        return "US state centrality comparison analysis (domestic vs international)"
    elif "us_state_comparison_summary" in name:
        return "Human-readable comparative analysis summary"
    elif "artifacts_manifest" in name:
        return "Complete file manifest with metadata"
    else:
        return "Pipeline artifact"