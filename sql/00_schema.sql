-- ============================================================
--  Schema — football relational dataset
-- ============================================================
--  Applied by db_setup.py as a single batch, exactly as written.
--  Tables are ordered parent-before-child so foreign keys resolve
--  without violations, and dropped in reverse for the same reason.
--
--  The DROP statements make this file safe to re-apply to an
--  existing database (db_setup.py with RECREATE_DB = False).
-- ============================================================

DROP TABLE IF EXISTS game_events CASCADE;
DROP TABLE IF EXISTS appearances CASCADE;
DROP TABLE IF EXISTS games       CASCADE;
DROP TABLE IF EXISTS players     CASCADE;
DROP TABLE IF EXISTS clubs       CASCADE;
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
    appearance_id  varchar(16) not null    primary key,
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
