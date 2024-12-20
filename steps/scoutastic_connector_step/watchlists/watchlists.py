import os
import json
import time
import logging
from typing import List, Dict
from connector import ScoutasticConnector
import orchest
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


def get_watchlists_data(connector: ScoutasticConnector) -> List[Dict]:
    """
    Fetches all watchlists and their associated players from the Scoutastic API.
    """
    logger.info("Fetching watchlists data")
    all_watchlists = []

    try:
        response = connector.fetch_data(endpoint="watchlists")
        if not response:
            logger.warning("No watchlists found.")
            return all_watchlists

        watchlists = response
    except Exception as e:
        logger.error(f"Error fetching watchlists: {e}")
        return all_watchlists

    for watchlist in watchlists:
        watch_id = watchlist.get("id")
        watch_name = watchlist.get("name", "Unknown")
        watch_owner = watchlist.get("owner", "Unknown")

        logger.info(f"Fetching players for watchlist {
                    watch_id} ({watch_name})")

        try:
            players_response = connector.fetch_data(
                endpoint=f"watchlists/{watch_id}/players")
            players = players_response.get("players", [])
        except Exception as e:
            logger.error(f"Error fetching players for watchlist {
                         watch_id}: {e}")
            players = []

        player_data = []
        for player in players:
            player_info = {
                "Player": f"{player.get('firstName', '')} {player.get('lastName', '')}".strip(),
                "Player Known Name": player.get("alias", ""),
                "Positions": [
                    pos["positions"][0]["color"]
                    if "positionsWithColors" in player and len(player["positionsWithColors"]) > 0 and "positions" in player["positionsWithColors"][-1]
                    else ""
                    for pos in player.get("positionsWithColors", [])
                ],
                "Colors": player.get("positions", []),
                "PlayerId": player.get("playerId"),
                "PlayerIdSct": player.get("id"),
            }
            player_data.append(player_info)

        all_watchlists.append({
            "id": watch_id,
            "name": watch_name,
            "owner": watch_owner,
            "players": player_data,
        })

    logger.info(f"Total watchlists collected: {len(all_watchlists)}")
    return all_watchlists


def save_to_json_file(all_watchlists):
    """
    Saves watchlist data to a JSON file.
    """
    with open("all_watchlists_data.json", "w") as f:
        json.dump(all_watchlists, f)


def orchest_handler():
    """
    Orchest step handler for extracting watchlist data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")

    if not auth_token or not team_identifier:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN or team_identifier")

    logger.info(f"Parameters received - team_identifier: {team_identifier}")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    watchlists = get_watchlists_data(connector)
    if not watchlists:
        logger.warning("No watchlist data found. Nothing to save.")
        return

    save_to_json_file(watchlists)


def script_handler():
    """
    Script handler for standalone execution.
    """
    logger.info("Running as standalone script")

    if len(sys.argv) != 2:
        raise ValueError("Please provide configuration JSON as an argument")

    config = json.loads(sys.argv[1])

    auth_token = config.get("auth_token")
    team_identifier = config.get("team_identifier")

    if not auth_token or not team_identifier:
        raise ValueError(
            "Missing required parameters: auth_token or team_identifier")

    logger.info(f"Parameters received - team_identifier: {team_identifier}")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    watchlists = get_watchlists_data(connector)
    if not watchlists:
        logger.warning("No watchlist data found. Nothing to save.")
        return

    save_to_json_file(watchlists)


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
