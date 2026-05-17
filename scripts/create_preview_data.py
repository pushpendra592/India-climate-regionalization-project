import pandas as pd
from pathlib import Path

def create_previews():
    print("Creating lightweight data previews for the dashboard...")
    data_dir = Path("data")
    previews_dir = data_dir / "previews"
    previews_dir.mkdir(exist_ok=True)

    files_to_preview = [
        data_dir / "interim" / "nasa_power_combined.csv",
        data_dir / "interim" / "merged_daily.csv",
        data_dir / "processed" / "feature_matrix_daily.csv",
        data_dir / "processed" / "feature_matrix_monthly.csv",
        data_dir / "processed" / "feature_matrix_seasonal.csv",
        data_dir / "processed" / "feature_matrix_yearly.csv",
        data_dir / "processed" / "climate_normals.csv"
    ]

    for f in files_to_preview:
        if f.exists():
            try:
                df = pd.read_csv(f, nrows=10)
                preview_path = previews_dir / f.name
                df.to_csv(preview_path, index=False)
                print(f"✅ Created preview: {preview_path} ({preview_path.stat().st_size / 1024:.1f} KB)")
            except Exception as e:
                print(f"❌ Error processing {f.name}: {e}")
        else:
            print(f"⚠️ Source file not found: {f}")
            
    print("\nDone! You can now commit the 'data/previews/' directory to GitHub.")

if __name__ == "__main__":
    create_previews()
