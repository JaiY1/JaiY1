from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, teamgamelog
from database import upsert_games, upsert_missed_games
from datetime import datetime
import time


def to_iso(date_str: str) -> str:
    """Convert 'Mar 23, 2026' -> '2026-03-23' for proper sorting/comparison."""
    return datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")


def find_player(name: str):
    matches = players.find_players_by_full_name(name)
    if not matches:
        all_players = players.get_players()
        matches = [p for p in all_players if name.lower() in p["full_name"].lower()]
    return matches[0] if matches else None


def get_team_id(abbreviation: str):
    match = teams.find_team_by_abbreviation(abbreviation)
    return match["id"] if match else None


def fetch_and_store(player_name: str, season: str = "2025-26"):
    player = find_player(player_name)
    if not player:
        return None, f"Player '{player_name}' not found."

    time.sleep(0.6)
    log = playergamelog.PlayerGameLog(
        player_id=player["id"],
        season=season,
        season_type_all_star="Regular Season"
    )
    df = log.get_data_frames()[0]

    if df.empty:
        return player["full_name"], "No game data found for this season."

    # Player's team abbreviation is always first 3 chars of MATCHUP
    team_abbrev = df.iloc[0]["MATCHUP"][:3]
    team_id = get_team_id(team_abbrev)

    games = []
    played_dates = set()
    for _, row in df.iterrows():
        iso_date = to_iso(row["GAME_DATE"])
        played_dates.add(iso_date)
        games.append({
            "player_id": player["id"],
            "player_name": player["full_name"],
            "season": season,
            "game_date": iso_date,
            "matchup": row["MATCHUP"],
            "pts": int(row["PTS"]),
            "reb": int(row["REB"]),
            "ast": int(row["AST"]),
            "fg3m": int(row["FG3M"]),
            "fg3_pct": float(row["FG3_PCT"]) if row["FG3_PCT"] else 0.0,
            "blk": int(row["BLK"]),
            "stl": int(row["STL"]),
            "ft_pct": float(row["FT_PCT"]) if row["FT_PCT"] else 0.0,
            "fg_pct": float(row["FG_PCT"]) if row["FG_PCT"] else 0.0,
        })

    upsert_games(games)

    # Fetch team schedule to find missed games
    if team_id:
        time.sleep(0.6)
        team_log = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        team_df = team_log.get_data_frames()[0]

        missed = []
        for _, row in team_df.iterrows():
            iso_date = to_iso(row["GAME_DATE"])
            if iso_date not in played_dates:
                missed.append({
                    "player_id": player["id"],
                    "player_name": player["full_name"],
                    "season": season,
                    "game_date": iso_date,
                    "matchup": row["MATCHUP"],
                })
        upsert_missed_games(missed)

    return player["full_name"], None
