```mermaid
classDiagram
direction BT
class appearances {
   integer game_id
   integer player_id
   integer yellow_cards
   integer red_cards
   integer goals
   integer assists
   integer minutes_played
   varchar(16) appearance_id
}
class clubs {
   varchar(64) name
   varchar(4) domestic_competition_id
   integer squad_size
   integer foreigners_number
   integer national_team_players
   varchar(64) stadium_name
   integer stadium_seats
   varchar(16) net_transfer_record
   numeric numeric_net_transfer_record
   numeric(4,3) win_rate
   numeric(5,2) goals_scored_per_game
   numeric(5,2) goals_conceded_per_game
   numeric(5,2) goal_difference_per_game
   numeric(10,1) avg_attendance
   integer total_games
   numeric(4,3) home_win_rate
   numeric(4,3) away_win_rate
   numeric(4,3) clean_sheet_rate
   numeric(4,2) points_per_game
   numeric(4,3) foreigners_ratio
   numeric(4,3) national_team_players_ratio
   integer club_id
}
class competitions {
   varchar(64) name
   varchar(32) type
   varchar(16) country_name
   varchar(4) competition_id
}
class game_events {
   integer game_id
   integer minute
   varchar(16) type
   integer player_id
   integer player_in_id
   integer player_assist_id
   integer game_event_id
}
class games {
   varchar(4) competition_id
   integer season
   date date
   integer home_club_id
   integer away_club_id
   integer home_club_goals
   integer away_club_goals
   varchar(64) stadium
   integer attendance
   integer total_goals
   integer goal_difference
   boolean is_draw
   boolean home_win
   boolean away_win
   integer game_id
}
class players {
   integer current_club_id
   varchar(64) player_code
   varchar(32) country_of_birth
   varchar(64) city_of_birth
   varchar(32) country_of_citizenship
   date date_of_birth
   varchar(32) sub_position
   varchar(16) position
   varchar(8) foot
   integer height_in_cm
   date contract_expiration_date
   integer age
   numeric(4,1) contract_years_remaining
   numeric(5,2) goals_per_90
   numeric(5,2) assists_per_90
   numeric(5,2) goal_contributions_per_90
   numeric(4,3) minutes_played_ratio
   numeric(5,2) cards_per_90
   integer total_appearances
   integer total_minutes_played
   integer player_id
}

appearances  -->  games : game_id
appearances  -->  players : player_id
clubs  -->  competitions : domestic_competition_id:competition_id
game_events  -->  games : game_id
game_events  -->  players : player_in_id:player_id
game_events  -->  players : player_id
game_events  -->  players : player_assist_id:player_id
games  -->  clubs : away_club_id:club_id
games  -->  clubs : home_club_id:club_id
games  -->  competitions : competition_id
players  -->  clubs : current_club_id:club_id
```