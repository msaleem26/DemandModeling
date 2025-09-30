from pathlib import Path


input_dir = Path(r"C:\Users\mmarek\Documents\Project_Files\Rotabull Data Export 1 Year\Data_Pre_Processes\Initial_Files")
csv_path = input_dir / "Part numbers with fair market value.csv"

if not csv_path.exists():
    print(f"File not found: {csv_path}")
    print("Input directory contents:", [p.name for p in input_dir.glob("*")])
    raise FileNotFoundError(f"{csv_path} not found")

FMV_df = pd.read_csv(csv_path, parse_dates=True, infer_datetime_format=True)

print(f"Loaded {len(FMV_df)} rows, {len(FMV_df.columns)} columns")
FMV_df.head()