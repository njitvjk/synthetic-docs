import os
import random
from pathlib import Path

from generate_documents import generate_invoices_multi_page, generate_contracts_multi_page


OUTPUT_DIR = Path("output/small")
INV_DIR = OUTPUT_DIR / "invoices"
CON_DIR = OUTPUT_DIR / "contracts"


def ensure_dirs():
    INV_DIR.mkdir(parents=True, exist_ok=True)
    CON_DIR.mkdir(parents=True, exist_ok=True)


def filesize(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def human(n: int) -> str:
    # simple human readable
    for unit in ["B", "KB", "MB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def main(request_each: int = 10, max_total_bytes: int = 7 * 1024 * 1024):
    """Generate up to request_each invoice and contract files (each 2-3 pages),
    but ensure the total size of created files stays under max_total_bytes.
    """
    ensure_dirs()

    # create one sample of each with 3 pages to estimate size
    sample_inv = INV_DIR / "_sample_invoice.pdf"
    sample_con = CON_DIR / "_sample_contract.pdf"
    generate_invoices_multi_page(str(sample_inv), pages=3)
    generate_contracts_multi_page(str(sample_con), pages=3)

    inv_size = filesize(sample_inv)
    con_size = filesize(sample_con)
    avg_size = (inv_size + con_size) / 2 if (inv_size and con_size) else max(inv_size, con_size, 1)

    # compute how many of each we can safely create
    max_files_total = max(1, int(max_total_bytes // avg_size))
    max_each = max(1, max_files_total // 2)
    count_each = min(request_each, max_each)

    print(f"Estimated sizes: invoice={human(inv_size)}, contract={human(con_size)}, avg={human(int(avg_size))}")
    print(f"Targeting {count_each} invoices and {count_each} contracts (<= {human(max_total_bytes)})")

    # remove sample files
    try:
        sample_inv.unlink()
        sample_con.unlink()
    except Exception:
        pass

    # generate files, pages randomly 2 or 3
    for i in range(1, count_each + 1):
        pages = random.choice([2, 3])
        inv_path = INV_DIR / f"invoice_{i:03d}.pdf"
        generate_invoices_multi_page(str(inv_path), pages=pages)
        con_path = CON_DIR / f"contract_{i:03d}.pdf"
        pages2 = random.choice([2, 3])
        generate_contracts_multi_page(str(con_path), pages=pages2)

    # summarize
    all_files = list(INV_DIR.glob("*.pdf")) + list(CON_DIR.glob("*.pdf"))
    total = sum(f.stat().st_size for f in all_files)
    print(f"Created {len(all_files)} files, total size {human(total)}")
    print(f"Invoices in: {INV_DIR.resolve()}")
    print(f"Contracts in: {CON_DIR.resolve()}")


if __name__ == "__main__":
    main(request_each=10)