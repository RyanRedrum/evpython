import requests
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import quote  # Import for URL encoding

class OddsApiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/"
        self.headers = {
            'Accept': 'application/json'
        }

    def fetch_odds(self, regions='us', markets='h2h', odds_format='american', bookmakers='draftkings', use_sample_data=False):
        """
        Fetch odds from the API or return sample data if use_sample_data is True.
        Parse the response into an array of standard types with specific properties.
        Filter games to only include those with a start time of today or the earliest date in the sample file.
        """
        if use_sample_data:
            # Load and return data from the sample JSON file
            try:
                with open('sample_odds_api_response.json', 'r') as file:
                    data = json.load(file)
                # Determine the earliest date in the sample data
                earliest_date = min(
                    datetime.fromisoformat(game['commence_time'].replace("Z", "+00:00")).date()
                    for game in data
                )
            except FileNotFoundError:
                raise Exception("Sample data file 'sample_odds_api_response.json' not found.")
            except json.JSONDecodeError:
                raise Exception("Error decoding JSON from 'sample_odds_api_response.json'.")
        else:
            # Calculate 6 AM tomorrow in UTC
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            commence_time_to = datetime(
                year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=6, tzinfo=timezone.utc
            )

            # Format commence_time_to as YYYY-MM-DDTHH:MM:SSZ
            commence_time_to_formatted = commence_time_to.strftime("%Y-%m-%dT%H:%M:%SZ")

            # URL encode the commenceTimeTo parameter
            commence_time_to_encoded = quote(commence_time_to_formatted)

            # Add the commenceTimeTo parameter to the API URL
            url = f"{self.base_url}?regions={regions}&markets={markets}&oddsFormat={odds_format}&bookmakers={bookmakers}&commenceTimeTo={commence_time_to_encoded}&apiKey={self.api_key}"
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()  # Raise an error for bad HTTP responses
                data = response.json()  # Return the structured JSON data
            except requests.exceptions.RequestException as e:
                raise Exception(f"API request failed: {e}")

        # Parse the JSON data into the desired format
        parsed_data = []
        for game in data:
            try:
                game_id = game.get('id')
                start_time = game.get('commence_time')
                home_team = game.get('home_team')
                away_team = game.get('away_team')

                # Convert start_time to a datetime object
                start_time_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

                # Extract odds for the home and away teams
                home_team_odds = None
                away_team_odds = None
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':  # Head-to-head market
                            outcomes = market.get('outcomes', [])
                            for outcome in outcomes:
                                if outcome.get('name') == home_team:
                                    home_team_odds = outcome.get('price')
                                elif outcome.get('name') == away_team:
                                    away_team_odds = outcome.get('price')

                # Append the parsed game data to the list
                parsed_data.append({
                    'game_id': game_id,
                    'start_time': start_time_dt.isoformat(),  # Full UTC datetime
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_team_odds': home_team_odds,
                    'away_team_odds': away_team_odds
                })
            except Exception as e:
                # Handle any parsing errors for individual games
                print(f"Error parsing game data: {e}")

        return parsed_data
