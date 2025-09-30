from snowflake.connector import connect
import json
import snowflake.connector
import pandas as pd
from pathlib import Path

def get_snowflake_connection():
    """
    Establish and return a Snowflake database connection.
    Reads connection parameters from credentials.json file.
    """
    #Read Connection Parameters:
    project_dir = Path(r"C:\Users\mmarek\Documents\Project_Files")
    cred_path = project_dir / "credentials.json"

    if not cred_path.exists():
        print(f"Credentials file not found: {cred_path}")
        print("Project directory contents:", [p.name for p in project_dir.glob("*")])
        raise FileNotFoundError(f"{cred_path} not found")

    with cred_path.open("r", encoding="utf-8") as f:
        connection_parameters = json.load(f)

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=connection_parameters['user'],
        password=connection_parameters['password'],
        account=connection_parameters['account'],
        warehouse=connection_parameters['warehouse'],
        role='BI_FINANCE_ANALYST_HQ',
        database=connection_parameters['database'],
        schema=connection_parameters['schema']
    )
    
    return conn

def findInventory(Rotabull_df, filename_inventory):
    """
    Find inventory data for parts in Rotabull_df.
    First checks for existing CSV file, otherwise queries Snowflake.
    """

    # Check if inventory file with filename_inventory already exists
    current_file_dir = Path(__file__).parent
    output_dir = current_file_dir / ".." / "Output"
    inventory_path = output_dir / f"{filename_inventory}"
    inventory_path = inventory_path.resolve()
    print(inventory_path)
    if inventory_path.exists():
        print(f"Found existing inventory file: {inventory_path}")
        try:
            DF_Inventory = pd.read_csv(inventory_path)
            print(f"Loaded existing inventory: {inventory_path} ({len(DF_Inventory)} rows, {len(DF_Inventory.columns)} cols)")
            return DF_Inventory
        except Exception as e:
            print(f"Unable to load existing inventory file {inventory_path}: {e}")
            # Continue to query Snowflake instead

    # Get unique parts from Rotabull data
    unique_parts = (
        Rotabull_df['Part Number']
        .dropna()
        .astype(str)
        .str.strip()
    )
    unique_parts_list = sorted(p for p in unique_parts.unique() if p != "")
    
    print(f"Unique parts found: {len(unique_parts_list)}")
    print("Sample parts:", unique_parts_list[:10])

    # Get Snowflake connection
    conn = get_snowflake_connection()

    # Query Snowflake in chunks to avoid massive SQL
    def _escape_sql(s: str) -> str:
        return str(s).replace("'", "''")

    CHUNK = 1000
    total = len(unique_parts_list)
    results = []
    
    for i in range(0, total, CHUNK):
        chunk = unique_parts_list[i:i+CHUNK]
        formatted = ", ".join(f"'{_escape_sql(p)}'" for p in chunk)
        sql_chunk = f"""
        SELECT "P/N", "Condition Code", "Qty Available", "SNAP_DATE", "Unit Cost", "Unit Price", "List Price", "P/N Type Code Simple"
        FROM DW_PROD.DW.SNAP_STOCK_DAILY
        WHERE "SNAP_DATE" >= '2024-08-01 00:00:00'
          AND "P/N" IN ({formatted})
        """
        df_part = pd.read_sql(sql_chunk, conn)
        results.append(df_part)
        print(f"Fetched {i+len(chunk):,}/{total:,} parts...")
    
    DF_Inventory = pd.concat(results, ignore_index=True) if results else pd.DataFrame(columns=["P/N", "Condition Code", "Qty Available", "SNAP_DATE", "Unit Cost", "Unit Price", "List Price", "P/N Type Code Simple"])
    print(f"Loaded DF_Inventory via chunked query: {len(DF_Inventory):,} rows, {len(DF_Inventory.columns)} cols")

    # Close connection
    try:
        conn.close()
    except Exception:
        pass
    
    # Save the inventory data
    try:
        DF_Inventory.to_csv(inventory_path, index=False)
    except Exception as e:
        print(f"Error saving inventory file: {e}")
    
    return DF_Inventory
