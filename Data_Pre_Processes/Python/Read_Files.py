import pandas as pd
from pathlib import Path

def read_csv_dataframe(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}\nDirectory contents: {[x.name for x in p.parent.glob('*')]}")
    if p.suffix.lower() != ".csv":
        raise ValueError(f"Unsupported file extension: {p.suffix} — only .csv supported")
    df = pd.read_csv(p)
    return df

def read_excel_dataframe(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}\nDirectory contents: {[x.name for x in p.parent.glob('*')]}")
    if p.suffix.lower() != ".xlsx":
        raise ValueError(f"Unsupported file extension: {p.suffix} — only .xlsx supported")
    df = pd.read_excel(p)
    return df

def save_csv_dataframe(df, filename):
    output_dir = Path(__file__).parent.parent / "Output"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / f"{filename}"
    
    if filepath.exists():
        print(f"File already exists, skipping: {filepath}")
        return
    
    print(f"Saving DataFrame to: {filename}")
    df.to_csv(filepath, index=False)
    print(f"Saved DataFrame to: {filepath}")

def save_excel_dataframe(df, filename):
    output_dir = Path(__file__).parent.parent / "Output"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / f"{filename}"
    
    if filepath.exists():
        print(f"File already exists, skipping: {filepath}")
        return
    
    print(f"Saving DataFrame to: {filename}")
    df.to_excel(filepath, index=False)
    print(f"Saved DataFrame to: {filepath}")
