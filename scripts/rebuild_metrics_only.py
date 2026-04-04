import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import derive_player_layers as d


def main() -> None:
    read_connection = sqlite3.connect(f"file:{d.SOURCE_DB_PATH}?mode=ro", uri=True)
    write_connection = sqlite3.connect(d.OUTPUT_DB_PATH)
    write_connection.execute("DROP TABLE IF EXISTS player_derived_metrics")
    write_connection.execute(d.PLAYER_DERIVED_METRICS_SQL)
    write_connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_derived_scope ON player_derived_metrics(player_name, scope)"
    )
    write_connection.commit()
    d.derive_player_metrics(read_connection, write_connection)
    count = write_connection.execute("SELECT COUNT(*) FROM player_derived_metrics").fetchone()[0]
    print(f"player_derived_metrics={count}")
    read_connection.close()
    write_connection.close()


if __name__ == "__main__":
    main()
