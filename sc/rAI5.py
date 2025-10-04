from pathlib import Path
import shutil

def clean_results(results_dir, log):
    """
    Removes temporary or old summary files in the Results folder
    and deletes the 'tables_png' folder if it exists.
    """
    results_dir = Path(results_dir)
    files_to_delete = ["summary0.txt", "report2.txt"]

    # Delete specific files
    for file in files_to_delete:
        path = results_dir / file
        if path.exists():
            path.unlink()
            log(f"✅ Deleted: {path}")
        else:
            log(f"⛔ Does not exist: {path}")

    # Delete the entire tables_png folder
    tables_png_dir = results_dir / "tables_png"
    if tables_png_dir.exists() and tables_png_dir.is_dir():
        shutil.rmtree(tables_png_dir)
        log(f"✅ Folder deleted: {tables_png_dir}")
    else:
        log(f"⛔ Folder does not exist: {tables_png_dir}")

def main(pdf_path, txt_path, log, output_dir=None, progress_callback=None):
    """
    Main function to clean old files and display the banner.
    """
    # Always work inside "Results"
    if output_dir:
        results_dir = Path(output_dir) / "Results"
    elif pdf_path:
        results_dir = Path(pdf_path).parent / "Results"
    else:
        results_dir = Path(__file__).resolve().parent / "Results"

    if progress_callback:
        progress_callback(0.0)

    results_dir.mkdir(parents=True, exist_ok=True)
    clean_results(results_dir, log)

    if progress_callback:
        progress_callback(1.0)
