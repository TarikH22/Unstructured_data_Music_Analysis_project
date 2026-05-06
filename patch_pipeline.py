import sys

with open("src/run_pipeline.py", "r") as f:
    content = f.read()

cleaning_code = """
    # 10. Cleaning stage (Lab 9)
    try:
        from src.cleaning.clean_pipeline import run_cleaning_pipeline
        from pathlib import Path
        raw_csv_path = Path("data/processed/analytics/integrated_raw_export.csv")
        out_dir = Path("data/processed/cleaned")
        run_cleaning_pipeline(raw_csv_path, out_dir)
    except Exception as e:
        from utils.logger import logger
        logger.error(f"Cleaning stage failed: {e}")

    logger.info("Pipeline finished")
"""

if "# 10. Cleaning stage" not in content:
    content = content.replace("    logger.info(\"Pipeline finished\")", cleaning_code)
    with open("src/run_pipeline.py", "w") as f:
        f.write(content)
        print("Patched src/run_pipeline.py successfully")
else:
    print("Already patched.")
