from f21_core_logging import setup_logging
from f22_core_db import fetch_one, init_db


def main() -> None:
    setup_logging()
    init_db()
    row = fetch_one("SELECT 1 AS ok")
    print({"db_ok": bool(row and row["ok"] == 1)})


if __name__ == "__main__":
    main()