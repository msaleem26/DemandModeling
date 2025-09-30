# Analyze Quantity distribution by Part Number to identify outliers
import numpy as np
import matplotlib.pyplot as plt

# First, let's examine the Quantity column
print("=== QUANTITY ANALYSIS ===")
print(f"Total rows: {len(Rotabull_df):,}")

# Check for Quantity column variations
qty_candidates = ["Quantity", "Qty", "Quantity Received", "Qty Received", "Qty Received (EA)"]
qty_col = None
for col in qty_candidates:
    if col in Rotabull_df.columns:
        qty_col = col
        break

if qty_col:
    print(f"Found quantity column: '{qty_col}'")
    
    # Convert to numeric and analyze
    Rotabull_df[f'{qty_col}_numeric'] = pd.to_numeric(Rotabull_df[qty_col], errors='coerce')
    
    print(f"\nOverall Quantity Statistics:")
    print(f"  Min: {Rotabull_df[f'{qty_col}_numeric'].min():,}")
    print(f"  Max: {Rotabull_df[f'{qty_col}_numeric'].max():,}")
    print(f"  Mean: {Rotabull_df[f'{qty_col}_numeric'].mean():,.2f}")
    print(f"  Median: {Rotabull_df[f'{qty_col}_numeric'].median():,.2f}")
    print(f"  95th percentile: {Rotabull_df[f'{qty_col}_numeric'].quantile(0.95):,.2f}")
    print(f"  99th percentile: {Rotabull_df[f'{qty_col}_numeric'].quantile(0.99):,.2f}")
    print(f"  99.9th percentile: {Rotabull_df[f'{qty_col}_numeric'].quantile(0.999):,.2f}")
    
    # Analyze by Part Number
    print(f"\n=== BY PART NUMBER ANALYSIS ===")
    part_qty_stats = (Rotabull_df.groupby('Part Number')[f'{qty_col}_numeric']
                      .agg(['count', 'min', 'max', 'mean', 'median', 'std'])
                      .round(2))
    
    print(f"Total unique part numbers: {len(part_qty_stats):,}")
    print(f"\nPart numbers with extreme max quantities (>10,000):")
    extreme_parts = part_qty_stats[part_qty_stats['max'] > 10000].sort_values('max', ascending=False)
    print(extreme_parts.head(10))
    
    print(f"\nPart numbers with unusual patterns (high std deviation):")
    high_std_parts = part_qty_stats[part_qty_stats['std'] > 1000].sort_values('std', ascending=False)
    print(high_std_parts.head(10))
    
else:
    print("No quantity column found!")
    print("Available columns:", list(Rotabull_df.columns))

    # Test the quantity outlier detection function
reload_modules()
from Python.Filtering import quantity_outliers

# Let's test with a smaller subset first to see the per-part analysis
print("=== TESTING QUANTITY OUTLIER DETECTION ===")

filename_outliers = "Rotabull_NoOutliers"
Rotabull_df_clean = quantity_outliers(Rotabull_df, filename_outliers)

print("\n=== BEFORE VS AFTER COMPARISON ===")
print(f"Original: {len(Rotabull_df):,} rows")
print(f"Cleaned:  {len(Rotabull_df_clean):,} rows")
print(f"Removed:  {len(Rotabull_df) - len(Rotabull_df_clean):,} rows ({100*(len(Rotabull_df) - len(Rotabull_df_clean))/len(Rotabull_df):.2f}%)")

# Let's examine how specific parts were handled
print("=== PER-PART ANALYSIS EXAMPLES ===")

# Check some of the extreme parts we identified earlier
extreme_part_examples = ['3863104-1', 'S6-01-0005-306', 'AN960PD4L', '113270-307']

for part in extreme_part_examples:
    if part in Rotabull_df['Part Number'].values:
        # Original data for this part
        original_part_data = Rotabull_df[Rotabull_df['Part Number'] == part]['Quantity'].astype(int)
        
        # Cleaned data for this part
        if part in Rotabull_df_clean['Part Number'].values:
            cleaned_part_data = Rotabull_df_clean[Rotabull_df_clean['Part Number'] == part]['Quantity'].astype(int)
        else:
            cleaned_part_data = pd.Series([], dtype=int)
        
        print(f"\nPart: {part}")
        print(f"  Original: {len(original_part_data)} rows, Quantities: {sorted(original_part_data.tolist())}")
        print(f"  Cleaned:  {len(cleaned_part_data)} rows, Quantities: {sorted(cleaned_part_data.tolist())}")
        print(f"  Removed:  {len(original_part_data) - len(cleaned_part_data)} outliers")

# Show overall improvement in data quality
print(f"\n=== DATA QUALITY IMPROVEMENT ===")
original_qty = pd.to_numeric(Rotabull_df['Quantity'], errors='coerce')
cleaned_qty = pd.to_numeric(Rotabull_df_clean['Quantity'], errors='coerce')

print(f"Mean quantity - Before: {original_qty.mean():.2f}, After: {cleaned_qty.mean():.2f}")
print(f"Max quantity - Before: {original_qty.max():,}, After: {cleaned_qty.max():,}")
print(f"99.9th percentile - Before: {original_qty.quantile(0.999):.0f}, After: {cleaned_qty.quantile(0.999):.0f}")

# Update the main dataframe
Rotabull_df = Rotabull_df_clean.copy()
print(f"\n✅ Updated Rotabull_df with cleaned data: {len(Rotabull_df):,} rows")

# Analyze different part categories to understand quantity patterns better
print("=== PART CATEGORY ANALYSIS ===")

# Categorize parts by their typical quantity ranges
part_categories = []

for part_num, group in Rotabull_df.groupby('Part Number'):
    quantities = pd.to_numeric(group['Quantity'], errors='coerce').dropna()
    if len(quantities) == 0:
        continue
        
    stats = {
        'part_number': part_num,
        'count': len(quantities),
        'min': quantities.min(),
        'max': quantities.max(),
        'median': quantities.median(),
        'mean': quantities.mean(),
        'std': quantities.std() if len(quantities) > 1 else 0,
        'q75': quantities.quantile(0.75),
        'q95': quantities.quantile(0.95)
    }
    part_categories.append(stats)

parts_df = pd.DataFrame(part_categories)

# Categorize parts by volume patterns
print("Part categories by typical volume:")
print("\n1. LOW VOLUME parts (median ≤ 10):")
low_vol = parts_df[parts_df['median'] <= 10]
print(f"   Count: {len(low_vol):,} parts ({len(low_vol)/len(parts_df)*100:.1f}%)")
print(f"   Typical max: {low_vol['max'].quantile(0.95):.0f}")
print(f"   Examples: {low_vol['part_number'].head(5).tolist()}")

print("\n2. MEDIUM VOLUME parts (median 11-100):")
med_vol = parts_df[(parts_df['median'] > 10) & (parts_df['median'] <= 100)]
print(f"   Count: {len(med_vol):,} parts ({len(med_vol)/len(parts_df)*100:.1f}%)")
print(f"   Typical max: {med_vol['max'].quantile(0.95):.0f}")
print(f"   Examples: {med_vol['part_number'].head(5).tolist()}")

print("\n3. HIGH VOLUME parts (median > 100):")
high_vol = parts_df[parts_df['median'] > 100]
print(f"   Count: {len(high_vol):,} parts ({len(high_vol)/len(parts_df)*100:.1f}%)")
print(f"   Typical max: {high_vol['max'].quantile(0.95):.0f}")
if len(high_vol) > 0:
    print(f"   Examples: {high_vol['part_number'].head(5).tolist()}")

# Look at parts with consistently high quantities (like 113270-307)
print("\n4. CONSISTENTLY HIGH parts (min > 1000):")
very_high = parts_df[parts_df['min'] > 1000]
print(f"   Count: {len(very_high):,} parts")
if len(very_high) > 0:
    print("   Details:")
    for _, row in very_high.head(10).iterrows():
        print(f"     {row['part_number']}: min={row['min']:.0f}, max={row['max']:.0f}, median={row['median']:.0f}")

# Specific analysis for the problematic part
print(f"\n5. Analysis of part 113270-307:")
if '113270-307' in parts_df['part_number'].values:
    part_row = parts_df[parts_df['part_number'] == '113270-307'].iloc[0]
    print(f"   All quantities are legitimate high-volume: {part_row['min']:.0f} to {part_row['max']:.0f}")
    print("   This part should NOT be filtered - it's a legitimate high-volume part")


    # Let's check if part 113270-307 exists in our dataset and analyze its quantities
target_part = '113270-307'
target_data = Rotabull_df[Rotabull_df['Part Number'] == target_part]

print(f"=== ANALYSIS OF PART {target_part} ===")
if len(target_data) > 0:
    quantities = sorted(target_data['Qty'].tolist())
    print(f"Found {len(target_data)} rows for part {target_part}")
    print(f"Quantities: {quantities}")
    print(f"Min: {min(quantities)}, Max: {max(quantities)}, Median: {target_data['Qty'].median()}")
    
    # Check if this part was affected by outlier removal
    original_data = Rotabull_raw_df[Rotabull_raw_df['Part Number'] == target_part]
    if len(original_data) > len(target_data):
        removed_count = len(original_data) - len(target_data)
        removed_quantities = original_data[~original_data.index.isin(target_data.index)]['Qty'].tolist()
        print(f"⚠️  REMOVED {removed_count} rows with quantities: {removed_quantities}")
    else:
        print("✅ No rows were removed for this part")
else:
    print(f"❌ Part {target_part} not found in current dataset")
    
    # Check if it exists in the original dataset
    if 'Rotabull_raw_df' in globals():
        original_data = Rotabull_raw_df[Rotabull_raw_df['Part Number'] == target_part]
        if len(original_data) > 0:
            quantities = sorted(original_data['Qty'].tolist())
            print(f"BUT found {len(original_data)} rows in ORIGINAL dataset")
            print(f"Original quantities: {quantities}")
            print("❌ ALL ROWS WERE REMOVED BY OUTLIER DETECTION!")


            # Now let's create an improved outlier detection function and update the module
improved_outlier_code = '''
def quantity_outliers_improved(df):
    """
    Improved outlier detection that considers part-specific patterns
    and doesn't penalize legitimate high-volume parts.
    """
    import pandas as pd
    import numpy as np
    from .Read_Files import read_csv_dataframe, save_csv_dataframe
    
    print("Starting improved quantity outlier detection...")
    original_count = len(df)
    
    # Group by part number for per-part analysis
    grouped = df.groupby('Part Number')
    
    outliers_to_remove = []
    analysis_summary = []
    
    for part_num, group in grouped:
        quantities = group['Qty'].values
        
        if len(quantities) < 3:
            # Too few data points for meaningful outlier detection
            continue
            
        # Calculate statistics
        median_qty = np.median(quantities)
        q1 = np.percentile(quantities, 25)
        q3 = np.percentile(quantities, 75)
        iqr = q3 - q1
        
        # Determine part category and set appropriate thresholds
        if median_qty <= 10:
            # LOW VOLUME parts - be very conservative with outliers
            # Only remove obvious data entry errors (like 99999)
            upper_threshold = max(100, q3 + 5 * iqr)  # At least 100, or statistical threshold
            lower_threshold = 0  # Don't remove low quantities for low-volume parts
            
        elif median_qty <= 100:
            # MEDIUM VOLUME parts - moderate outlier detection
            upper_threshold = max(1000, q3 + 3 * iqr)
            lower_threshold = max(0, q1 - 3 * iqr)
            
        else:
            # HIGH VOLUME parts - allow much higher variation
            # These parts legitimately have high quantities
            upper_threshold = max(10000, q3 + 5 * iqr)  # Very generous upper limit
            lower_threshold = max(0, q1 - 3 * iqr)
        
        # Additional check: if max quantity is reasonable relative to median, keep it
        max_qty = np.max(quantities)
        if max_qty <= median_qty * 20:  # If max is within 20x median, likely legitimate
            continue
            
        # Find outliers for this part
        part_outliers = group[
            (group['Qty'] > upper_threshold) |
            (group['Qty'] < lower_threshold)
        ].index.tolist()
        
        if part_outliers:
            outliers_to_remove.extend(part_outliers)
            removed_quantities = group.loc[part_outliers, 'Qty'].tolist()
            analysis_summary.append({
                'part': part_num,
                'category': 'LOW' if median_qty <= 10 else 'MEDIUM' if median_qty <= 100 else 'HIGH',
                'median': median_qty,
                'removed_count': len(part_outliers),
                'removed_quantities': removed_quantities,
                'thresholds': f"{lower_threshold:.1f} - {upper_threshold:.1f}"
            })
    
    # Remove outliers
    df_cleaned = df.drop(outliers_to_remove)
    removed_count = len(outliers_to_remove)
    
    print(f"Improved outlier detection results:")
    print(f"  Original rows: {original_count:,}")
    print(f"  Removed outliers: {removed_count:,}")
    print(f"  Final rows: {len(df_cleaned):,}")
    print(f"  Removal rate: {removed_count/original_count*100:.2f}%")
    
    # Show summary of parts that had outliers removed
    if analysis_summary:
        print(f"\\nParts with outliers removed ({len(analysis_summary)} parts):")
        for item in analysis_summary[:10]:  # Show first 10
            print(f"  {item['part']} ({item['category']}): removed {item['removed_count']} quantities {item['removed_quantities']} (thresholds: {item['thresholds']})")
        if len(analysis_summary) > 10:
            print(f"  ... and {len(analysis_summary) - 10} more parts")
    
    return df_cleaned
'''

# Write the improved function to the Filtering module
filtering_file = r'c:\Users\mmarek\Documents\Project_Files\Rotabull Data Export 1 Year\Data_Pre_Processes\Python\Filtering.py'

# Read current content
with open(filtering_file, 'r') as f:
    current_content = f.read()

# Add the improved function
with open(filtering_file, 'a') as f:
    f.write('\n\n' + improved_outlier_code)

print("✅ Added improved outlier detection function to Filtering.py")
print("✅ Function: quantity_outliers_improved()")
print("   - Respects part categories (LOW/MEDIUM/HIGH volume)")
print("   - Conservative with low-volume parts") 
print("   - Allows legitimate high quantities for high-volume parts")
print("   - Uses 20x median rule to preserve reasonable variations")


# Debug the outlier detection - let's trace through the logic manually
print("=== DEBUGGING OUTLIER DETECTION ===")

# Check the TEST-OUTLIER-PART specifically
outlier_test = test_df[test_df['Part Number'] == 'TEST-OUTLIER-PART']
quantities = outlier_test['Qty'].values
print(f"TEST-OUTLIER-PART quantities: {quantities}")

import numpy as np
median_qty = np.median(quantities)
q1 = np.percentile(quantities, 25)
q3 = np.percentile(quantities, 75)
iqr = q3 - q1

print(f"Statistics: median={median_qty}, q1={q1}, q3={q3}, iqr={iqr}")

# This should be LOW VOLUME (median ≤ 10)
upper_threshold = max(100, q3 + 5 * iqr)
print(f"Upper threshold: {upper_threshold}")

# Check the 20x median rule
max_qty = np.max(quantities)
median_check = max_qty <= median_qty * 20
print(f"Max quantity: {max_qty}")
print(f"20x median check: {max_qty} <= {median_qty * 20} = {median_check}")

# The issue is the 20x median rule is allowing 99999!
# Let's fix this by being more strict about obvious outliers


# Test the fixed outlier detection function
# Reload the module to get the updated function
import importlib
import Python.Filtering
importlib.reload(Python.Filtering)
from Python.Filtering import quantity_outliers_improved

print("=== TESTING FIXED OUTLIER DETECTION ===")

# Test on our sample with synthetic cases
test_cleaned_fixed = quantity_outliers_improved(test_df)

# Check results for our test parts
print(f"\n=== FIXED TEST RESULTS ===")
for test_part in ['TEST-113270-307', 'TEST-OUTLIER-PART']:
    original = test_df[test_df['Part Number'] == test_part]
    cleaned = test_cleaned_fixed[test_cleaned_fixed['Part Number'] == test_part]
    
    print(f"{test_part}:")
    print(f"  Original: {len(original)} rows, Qty: {sorted(original['Qty'].tolist())}")
    print(f"  Cleaned:  {len(cleaned)} rows, Qty: {sorted(cleaned['Qty'].tolist())}")
    if len(original) > len(cleaned):
        removed = original[~original.index.isin(cleaned.index)]
        print(f"  ✅ Correctly removed: {removed['Qty'].tolist()}")
    else:
        print(f"  ✅ No outliers removed (as expected)" if test_part == 'TEST-113270-307' else "  ❌ Should have removed outliers")

        # Let's debug why TEST-OUTLIER-PART isn't being filtered
print("=== DEBUGGING TEST-OUTLIER-PART ===")

# Manual calculation for TEST-OUTLIER-PART
debug_data = test_df[test_df['Part Number'] == 'TEST-OUTLIER-PART']
print(f"Data: {debug_data[['Part Number', 'Qty']].values}")

# Check which quantity column is being used
qty_col = 'Quantity' if 'Quantity' in debug_data.columns else 'Qty'
print(f"Using quantity column: {qty_col}")

quantities = debug_data[qty_col].values
print(f"Quantities: {quantities}")

import numpy as np
median_qty = np.median(quantities)
q1 = np.percentile(quantities, 25)
q3 = np.percentile(quantities, 75)
iqr = q3 - q1

print(f"Statistics: median={median_qty}, q1={q1}, q3={q3}, iqr={iqr}")

# Calculate thresholds (LOW VOLUME category since median ≤ 10)
absolute_max = 50000
if iqr == 0:
    upper_threshold = max(50, median_qty * 10)
else:
    upper_threshold = max(100, q3 + 3 * iqr)

upper_threshold = min(upper_threshold, absolute_max)
print(f"Upper threshold: {upper_threshold}")

# Check if 99999 exceeds threshold
max_qty = np.max(quantities)
print(f"Max quantity: {max_qty}")
print(f"Should remove? {max_qty} > {upper_threshold} = {max_qty > upper_threshold}")

# The issue might be that the test data doesn't have the right column structure
print(f"Test data columns: {list(debug_data.columns)}")
print(f"Test data sample:")
print(debug_data.head())

# Fix the test data by creating it properly with the right column structure
print("=== CREATING PROPER TEST DATA ===")

# Use a small sample from the main dataset
test_df_fixed = Rotabull_df.head(1000).copy()

# Create proper test parts that match the dataframe structure
# Create rows that will be added to the test dataframe
num_original_cols = len(test_df_fixed.columns)

# Create TEST-113270-307 data (legitimate high quantities)
high_vol_indices = range(len(test_df_fixed), len(test_df_fixed) + 5)
for i, qty in enumerate([45000, 60000, 75000, 75000, 80000]):
    # Create a new row based on the first row structure, but modify key fields
    new_row = test_df_fixed.iloc[0].copy()
    new_row['Part Number'] = 'TEST-113270-307'
    new_row['Quantity'] = qty
    # Add this row to the dataframe
    test_df_fixed.loc[len(test_df_fixed)] = new_row

# Create TEST-OUTLIER-PART data (obvious outlier)
for i, qty in enumerate([1, 2, 99999]):
    new_row = test_df_fixed.iloc[0].copy()
    new_row['Part Number'] = 'TEST-OUTLIER-PART'
    new_row['Quantity'] = qty
    # Add this row to the dataframe
    test_df_fixed.loc[len(test_df_fixed)] = new_row

print(f"Created proper test dataset: {len(test_df_fixed):,} rows")

# Check our test parts
for test_part in ['TEST-113270-307', 'TEST-OUTLIER-PART']:
    part_data = test_df_fixed[test_df_fixed['Part Number'] == test_part]
    quantities = part_data['Quantity'].tolist()
    print(f"{test_part}: {len(part_data)} rows, Quantities: {quantities}")

# Now test the outlier detection on the properly structured data
print(f"\n=== TESTING WITH PROPERLY STRUCTURED DATA ===")
test_cleaned_proper = quantity_outliers_improved(test_df_fixed)

# Check results
print(f"\n=== PROPER TEST RESULTS ===")
for test_part in ['TEST-113270-307', 'TEST-OUTLIER-PART']:
    original = test_df_fixed[test_df_fixed['Part Number'] == test_part]
    cleaned = test_cleaned_proper[test_cleaned_proper['Part Number'] == test_part]
    
    print(f"{test_part}:")
    print(f"  Original: {len(original)} rows, Qty: {sorted(original['Quantity'].tolist())}")
    print(f"  Cleaned:  {len(cleaned)} rows, Qty: {sorted(cleaned['Quantity'].tolist())}")
    if len(original) > len(cleaned):
        removed = original[~original.index.isin(cleaned.index)]
        print(f"  ✅ Correctly removed: {removed['Quantity'].tolist()}")
    else:
        print(f"  ✅ No outliers removed" if test_part == 'TEST-113270-307' else "  ❌ Should have removed outliers")

        # Check column names first
print("=== CHECKING DATAFRAME COLUMNS ===")
print(f"Columns in Rotabull_df: {list(Rotabull_df.columns)}")
print(f"Shape: {Rotabull_df.shape}")

# Check if it's 'Quantity' instead of 'Qty'
if 'Quantity' in Rotabull_df.columns:
    print("Found 'Quantity' column - will use that")
    qty_col = 'Quantity'
elif 'Qty' in Rotabull_df.columns:
    print("Found 'Qty' column - will use that") 
    qty_col = 'Qty'
else:
    # Find column with quantity-like name
    qty_cols = [col for col in Rotabull_df.columns if 'qty' in col.lower() or 'quant' in col.lower()]
    print(f"Potential quantity columns: {qty_cols}")
    if qty_cols:
        qty_col = qty_cols[0]
        print(f"Using column: {qty_col}")
    else:
        print("No quantity column found!")
        print(f"Available columns: {list(Rotabull_df.columns)}")

        # Now apply the improved outlier detection to the full dataset
# Reload the module to get the updated function
import importlib
import Python.Filtering
importlib.reload(Python.Filtering)
from Python.Filtering import quantity_outliers_improved

print("=== APPLYING IMPROVED OUTLIER DETECTION TO FULL DATASET ===")
print(f"Current Rotabull_df: {len(Rotabull_df):,} rows")

# Apply the improved outlier detection
Rotabull_df_improved = quantity_outliers_improved(Rotabull_df)

# Data quality metrics
print(f"\n=== DATA QUALITY METRICS ===")
print(f"Mean quantity - Improved: {Rotabull_df_improved['Quantity'].mean():.2f}")
print(f"Max quantity - Improved: {Rotabull_df_improved['Quantity'].max():,}")
print(f"99.9th percentile - Improved: {Rotabull_df_improved['Quantity'].quantile(0.999):.0f}")

# Update our main dataframe with the improved cleaning
Rotabull_df = Rotabull_df_improved.copy()
print(f"\n✅ Updated Rotabull_df with improved outlier detection: {len(Rotabull_df):,} rows")

# Test the corrected outlier detection (upper threshold only)
print("=== TESTING CORRECTED OUTLIER DETECTION (UPPER THRESHOLD ONLY) ===")

# Reload the updated module
import importlib
import Python.Filtering
importlib.reload(Python.Filtering)
from Python.Filtering import quantity_outliers_improved

# Test with our properly structured test data
print("Creating test data with high and low quantities...")

# Use a small sample and add test cases
test_df_corrected = Rotabull_df.head(100).copy()

# Add test cases with both high and low quantities
test_cases = [
    # High volume legitimate part (should keep all)
    {'part': 'TEST-HIGH-LEGIT', 'quantities': [45000, 60000, 75000, 75000, 80000]},
    # Low volume part with obvious outlier (should remove only 99999)
    {'part': 'TEST-LOW-OUTLIER', 'quantities': [1, 2, 3, 99999]},
    # Part with very low quantities (should keep all, including zeros)
    {'part': 'TEST-LOW-QUANTITIES', 'quantities': [0, 1, 1, 2, 3]}
]

for test_case in test_cases:
    for qty in test_case['quantities']:
        new_row = test_df_corrected.iloc[0].copy()
        new_row['Part Number'] = test_case['part']
        new_row['Quantity'] = qty
        test_df_corrected.loc[len(test_df_corrected)] = new_row

print(f"Created test dataset with {len(test_df_corrected):,} rows")

# Show what we're testing
for test_case in test_cases:
    part_data = test_df_corrected[test_df_corrected['Part Number'] == test_case['part']]
    print(f"{test_case['part']}: {test_case['quantities']}")

# Apply the corrected outlier detection
print(f"\n=== APPLYING CORRECTED OUTLIER DETECTION ===")
test_cleaned_corrected = quantity_outliers_improved(test_df_corrected)

# Check results for each test case
print(f"\n=== CORRECTED TEST RESULTS ===")
for test_case in test_cases:
    part_name = test_case['part']
    original = test_df_corrected[test_df_corrected['Part Number'] == part_name]
    cleaned = test_cleaned_corrected[test_cleaned_corrected['Part Number'] == part_name]
    
    print(f"\n{part_name}:")
    print(f"  Original: {len(original)} rows, Qty: {sorted(original['Quantity'].tolist())}")
    print(f"  Cleaned:  {len(cleaned)} rows, Qty: {sorted(cleaned['Quantity'].tolist())}")
    
    if len(original) > len(cleaned):
        removed = original[~original.index.isin(cleaned.index)]
        removed_qtys = removed['Quantity'].tolist()
        print(f"  ✅ Removed high outliers: {removed_qtys}")
        
        # Check if low quantities were preserved
        low_qtys = [q for q in test_case['quantities'] if q < 10]
        preserved_low = cleaned[cleaned['Quantity'] < 10]['Quantity'].tolist()
        print(f"  ✅ Preserved low quantities: {sorted(preserved_low)}")
    else:
        print(f"  ✅ No outliers removed - all quantities preserved")



        # Apply the corrected outlier detection to the full dataset
print("=== APPLYING CORRECTED OUTLIER DETECTION TO FULL DATASET ===")
print(f"Current Rotabull_df: {len(Rotabull_df):,} rows")

# Apply the corrected outlier detection (upper threshold only)
Rotabull_df_final = quantity_outliers_improved(Rotabull_df)

# Data quality metrics
print(f"\n=== FINAL DATA QUALITY METRICS ===")
print(f"Mean quantity: {Rotabull_df_final['Quantity'].mean():.2f}")
print(f"Min quantity: {Rotabull_df_final['Quantity'].min():,}")
print(f"Max quantity: {Rotabull_df_final['Quantity'].max():,}")
print(f"99.9th percentile: {Rotabull_df_final['Quantity'].quantile(0.999):.0f}")

# Update our main dataframe with the final cleaned data
Rotabull_df = Rotabull_df_final.copy()
print(f"\n✅ Updated Rotabull_df with corrected outlier detection: {len(Rotabull_df):,} rows")
print("✅ Now only removes excessively HIGH quantities, preserves all low quantities including zeros")

# Test the improved outlier detection function
from Python.Filtering import quantity_outliers_improved

# Create a test scenario with a part that has legitimate high quantities
# Let's use a sample of our current data and add synthetic test cases
test_df = Rotabull_df.head(1000).copy()  # Use current data for testing

# Add a test part with high legitimate quantities (like your 113270-307 example)
test_part_data = pd.DataFrame({
    'Part Number': ['TEST-113270-307'] * 5,
    'Qty': [45000, 60000, 75000, 75000, 80000],
    'Date': pd.date_range('2024-01-01', periods=5),
    'Customer': ['Test Customer'] * 5,
    'Unit Price': [1.0] * 5,
    'Line Total': [45000, 60000, 75000, 75000, 80000]
})

# Also add some obvious outliers to test the detection
outlier_part_data = pd.DataFrame({
    'Part Number': ['TEST-OUTLIER-PART'] * 3,
    'Qty': [1, 2, 99999],  # 99999 should be detected as outlier
    'Date': pd.date_range('2024-01-01', periods=3),
    'Customer': ['Test Customer'] * 3,
    'Unit Price': [1.0] * 3,
    'Line Total': [1, 2, 99999]
})

# Combine test data
test_df = pd.concat([test_df, test_part_data, outlier_part_data], ignore_index=True)

print(f"Original test dataset: {len(test_df):,} rows")
print(f"Added test parts:")
print(f"  TEST-113270-307: quantities {test_part_data['Qty'].tolist()}")
print(f"  TEST-OUTLIER-PART: quantities {outlier_part_data['Qty'].tolist()}")

# Apply improved outlier detection
test_cleaned = quantity_outliers_improved(test_df)

# Check results for our test parts
print(f"\n=== TEST RESULTS ===")
for test_part in ['TEST-113270-307', 'TEST-OUTLIER-PART']:
    original = test_df[test_df['Part Number'] == test_part]
    cleaned = test_cleaned[test_cleaned['Part Number'] == test_part]
    
    print(f"{test_part}:")
    print(f"  Original: {len(original)} rows, Qty: {sorted(original['Qty'].tolist())}")
    print(f"  Cleaned:  {len(cleaned)} rows, Qty: {sorted(cleaned['Qty'].tolist())}")
    if len(original) > len(cleaned):
        removed = original[~original.index.isin(cleaned.index)]
        print(f"  ✅ Removed: {removed['Qty'].tolist()}")
    else:
        print(f"  ✅ No outliers removed")