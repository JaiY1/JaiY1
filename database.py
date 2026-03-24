import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nba_stats.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            player_name TEXT,
            season TEXT,
            game_date TEXT,
            matchup TEXT,
            pts INTEGER,
            reb INTEGER,
            ast INTEGER,
            fg3m INTEGER,
            fg3_pct REAL,
            blk INTEGER,
            stl INTEGER,
            ft_pct REAL,
            fg_pct REAL
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_player_game
        ON player_games (player_id, game_date)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS missed_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            player_name TEXT,
            season TEXT,
            game_date TEXT,
            matchup TEXT
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_missed_game
        ON missed_games (player_id, game_date)
    """)
    conn.commit()
    conn.close()


def upsert_games(games: list[dict]):
    conn = get_conn()
    conn.executemany("""
        INSERT OR REPLACE INTO player_games
            (player_id, player_name, season, game_date, matchup,
             pts, reb, ast, fg3m, fg3_pct, blk, stl, ft_pct, fg_pct)
        VALUES
            (:player_id, :player_name, :season, :game_date, :matchup,
             :pts, :reb, :ast, :fg3m, :fg3_pct, :blk, :stl, :ft_pct, :fg_pct)
    """, games)
    conn.commit()
    conn.close()


def upsert_missed_games(games: list[dict]):
    conn = get_conn()
    conn.executemany("""
        INSERT OR IGNORE INTO missed_games
            (player_id, player_name, season, game_date, matchup)
        VALUES
            (:player_id, :player_name, :season, :game_date, :matchup)
    """, games)
    conn.commit()
    conn.close()


def get_player_games(player_name: str, season: str = None):
    conn = get_conn()
    query = "SELECT * FROM player_games WHERE LOWER(player_name) = LOWER(?)"
    params = [player_name]
    if season:
        query += " AND season = ?"
        params.append(season)
    query += " ORDER BY game_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_missed_games(player_name: str, season: str = None):
    conn = get_conn()
    query = "SELECT * FROM missed_games WHERE LOWER(player_name) = LOWER(?)"
    params = [player_name]
    if season:
        query += " AND season = ?"
        params.append(season)
    query += " ORDER BY game_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_team_games(player_name: str, season: str = None):
    """Return all team games (played + missed) merged, sorted by date DESC."""
    conn = get_conn()
    params = [player_name, player_name]
    season_clause = ""
    if season:
        season_clause = "AND season = ?"
        params = [player_name, season, player_name, season]

    query = f"""
        SELECT game_date, matchup, 'played' as status FROM player_games
        WHERE LOWER(player_name) = LOWER(?) {season_clause}
        UNION ALL
        SELECT game_date, matchup, 'missed' as status FROM missed_games
        WHERE LOWER(player_name) = LOWER(?) {season_clause}
        ORDER BY game_date DESC
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
