import sys
import re
import time
import threading
import itertools
import psycopg2
from psycopg2 import sql
import pandas as pd
from pathlib import Path
from db_config import DB_CONFIG, DB_CONFIG_INIT


# Personal Note: Only change SCHEMA_SQL and CSV_TABLE_MAPPING for different projects

# Schema definition: list of CREATE TABLE statements
# (Important) Ordered by dependency to avoid Foreign Key violations
SCHEMA_SQL = """
DROP TABLE IF EXISTS game_events CASCADE;
DROP TABLE IF EXISTS appearances CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS clubs CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;

CREATE TABLE competitions
(
    competition_id varchar(4)  not null    primary key,
    name           varchar(64) not null,
    type           varchar(32) not null,
    country_name   varchar(16)
);

CREATE TABLE clubs
(
    club_id                 integer     not null    primary key,
    name                    varchar(64) not null,
    domestic_competition_id varchar(4)  not null
        constraint fk_domestic_competition_id
            references competitions,
    squad_size              integer     not null,
    foreigners_number       integer     not null,
    national_team_players   integer     not null,
    stadium_name            varchar(64) not null,
    stadium_seats           integer     not null,
    net_transfer_record     varchar(16) not null
);

CREATE TABLE players
(
    player_id                integer     not null
        primary key,
    current_club_id          integer     not null
        constraint fk_current_club_id
            references clubs,
    player_code              varchar(64) not null,
    country_of_birth         varchar(32),
    city_of_birth            varchar(64),
    country_of_citizenship   varchar(32),
    date_of_birth            date,
    sub_position             varchar(32),
    position                 varchar(16),
    foot                     varchar(8),
    height_in_cm             integer,
    contract_expiration_date date
);

CREATE TABLE games
(
    game_id         integer     not null    primary key,
    competition_id  varchar(4)  not null
        constraint fk_competition_id
            references competitions,
    season          integer     not null,
    date            date        not null,
    home_club_id    integer     not null
        constraint fk_home_club_id
            references clubs,
    away_club_id    integer     not null
        constraint fk_away_club_id
            references clubs,
    home_club_goals integer     not null,
    away_club_goals integer     not null,
    stadium         varchar(64) not null,
    attendance      integer
);

CREATE TABLE appearances
(
    appearance_id  varchar(16)   not null   primary key,
    game_id        integer     not null
        constraint fk_game_id
            references games,
    player_id      integer     not null
        constraint fk_player_id
            references players,
    yellow_cards   integer     not null,
    red_cards      integer     not null,
    goals          integer     not null,
    assists        integer     not null,
    minutes_played integer     not null
);

CREATE TABLE game_events
(
    game_event_id    integer     not null    primary key,
    game_id          integer     not null
        constraint fk_game_id_1
            references games,
    minute           integer     not null,
    type             varchar(16) not null,
    player_id        integer     not null
        constraint fk_player_id
            references players,
    player_in_id     integer
        constraint fk_player_in_id
            references players,
    player_assist_id integer
        constraint fk_player_assist_id
            references players
);
"""

# CSV to table mapping: {rel_csv_path: table_name}
# (Important) Order by dependency to ensure parent records exist before child records
CSV_TABLE_MAPPING = {
    r"raw_data/competitions.csv" : "competitions",
    r"raw_data/clubs.csv"        : "clubs",
    r"raw_data/players.csv"      : "players",
    r"raw_data/games.csv"        : "games",
    r"raw_data/appearances.csv"  : "appearances",
    r"raw_data/game_events.csv"  : "game_events"
}

# ============================================
# ANSI COLOR HELPERS (no external deps)
# ============================================

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"

def _c(text, *codes):
    """Wrap text with one or more ANSI codes and reset at the end."""
    return "".join(codes) + str(text) + RESET

# ============================================
# SPINNER (pure threading, no external deps)
# ============================================

class Spinner:
    """
    Context-manager spinner that animates on a single terminal line
    while a blocking operation runs, then replaces itself with a
    success / failure icon when complete.

    Usage:
        with Spinner("Creating table players"):
            do_slow_work()
        # success → ✅  Creating table players  (done)
        # error   → ❌  Creating table players  (failed)
    """

    FRAMES   = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    INTERVAL = 0.08   # seconds between frames

    def __init__(self, message: str, indent: int = 2):
        self.message  = message
        self.indent   = " " * indent
        self._stop    = threading.Event()
        self._thread  = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                break
            sys.stdout.write(
                f"\r{self.indent}{_c(frame, CYAN)}  {self.message}{_c('...', DIM)}"
            )
            sys.stdout.flush()
            time.sleep(self.INTERVAL)

    def start(self):
        self._thread.start()
        return self

    def stop(self, success: bool = True, suffix: str = ""):
        self._stop.set()
        self._thread.join()
        icon = _c("✅", GREEN) if success else _c("❌", RED)
        tag  = _c(f"  ({suffix})", DIM) if suffix else ""
        sys.stdout.write(f"\r{self.indent}{icon}  {self.message}{tag}\n")
        sys.stdout.flush()

    # ── context-manager protocol ──────────────────────────────────────────
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # exc_type is None when the block exits cleanly
        self.stop(success=(exc_type is None))
        # Do NOT suppress exceptions — let them propagate to the caller
        return False

# ============================================
# FUNCTIONS 
# ============================================

def _print_header(title: str):
    """Print a bold section header with a surrounding box."""
    bar = "═" * 50
    print()
    print(_c(f"╔{bar}╗", BOLD, CYAN))
    print(_c(f"║  {title:<48}║", BOLD, CYAN))
    print(_c(f"╚{bar}╝", BOLD, CYAN))
    print()

def _print_section(label: str):
    """Print a dimmed step sub-header."""
    print(_c(f"\n  ── {label} {'─' * (44 - len(label))}", DIM))

def _database_exists(db_name: str, config_init: dict) -> bool:
    """Return True if the target database already exists in the Postgres cluster."""
    conn   = psycopg2.connect(**config_init)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [db_name])
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def confirm_reset(db_name: str, config_init: dict) -> None:
    """
    Warn the user that the database is about to be wiped and rebuilt from
    scratch, then wait for explicit confirmation before proceeding.

    Rollback guarantee: this function is called BEFORE any destructive
    operation.  Answering 'no' leaves the database completely untouched —
    there is nothing to roll back.
    """
    exists = _database_exists(db_name, config_init)

    if exists:
        # ── Destructive-action warning (database already exists) ───────────
        print(_c("  ╔══════════════════════════════════════════════════╗", BOLD, YELLOW))
        print(_c("  ║  ⚠️   WARNING — DESTRUCTIVE OPERATION             ║", BOLD, YELLOW))
        print(_c("  ╠══════════════════════════════════════════════════╣", BOLD, YELLOW))
        print(_c("  ║  Database : ", YELLOW) + _c(f"{db_name:<37}", BOLD, WHITE) + _c("║", YELLOW))
        print(_c("  ║                                                  ║", YELLOW))
        print(_c("  ║  The database above WILL BE PERMANENTLY          ║", YELLOW))
        print(_c("  ║  DELETED and rebuilt completely from scratch.    ║", YELLOW))
        print(_c("  ║  ALL existing data will be lost.                 ║", YELLOW))
        print(_c("  ╚══════════════════════════════════════════════════╝", BOLD, YELLOW))
    else:
        # ── First-time run (no database exists yet) ────────────────────────
        print(_c("  ╔══════════════════════════════════════════════════╗", BOLD, CYAN))
        print(_c("  ║  ℹ️   FIRST-TIME SETUP                            ║", BOLD, CYAN))
        print(_c("  ╠══════════════════════════════════════════════════╣", BOLD, CYAN))
        print(_c("  ║  Database : ", CYAN) + _c(f"{db_name:<37}", BOLD, WHITE) + _c("║", CYAN))
        print(_c("  ║                                                  ║", CYAN))
        print(_c("  ║  No existing database was found.                 ║", CYAN))
        print(_c("  ║  A fresh database will be created.               ║", CYAN))
        print(_c("  ╚══════════════════════════════════════════════════╝", BOLD, CYAN))

    print()

    try:
        answer = input(_c("  Proceed? [yes / no]  → ", BOLD)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Non-interactive environment or Ctrl-C — treat as 'no'
        answer = "no"

    print()

    if answer in ("yes", "y"):
        print(_c("  ✔  Confirmed. Starting setup...", BOLD, GREEN))
        print()
    else:
        # User declined — nothing has been modified yet, so exiting here is a
        # complete and safe rollback of the entire operation.
        print(_c("  ✖  Aborted. No changes were made.", BOLD, RED))
        print()
        sys.exit(0)

def drop_database(db_name: str, config_init: dict):
    """Drop PostgreSQL database if it exists, forcing disconnection of active sessions."""
    with Spinner(f"Dropping database '{db_name}'"):
        conn = psycopg2.connect(**config_init)
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            # Terminate all active connections to the target database before dropping.
            # Without this, DROP DATABASE will fail if any sessions are still connected.
            cursor.execute(
                sql.SQL("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """),
                [db_name]
            )
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                sql.Identifier(db_name)
            ))
        finally:
            cursor.close()
            conn.close()

def create_database(db_name: str, config_init: dict):
    """Create PostgreSQL database if it doesn't exist."""
    with Spinner(f"Creating database '{db_name}'"):
        conn = psycopg2.connect(**config_init)
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
        except psycopg2.errors.DuplicateDatabase:
            pass   # already exists — spinner will still show ✅
        finally:
            cursor.close()
            conn.close()

def _parse_drop_block(schema_sql: str) -> str:
    """Extract all DROP TABLE lines from the schema as a single SQL string."""
    lines = [
        line for line in schema_sql.splitlines()
        if line.strip().upper().startswith("DROP TABLE")
    ]
    return "\n".join(lines)

def _parse_create_statements(schema_sql: str) -> list:
    """
    Return a list of (table_name, create_sql) tuples parsed from schema_sql.
    Handles multi-line CREATE TABLE ... ; blocks.
    """
    pattern = re.compile(
        r"(CREATE\s+TABLE\s+(\w+)\s*\(.*?\);)",
        re.DOTALL | re.IGNORECASE
    )
    return [(m.group(2), m.group(1)) for m in pattern.finditer(schema_sql)]

def create_schema(schema_sql: str, config: dict):
    """
    Execute schema SQL to create tables, showing a spinner and result per table
    instead of running the entire schema as one silent batch.
    """
    conn   = psycopg2.connect(**config)
    cursor = conn.cursor()

    try:
        # ── 1. Drop existing tables (single batch) ─────────────────────────
        drop_sql = _parse_drop_block(schema_sql)
        if drop_sql:
            with Spinner("Dropping existing tables"):
                cursor.execute(drop_sql)
                conn.commit()

        # ── 2. Create each table individually so the user gets live feedback ─
        tables = _parse_create_statements(schema_sql)
        print()
        for table_name, create_sql in tables:
            with Spinner(f"Creating table  {_c(table_name, BOLD, WHITE)}"):
                cursor.execute(create_sql)
                conn.commit()

    except Exception as e:
        conn.rollback()
        print(_c(f"\n  ❌ Schema creation failed: {e}", RED))
        raise
    finally:
        cursor.close()
        conn.close()

def load_csv_to_table(csv_path: str, table_name: str, config: dict):
    """Load CSV file into PostgreSQL table using COPY, with a live spinner."""
    csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"  {_c('⚠', YELLOW)}  CSV not found — skipping: {_c(str(csv_path), DIM)}")
        return

    df = pd.read_csv(csv_path)

    if df.empty:
        print(f"  {_c('⚠', YELLOW)}  CSV is empty — skipping: {_c(csv_path.name, DIM)}")
        return

    conn    = psycopg2.connect(**config)
    cursor  = conn.cursor()
    spinner = Spinner(
        f"Loading  {_c(f'{table_name:<20}', BOLD, WHITE)}"
        f"  {_c(f'{len(df):>10,} rows', DIM)}"
    )
    spinner.start()

    try:
        # Convert DataFrame to tab-separated string for COPY
        # float_format='%.0f' prevents integers with NaNs from being exported as '186.0'
        output = df.to_csv(
            index=False, header=False, sep='\t',
            na_rep='\\N', float_format='%.0f'
        )
        cursor.copy_from(
            file=pd.io.common.StringIO(output),
            table=table_name,
            sep='\t',
            null='\\N',
            columns=df.columns.tolist()
        )
        conn.commit()
        spinner.stop(success=True, suffix=f"{len(df):,} rows loaded")

    except Exception as e:
        conn.rollback()
        spinner.stop(success=False, suffix="failed")
        print(_c(f"     → {e}", RED))
        raise
    finally:
        cursor.close()
        conn.close()

def load_all_csvs(csv_mapping: dict, config: dict):
    """Load multiple CSVs based on mapping."""
    for csv_path, table_name in csv_mapping.items():
        load_csv_to_table(csv_path, table_name, config)

def run_setup():
    """Main setup function: create DB, schema, and load CSVs."""
    _print_header("DATABASE SETUP")

    # ── Guard: warn the user and require explicit confirmation ─────────────
    # confirm_reset() is called BEFORE any destructive operation, so
    # answering 'no' guarantees zero changes to the database.
    confirm_reset(DB_CONFIG['dbname'], DB_CONFIG_INIT)

    # Step 1: Drop existing database to ensure a completely fresh start
    _print_section("Step 1 — Drop existing database")
    drop_database(DB_CONFIG['dbname'], DB_CONFIG_INIT)

    # Step 2: Create database
    _print_section("Step 2 — Create database")
    create_database(DB_CONFIG['dbname'], DB_CONFIG_INIT)

    # Step 3: Create schema (per-table spinners shown inside create_schema)
    _print_section("Step 3 — Create schema")
    create_schema(SCHEMA_SQL, DB_CONFIG)

    # Step 4: Load CSVs
    _print_section("Step 4 — Load data")
    if CSV_TABLE_MAPPING:
        print()
        load_all_csvs(CSV_TABLE_MAPPING, DB_CONFIG)
    else:
        print("  ℹ️  No CSV files to load (CSV_TABLE_MAPPING is empty).")

    # ── Done ───────────────────────────────────────────────────────────────
    print()
    print(_c("  ╔══════════════════════════════════════════════════╗", BOLD, GREEN))
    print(_c("  ║  ✅  Setup complete! Database is ready.          ║", BOLD, GREEN))
    print(_c("  ╚══════════════════════════════════════════════════╝", BOLD, GREEN))
    print()

if __name__ == "__main__":
    run_setup()