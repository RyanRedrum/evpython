import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
import pytz 

class MLBGameSimClient:
    def __init__(self, url="https://www.mlbgamesim.com/mlb-predictions.asp?LineType=2"):
        self.url = url

    def fetch_predictions(self):
        """Fetches and parses predictions from the specified page."""
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Raise an error for bad HTTP responses
            soup = BeautifulSoup(response.text, 'html.parser')

            # Parse the predictions table
            predictions = []
            table = soup.find('table', {'class': 'table'})  # Adjust the class or ID based on the actual HTML
            if not table:
                raise Exception("Predictions table not found on the page.")

            rows = table.find_all('tr')[1:]  # Skip the header row
            local_tz = pytz.timezone("America/New_York")  # Define the local timezone
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:  # Ensure there are enough columns
                    # Extract teams using a regular expression
                    match = re.search(r"\xa0(.+) @ (.+) \xa0", cols[1].text)
                    if match:
                        away_team = match.group(1).strip()
                        home_team = match.group(2).strip()
                    else:
                        away_team = None
                        home_team = None

                    # Convert the time column to a full UTC datetime
                    game_time_str = cols[0].text.strip()  # Example: "7 PM" or "1:35 PM"

                    # Check if the time string is missing minutes and append ":00" before "PM" or "AM"
                    if re.match(r"^\d{1,2} [AP]M$", game_time_str):  # Matches "7 PM" or "12 AM"
                        game_time_str = game_time_str.replace(" AM", ":00 AM").replace(" PM", ":00 PM")

                    # Parse the time string and convert it to a datetime object
                    today = datetime.now(local_tz).date()  # Get today's date in the local timezone
                    local_game_time = local_tz.localize(
                        datetime.strptime(game_time_str, "%I:%M %p").replace(
                            year=today.year, month=today.month, day=today.day
                        )
                    )
                    utc_game_time = local_game_time.astimezone(pytz.utc)

                    # Extract the winning team and win percentage from the predicted outcome
                    predicted_outcome = cols[2].text.strip()
                    winning_team_match = re.match(r"(.+?) win", predicted_outcome)
                    winning_team = winning_team_match.group(1).strip() if winning_team_match else None

                    win_percentage_match = re.search(r"(\d+(\.\d+)?)%", predicted_outcome)
                    win_percentage = float(win_percentage_match.group(1).strip()) if win_percentage_match else None

                    # Calculate home and away team winning percentages
                    if winning_team == home_team:
                        home_team_win_percentage = win_percentage
                        away_team_win_percentage = 100 - win_percentage if win_percentage else None
                    elif winning_team == away_team:
                        away_team_win_percentage = win_percentage
                        home_team_win_percentage = 100 - win_percentage if win_percentage else None
                    else:
                        home_team_win_percentage = None
                        away_team_win_percentage = None

                    predictions.append({
                        'time': utc_game_time.isoformat(),  # Full UTC datetime
                        'home_team': home_team,  # Home team
                        'away_team': away_team,  # Away team
                        'home_team_win_percentage': home_team_win_percentage,  # Home team win percentage
                        'away_team_win_percentage': away_team_win_percentage  # Away team win percentage
                    })

            return predictions
        except Exception as e:
            raise Exception(f"Failed to fetch predictions: {e}")