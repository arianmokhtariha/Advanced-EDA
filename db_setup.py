import psycopg2
from psycopg2 import sql
import pandas as pd
from pathlib import Path
from db_config import DB_CONFIG, DB_CONFIG_INIT


# Note: Only change SCHEMA_SQL and CSV_TABLE_MAPPING for different projects 

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
# (Important) Ordered by dependency to ensure parent records exist before child records
CSV_TABLE_MAPPING = {
    r"data/competitions.csv" : "competitions",
    r"data/clubs.csv" : "clubs",
    r"data/players.csv" : "players",
    r"data/games.csv" : "games",
    r"data/appearances.csv" : "appearances",
    r"data/game_events.csv" : "game_events"
}

# ============================================
# FUNCTIONS (no need to modify)
# ============================================

def create_database(db_name, config_init):
    """Create PostgreSQL database if it doesn't exist."""
    conn = psycopg2.connect(**config_init)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name)
        ))
        print(f"✅ Database '{db_name}' created.")
    except psycopg2.errors.DuplicateDatabase:
        print(f"ℹ️  Database '{db_name}' already exists.")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_schema(schema_sql, config):
    """Execute schema SQL to create tables."""
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Schema created successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Schema creation failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def load_csv_to_table(csv_path, table_name, config):
    """Load CSV file into PostgreSQL table using COPY."""
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        print(f"⚠️  CSV file not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print(f"⚠️  CSV file is empty: {csv_path}")
        return
    
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    
    try:
        # Convert DataFrame to tab-separated string for COPY
        # float_format='%.0f' prevents integers with NaNs from being exported as '186.0'
        output = df.to_csv(index=False, header=False, sep='\t', na_rep='\\N', float_format='%.0f')
        
        cursor.copy_from(
            file=pd.io.common.StringIO(output),
            table=table_name,
            sep='\t',
            null='\\N',
            columns=df.columns.tolist()
        )
        conn.commit()
        print(f"✅ Loaded {len(df)} rows into '{table_name}' from {csv_path.name}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to load {csv_path}: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def load_all_csvs(csv_mapping, config):
    """Load multiple CSVs based on mapping."""
    for csv_path, table_name in csv_mapping.items():
        load_csv_to_table(csv_path, table_name, config)

def run_setup():
    """Main setup function: create DB, schema, and load CSVs."""
    print("=" * 50)
    print("DATABASE SETUP")
    print("=" * 50)
    
    # Step 1: Create database
    create_database(DB_CONFIG['dbname'], DB_CONFIG_INIT)
    
    # Step 2: Create schema
    create_schema(SCHEMA_SQL, DB_CONFIG)
    
    # Step 3: Load CSVs
    if CSV_TABLE_MAPPING:
        load_all_csvs(CSV_TABLE_MAPPING, DB_CONFIG)
    else:
        print("ℹ️  No CSV files to load (CSV_TABLE_MAPPING is empty).")
    
    print("=" * 50)
    print("✅ Setup complete!")
    print("=" * 50)

if __name__ == "__main__":
    run_setup()
