import argparse
import api_client
from mlb_game_sim_client import MLBGameSimClient
from spreadsheet_client import SpreadsheetClient
from datetime import datetime
import pytz  # Add this import for timezone handling

class EvPythonGenerator:
    def __init__(self, use_sample_data):
        self.api_key = self.get_api_key()
        self.use_sample_data = use_sample_data

    def get_api_key(self, file_path='creds/odds_api_key.txt'):
        """Reads the API key from a file."""
        try:
            with open(file_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            raise Exception(f"Error: {file_path} not found.")
        except Exception as e:
            raise Exception(f"Error reading API key: {e}")

    def generate(self):
        odds_api_client = api_client.OddsApiClient(api_key=self.api_key)
        mlb_game_sim_client = MLBGameSimClient()
        try:
            # Fetch odds data and predictions
            odds_data = odds_api_client.fetch_odds(use_sample_data=self.use_sample_data)
            predictions = mlb_game_sim_client.fetch_predictions()

            # Merge the two datasets
            merged_data = self.merge_odds_and_predictions(odds_data, predictions)

            return merged_data
        except Exception as e:
            return str(e)

    def merge_odds_and_predictions(self, odds_data, predictions):
        """Merge odds data and predictions by matching teams and start time."""
        merged_data = []
        local_tz = pytz.timezone("America/New_York")  # Replace with your desired local timezone

        for odds in odds_data:
            for prediction in predictions:
                # Extract the last word of the team names for comparison
                odds_home_team = odds['home_team'].split()[-1]
                odds_away_team = odds['away_team'].split()[-1]
                prediction_home_team = prediction['home_team'].split()[-1]
                prediction_away_team = prediction['away_team'].split()[-1]

                # Match by home team, away team, and start time
                if (
                    odds_home_team == prediction_home_team and
                    odds_away_team == prediction_away_team and
                    self.compare_times(odds['start_time'], prediction['time'])
                ):
                    # Convert start_time to local time and format it for Google Sheets
                    utc_start_time = datetime.fromisoformat(odds['start_time'].replace("Z", "+00:00"))
                    local_start_time = utc_start_time.astimezone(local_tz)
                    formatted_start_time = local_start_time.strftime("%Y-%m-%d %H:%M:%S")  # Format for Google Sheets

                    # Combine the data into a single dictionary
                    merged_data.append({
                        'game_id': odds['game_id'],
                        'start_time': formatted_start_time,  # Local time formatted for Google Sheets
                        'home_team': odds['home_team'],
                        'away_team': odds['away_team'],
                        'home_team_odds': odds['home_team_odds'],
                        'away_team_odds': odds['away_team_odds'],
                        'home_team_win_percentage': prediction['home_team_win_percentage'],
                        'away_team_win_percentage': prediction['away_team_win_percentage']
                    })
        return merged_data

    def compare_times(self, odds_time, prediction_time):
        """Compare two times to see if they match by hour and date (both in UTC)."""
        try:
            # Ensure both times are datetime objects
            odds_dt = datetime.fromisoformat(odds_time.replace("Z", "+00:00"))
            prediction_dt = datetime.fromisoformat(prediction_time.replace("Z", "+00:00"))

            # Compare the date and hour
            return odds_dt.date() == prediction_dt.date() and odds_dt.hour == prediction_dt.hour
        except ValueError:
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch odds data from the API and build EV based betting spreadsheet.')
    parser.add_argument('--use_sample_data', action='store_true', help='Use sample data instead of fetching from the API.')
    parser.add_argument('--spreadsheet_name', type=str, required=True, help='Name of the Google Sheets spreadsheet.')

    args = parser.parse_args()

    generator = EvPythonGenerator(use_sample_data=args.use_sample_data)
    merged_data = generator.generate()

    # Update the Google Sheet
    credentials_file = 'creds/googlesheetscreds.json'  # Hardcoded credentials file path
    spreadsheet_client = SpreadsheetClient(credentials_file)
    spreadsheet_client.update_sheet(args.spreadsheet_name, merged_data)
