"""Live-stats tools for the stats agent.

LangChain `@tool` functions over `nba_api`, normalized to small dicts. This mirrors
the companion `nba-mcp-server` project; when `NBA_SCOUT_MCP_SERVER_URL` is set the
plan is to load those same tools over MCP instead (see roadmap).
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_TIMEOUT = 30


def _pct(v: Any) -> float | None:
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return None


@tool
def find_player(name: str) -> dict[str, Any]:
    """Resolve an NBA player name to a player_id. Call this before player_career_stats."""
    from nba_api.stats.static import players

    matches = players.find_players_by_full_name(name)
    if not matches:
        return {"error": f"no player matching {name!r}"}
    p = matches[0]
    return {"player_id": p["id"], "name": p["full_name"], "is_active": p["is_active"]}


@tool
def player_career_stats(player_id: int) -> dict[str, Any]:
    """Career regular-season and playoff averages for a player.

    Needs player_id from find_player.
    """
    from nba_api.stats.endpoints import playercareerstats

    data = playercareerstats.PlayerCareerStats(
        player_id=player_id, timeout=_TIMEOUT
    ).get_normalized_dict()

    def totals(key: str) -> dict[str, Any] | None:
        rows = data.get(key) or []
        if not rows:
            return None
        r = rows[0]
        gp = r["GP"] or 1
        return {
            "games": r["GP"],
            "ppg": round((r["PTS"] or 0) / gp, 1),
            "rpg": round((r["REB"] or 0) / gp, 1),
            "apg": round((r["AST"] or 0) / gp, 1),
            "fg_pct": _pct(r["FG_PCT"]),
            "fg3_pct": _pct(r["FG3_PCT"]),
        }

    return {
        "regular_season": totals("CareerTotalsRegularSeason"),
        "playoffs": totals("CareerTotalsPostSeason"),
    }


@tool
def stat_leaders(season: str, stat: str = "points", limit: int = 5) -> list[dict[str, Any]]:
    """Per-game league leaders for a season (e.g. season='2023-24').

    stat: points, rebounds, assists, steals, blocks, three_pointers.
    """
    from nba_api.stats.endpoints import leaguedashplayerstats

    field = {
        "points": "PTS", "rebounds": "REB", "assists": "AST",
        "steals": "STL", "blocks": "BLK", "three_pointers": "FG3M",
    }.get(stat)
    if field is None:
        return [{"error": f"unknown stat {stat!r}"}]

    rows = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="PerGame", timeout=_TIMEOUT
    ).get_normalized_dict()["LeagueDashPlayerStats"]
    rows.sort(key=lambda r: r.get(field) or 0, reverse=True)
    return [
        {"rank": i + 1, "player": r["PLAYER_NAME"], "team": r["TEAM_ABBREVIATION"],
         "value": round(r[field] or 0, 1)}
        for i, r in enumerate(rows[: min(limit, 25)])
    ]


@tool
def league_standings(season: str) -> dict[str, list[dict[str, Any]]]:
    """Standings by conference for a season (e.g. season='2023-24')."""
    from nba_api.stats.endpoints import leaguestandingsv3

    rows = leaguestandingsv3.LeagueStandingsV3(
        season=season, timeout=_TIMEOUT
    ).get_normalized_dict()["Standings"]
    out: dict[str, list[dict[str, Any]]] = {"East": [], "West": []}
    for r in rows:
        out[r["Conference"]].append(
            {"rank": r["PlayoffRank"], "team": f"{r['TeamCity']} {r['TeamName']}",
             "wins": r["WINS"], "losses": r["LOSSES"]}
        )
    for teams in out.values():
        teams.sort(key=lambda x: x["rank"])
    return out


def get_stats_tools() -> list:
    """The tool list bound to the stats agent."""
    return [find_player, player_career_stats, stat_leaders, league_standings]
