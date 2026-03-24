import re
from flask import Flask, request, jsonify, render_template
from database import init_db, get_player_games, get_missed_games, get_all_team_games
from nba_client import fetch_and_store

app = Flask(__name__)
init_db()

STAT_FIELDS = {
    "points": "pts", "pts": "pts",
    "rebounds": "reb", "reb": "reb",
    "assists": "ast", "ast": "ast",
    "blocks": "blk", "blk": "blk",
    "steals": "stl", "stl": "stl",
    "threes": "fg3m", "3 pointers": "fg3m", "three pointers": "fg3m", "fg3m": "fg3m",
    "three point percentage": "fg3_pct", "3pt%": "fg3_pct",
    "field goal percentage": "fg_pct", "fg%": "fg_pct",
    "free throw percentage": "ft_pct", "ft%": "ft_pct",
}

STAT_LABELS = {
    "pts": "points", "reb": "rebounds", "ast": "assists",
    "fg3m": "3-pointers made", "fg3_pct": "3PT%",
    "blk": "blocks", "stl": "steals",
    "ft_pct": "FT%", "fg_pct": "FG%"
}


def parse_question(question: str):
    q = question.lower()
    stat_field = None
    for keyword, field in STAT_FIELDS.items():
        if keyword in q:
            stat_field = field
            break
    threshold = None
    numbers = re.findall(r'\d+\.?\d*', q)
    if numbers:
        threshold = float(numbers[0])
    return stat_field, threshold


def compute_stats(games: list[dict], stat_field: str, threshold: float = None):
    total = len(games)
    if total == 0:
        return {}
    values = [g[stat_field] for g in games if g[stat_field] is not None]
    result = {
        "total_games": total,
        "average": round(sum(values) / len(values), 2) if values else 0,
        "max": max(values) if values else 0,
        "min": min(values) if values else 0,
    }
    if threshold is not None:
        above = sum(1 for v in values if v >= threshold)
        result["threshold"] = threshold
        result["games_above"] = above
        result["frequency_pct"] = round((above / total) * 100, 1)
    return result


def split_window(team_games: list[dict], last_n: int):
    """
    Take the last_n team games, split into played vs missed.
    Returns (played_dates set, missed_in_window list).
    """
    window = team_games[:last_n] if last_n > 0 else team_games
    played_dates = {g["game_date"] for g in window if g["status"] == "played"}
    missed = [g for g in window if g["status"] == "missed"]
    return played_dates, missed


@app.route("/")
def index():
    return render_template("index.html")


PLAYER_POPULARITY = {}  # player_id -> rank, loaded at startup


def load_popularity(season: str = "2025-26"):
    """Rank all players by minutes played this season. Starters > bench > rest."""
    global PLAYER_POPULARITY
    try:
        from nba_api.stats.endpoints import leaguedashplayerstats
        import time
        time.sleep(0.6)
        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            per_mode_detailed="PerGame",
            season_type_all_star="Regular Season"
        )
        df = stats.get_data_frames()[0]
        df = df.sort_values("MIN", ascending=False).reset_index(drop=True)
        PLAYER_POPULARITY = {int(row["PLAYER_ID"]): idx for idx, row in df.iterrows()}
        print(f"Loaded popularity for {len(PLAYER_POPULARITY)} players.")
    except Exception as e:
        print(f"Could not load popularity rankings: {e}")


load_popularity()


@app.route("/api/players")
def player_suggestions():
    query = request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return jsonify([])

    from nba_api.stats.static import players as nba_players
    all_players = nba_players.get_players()

    matches = [p for p in all_players if query in p["full_name"].lower()]
    # Sort: minutes-based rank first, then active, then alphabetical
    matches.sort(key=lambda p: (
        PLAYER_POPULARITY.get(p["id"], 9999),
        not p["is_active"],
        p["full_name"]
    ))
    return jsonify([p["full_name"] for p in matches[:10]])


@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    player_name = data.get("player", "").strip()
    season = data.get("season", "2025-26")

    if not player_name:
        return jsonify({"error": "Player name required."}), 400

    full_name, err = fetch_and_store(player_name, season)
    if err:
        return jsonify({"error": err}), 404

    games = get_player_games(full_name, season)
    missed = get_missed_games(full_name, season)
    return jsonify({
        "player": full_name,
        "games_loaded": len(games),
        "missed_games_total": len(missed)
    })


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json
    player_name = data.get("player", "").strip()
    question = data.get("question", "").strip()
    season = data.get("season", "2025-26")
    last_n = int(data.get("last_n", 0))  # 0 = all games

    if not player_name or not question:
        return jsonify({"error": "Player and question are required."}), 400

    all_games = get_player_games(player_name, season)
    if not all_games:
        return jsonify({"error": f"No data for {player_name}. Search them first."}), 404

    if last_n > 0:
        # Use team schedule to define the window (played + missed combined)
        team_games = get_all_team_games(player_name, season)
        played_dates, missed_in_window = split_window(team_games, last_n)
        games = [g for g in all_games if g["game_date"] in played_dates]
    else:
        games = all_games
        missed_in_window = []

    stat_field, threshold = parse_question(question)
    if not stat_field:
        return jsonify({"error": "Couldn't understand the stat. Try mentioning points, rebounds, assists, etc."}), 400

    stats = compute_stats(games, stat_field, threshold)
    stat_label = STAT_LABELS.get(stat_field, stat_field)

    scope = f"last {last_n} games" if last_n > 0 else "this season"
    answer_parts = [
        f"{player_name} averages {stats['average']} {stat_label} per game over {stats['total_games']} games ({scope}).",
        f"High: {stats['max']} | Low: {stats['min']}."
    ]
    if threshold is not None:
        answer_parts.append(
            f"He hit {threshold}+ {stat_label} in {stats['games_above']} of {stats['total_games']} games ({stats['frequency_pct']}% of the time)."
        )

    injury_warning = None
    if last_n > 0 and missed_in_window:
        injury_warning = (
            f"⚠️ {player_name} missed {len(missed_in_window)} game(s) during this {last_n}-game window "
            f"(DNP/Injury). Stats reflect only {len(games)} played games."
        )

    return jsonify({
        "answer": " ".join(answer_parts),
        "stats": stats,
        "injury_warning": injury_warning,
        "missed_games": [m["game_date"] + " " + m["matchup"] for m in missed_in_window]
    })


if __name__ == "__main__":
    app.run(debug=True)
