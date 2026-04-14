from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    ui_path = Path(__file__).with_name("ui.py")
    sys.argv = [
        "streamlit",
        "run",
        str(ui_path),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
