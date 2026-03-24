from flask import Flask, request, jsonify, render_template
from database import init_db, get_player_games, player_exists
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


def parse_question(question: str):
    """Extract stat field and threshold from a natural language question."""
    q = question.lower()

    stat_field = None
    for keyword, field in STAT_FIELDS.items():
        if keyword in q:
            stat_field = field
            break

    threshold = None
    import re
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    player_name = data.get("player", "").strip()
    season = data.get("season", "2024-25")

    if not player_name:
        return jsonify({"error": "Player name required."}), 400

    if not player_exists(player_name):
        full_name, err = fetch_and_store(player_name, season)
        if err:
            return jsonify({"error": err}), 404
        player_name = full_name

    games = get_player_games(player_name, season)
    return jsonify({"player": player_name, "games_loaded": len(games)})


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json
    player_name = data.get("player", "").strip()
    question = data.get("question", "").strip()
    season = data.get("season", "2024-25")

    if not player_name or not question:
        return jsonify({"error": "Player and question are required."}), 400

    games = get_player_games(player_name, season)
    if not games:
        return jsonify({"error": f"No data for {player_name}. Search them first."}), 404

    stat_field, threshold = parse_question(question)
    if not stat_field:
        return jsonify({"error": "Couldn't understand the stat in your question. Try mentioning points, rebounds, assists, etc."}), 400

    stats = compute_stats(games, stat_field, threshold)

    stat_label = {
        "pts": "points", "reb": "rebounds", "ast": "assists",
        "fg3m": "3-pointers made", "fg3_pct": "3PT%",
        "blk": "blocks", "stl": "steals",
        "ft_pct": "FT%", "fg_pct": "FG%"
    }.get(stat_field, stat_field)

    answer_parts = [
        f"{player_name} averages {stats['average']} {stat_label} per game over {stats['total_games']} games this season.",
        f"High: {stats['max']} | Low: {stats['min']}."
    ]
    if threshold is not None:
        answer_parts.append(
            f"He hit {threshold}+ {stat_label} in {stats['games_above']} of {stats['total_games']} games ({stats['frequency_pct']}% of the time)."
        )

    return jsonify({"answer": " ".join(answer_parts), "stats": stats})


if __name__ == "__main__":
    app.run(debug=True)
