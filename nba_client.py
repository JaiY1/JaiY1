from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from database import upsert_games
import time


def find_player(name: str):
    matches = players.find_players_by_full_name(name)
    if not matches:
        # Try partial match
        all_players = players.get_players()
        matches = [p for p in all_players if name.lower() in p["full_name"].lower()]
    return matches[0] if matches else None


def fetch_and_store(player_name: str, season: str = "2024-25"):
    player = find_player(player_name)
    if not player:
        return None, f"Player '{player_name}' not found."

    time.sleep(0.6)  # respect NBA.com rate limit
    log = playergamelog.PlayerGameLog(
        player_id=player["id"],
        season=season,
        season_type_all_star="Regular Season"
    )
    df = log.get_data_frames()[0]

    if df.empty:
        return player["full_name"], "No game data found for this season."

    games = []
    for _, row in df.iterrows():
        games.append({
            "player_id": player["id"],
            "player_name": player["full_name"],
            "season": season,
            "game_date": row["GAME_DATE"],
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
    return player["full_name"], None
