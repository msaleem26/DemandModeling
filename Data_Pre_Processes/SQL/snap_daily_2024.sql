formatted_parts = ", ".join(f"'{part}'" for part in unique_parts_list)

-- sql_query = f'''
SELECT "P/N", "Condition Code", "Qty Available", "SNAP_DATE", "Unit Cost", "Unit Price", "List Price"
FROM DW_PROD.DW.SNAP_STOCK_DAILY
WHERE "SNAP_DATE" >= '2024-08-01 00:00:00';
AND "P/N" IN ({formatted_parts});
-- '''

-- print(sql_query)
