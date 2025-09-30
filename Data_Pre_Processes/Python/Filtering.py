# Deduplicate rows per (Buyer Company Name, Part Number, Condition Code) within ~30 days
# Keep at least one row (the earliest chronologically) per 30-day cluster.
import pandas as pd
from IPython.display import display


def day2_duplicates(df, filename_duplicates=None):
    """
    Deduplicate rows within 2 days. If filename_duplicates is provided and file exists, 
    read the pre-processed file instead of processing.
    """
    
    # Original deduplication logic
    key_cols = ['Buyer Company Name', 'Part Number', 'Condition Code']
    for c in key_cols + ['Received At (UTC)']:
        if c not in df.columns:
            raise KeyError(f"Missing expected column: {c}")

    # Normalize and parse Received At into a datetime column
    df['_recv_dt'] = pd.to_datetime(df['Received At (UTC)'], errors='coerce', utc=True)
    # convert to naive UTC timestamps for easier arithmetic
    if df['_recv_dt'].dt.tz is not None:
        df['_recv_dt'] = df['_recv_dt'].dt.tz_convert('UTC').dt.tz_localize(None)

    # Prepare container for kept indices
    kept_indices = []

    # Iterate groups defined by keys
    grouped = df.groupby(key_cols, sort=False)
    for name, group in grouped:
        # Sort by Received datetime ascending
        g = group.sort_values('_recv_dt')
        last_kept_dt = None
        last_kept_idx = None
        for idx, row in g.iterrows():
            dt = row['_recv_dt']
            if pd.isna(dt):
                # If no date, keep only the first encountered (to ensure at least one copy kept)
                if last_kept_dt is None:
                    kept_indices.append(idx)
                    last_kept_dt = pd.NaT
                    last_kept_idx = idx
                else:
                    # skip additional undated rows
                    continue
            else:
                if last_kept_dt is None or pd.isna(last_kept_dt):
                    # Keep the first dated row
                    kept_indices.append(idx)
                    last_kept_dt = dt
                    last_kept_idx = idx
                else:
                    # If this row is within 2 days of last_kept_dt, consider it duplicate and skip
                    if (dt - last_kept_dt) <= pd.Timedelta(days=2): ################################# CHANGE FOR DAYS
                        # duplicate within 2 days -> skip
                        continue
                    else:
                        # far enough, keep and update last_kept_dt
                        kept_indices.append(idx)
                        last_kept_dt = dt
                        last_kept_idx = idx

    # Build deduped and duplicates DataFrames
    keep_mask = df.index.isin(kept_indices)
    Checked_DF_deduped = df.loc[keep_mask].copy().reset_index(drop=True)
    duplicates_found = df.loc[~keep_mask].copy().reset_index(drop=True)

    # Drop helper column before exposing results
    for d in (Checked_DF_deduped, duplicates_found):
        if '_recv_dt' in d.columns:
            d.drop(columns=['_recv_dt'], inplace=True, errors='ignore')

    # Summary
    total = len(df)
    kept = len(Checked_DF_deduped)
    removed = len(duplicates_found)
    print(f"Total rows: {total:,}")
    print(f"Kept rows after 2-day deduplication: {kept:,}")
    print(f"Rows marked as duplicates (removed): {removed:,}")

    if removed:
        print('\nSample duplicates (first 10):')
        # display(duplicates_found.head(10))

    print('\nSample kept rows (first 10):')
    # display(Checked_DF_deduped.head(10))

    # Expose variables for later cells
    # - Checked_DF_deduped: deduplicated DataFrame
    # - duplicates_found: rows that were considered duplicates within 2 days

    print('\nDeduplication complete. Use `Checked_DF_deduped` for exports or further analysis.')
    
    return Checked_DF_deduped

def quantity_outliers_improved(df):
    """
    Improved outlier detection that considers part-specific patterns
    and doesn't penalize legitimate high-volume parts.
    Uses progressive, data-driven thresholds instead of hardcoded limits.
    """
    import pandas as pd
    import numpy as np

    
    print("Starting improved quantity outlier detection...")
    original_count = len(df)
    
    if original_count == 0:
        print("Empty dataframe provided")
        return df
    
    # Group by part number for per-part analysis
    grouped = df.groupby('Part Number')
    
    outliers_to_remove = []
    analysis_summary = []
    
    # First pass: analyze the overall distribution to understand data characteristics
    qty_col = 'Quantity' if 'Quantity' in df.columns else 'Qty'
    all_quantities = pd.to_numeric(df[qty_col], errors='coerce').dropna()
    
    if len(all_quantities) == 0:
        print("No valid numeric quantities found")
        return df
    
    # Calculate global statistics for context
    global_median = all_quantities.median()
    global_95th = all_quantities.quantile(0.95)
    global_99th = all_quantities.quantile(0.99)
    global_999th = all_quantities.quantile(0.999)
    
    print(f"Global quantity statistics:")
    print(f"  Median: {global_median:.0f}")
    print(f"  95th percentile: {global_95th:.0f}")
    print(f"  99th percentile: {global_99th:.0f}")
    print(f"  99.9th percentile: {global_999th:.0f}")
    
    for part_num, group in grouped:
        quantities = pd.to_numeric(group[qty_col], errors='coerce').dropna().values
        
        if len(quantities) < 2:
            # Too few data points for meaningful outlier detection
            continue
            
        # Calculate statistics
        median_qty = np.median(quantities)
        q1 = np.percentile(quantities, 25)
        q3 = np.percentile(quantities, 75)
        iqr = q3 - q1
        max_qty = np.max(quantities)
        min_qty = np.min(quantities)
        
        # Progressive threshold calculation based on data characteristics
        # Determine part category and set appropriate thresholds
        if median_qty <= 10:
            # LOW VOLUME parts - be conservative but catch obvious errors
            if iqr == 0:  # All values the same
                # For consistent low-volume parts, allow moderate variation
                upper_threshold = max(median_qty * 20, 100)
            else:
                # Use statistical approach with wider tolerance
                upper_threshold = q3 + 5 * iqr
                # But ensure it's at least reasonable for low-volume parts
                upper_threshold = max(upper_threshold, 50)
            
            # Additional check: if max is extreme compared to global context
            if max_qty > global_99th * 2:
                upper_threshold = min(upper_threshold, global_99th)
            
        elif median_qty <= 100:
            # MEDIUM VOLUME parts - moderate outlier detection
            if iqr == 0:
                upper_threshold = median_qty * 10  # Allow 10x variation for consistent parts
            else:
                upper_threshold = q3 + 4 * iqr
                # Ensure reasonable minimum threshold
                upper_threshold = max(upper_threshold, median_qty * 3)
            
            # Context check against global distribution
            if max_qty > global_999th:
                upper_threshold = min(upper_threshold, global_999th)
            
        else:
            # HIGH VOLUME parts - allow much higher variation
            if iqr == 0:
                # For consistent high-volume parts, be very conservative
                upper_threshold = median_qty * 3
            else:
                # Allow significant variation for high-volume parts
                upper_threshold = q3 + 6 * iqr
                # But ensure it's at least double the median
                upper_threshold = max(upper_threshold, median_qty * 2)
            
            # For high-volume parts, be more lenient with global context
            if max_qty > global_999th * 3:
                upper_threshold = min(upper_threshold, global_999th * 2)
        
        # Additional legitimacy checks
        
        # 1. If this is a consistently high-volume part (all quantities > 1000), be very conservative
        if min_qty > 1000 and max_qty <= median_qty * 2:
            continue  # Skip outlier detection for consistent high-volume parts
        
        # 2. If the part has reasonable variation (max within 50x of median), be conservative
        if max_qty <= median_qty * 50 and median_qty > 0:
            # This suggests legitimate business variation, not data entry errors
            continue
        
        # 3. Progressive detection: only flag truly extreme outliers
        # Look for quantities that are drastically different from the pattern
        if len(quantities) >= 3:
            # Sort quantities to understand the distribution
            sorted_qtys = np.sort(quantities)
            
            # Check if there's a clear jump in the highest values
            if len(sorted_qtys) >= 3:
                # Look at the gap between the highest value and second-highest
                highest = sorted_qtys[-1]
                second_highest = sorted_qtys[-2]
                
                # If the highest is more than 10x the second highest, it's likely an error
                if highest > second_highest * 10 and second_highest > 0:
                    upper_threshold = min(upper_threshold, second_highest * 5)
        
        # Find outliers for this part - ONLY remove quantities that are too HIGH
        outlier_mask = group[qty_col] > upper_threshold
        part_outliers = group[outlier_mask].index.tolist()
        
        if part_outliers:
            outliers_to_remove.extend(part_outliers)
            removed_quantities = group.loc[part_outliers, qty_col].tolist()
            analysis_summary.append({
                'part': part_num,
                'category': 'LOW' if median_qty <= 10 else 'MEDIUM' if median_qty <= 100 else 'HIGH',
                'median': median_qty,
                'max_before': max_qty,
                'removed_count': len(part_outliers),
                'removed_quantities': removed_quantities,
                'threshold': f"≤ {upper_threshold:.1f}",
                'reasoning': f"median={median_qty:.0f}, iqr={iqr:.1f}"
            })
    
    # Remove outliers
    df_cleaned = df.drop(outliers_to_remove)
    removed_count = len(outliers_to_remove)
    
    print(f"Progressive outlier detection results:")
    print(f"  Original rows: {original_count:,}")
    print(f"  Removed outliers: {removed_count:,}")
    print(f"  Final rows: {len(df_cleaned):,}")
    
    # Avoid division by zero for empty dataframes
    if original_count > 0:
        print(f"  Removal rate: {removed_count/original_count*100:.2f}%")
    else:
        print(f"  Removal rate: 0.00% (empty dataframe)")
    
    # Show summary of parts that had outliers removed
    if analysis_summary:
        print(f"\nParts with outliers removed ({len(analysis_summary)} parts):")
        for item in analysis_summary[:10]:  # Show first 10
            print(f"  {item['part']} ({item['category']}): removed {item['removed_count']} quantities {item['removed_quantities']}")
            print(f"    → threshold: {item['threshold']} | {item['reasoning']}")
        if len(analysis_summary) > 10:
            print(f"  ... and {len(analysis_summary) - 10} more parts")
    else:
        print("\nNo outliers detected - all quantities appear reasonable for their respective parts")
    
    return df_cleaned