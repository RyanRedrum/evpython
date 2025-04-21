import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class SpreadsheetClient:
    def __init__(self, credentials_file):
        """Initialize the SpreadsheetClient with the path to the credentials file."""
        self.credentials_file = credentials_file
        self.client = self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API using the service account credentials."""
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
        return gspread.authorize(credentials)

    def update_sheet(self, spreadsheet_name, data):
        """Create a new worksheet named with today's date as a duplicate of the 'template' worksheet."""
        try:
            # Open the spreadsheet
            spreadsheet = self.client.open(spreadsheet_name)

            # Get today's date as a string (e.g., "2025-04-21")
            today_date = datetime.now().strftime("%Y-%m-%d")

            # Check if a worksheet with today's date already exists
            worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if today_date in worksheet_titles:
                # Delete the existing worksheet
                worksheet_to_delete = spreadsheet.worksheet(today_date)
                spreadsheet.del_worksheet(worksheet_to_delete)

            # Find the 'template' worksheet
            template_worksheet = spreadsheet.worksheet("Template")

            # Duplicate the 'template' worksheet and rename it to today's date
            new_worksheet = template_worksheet.duplicate(new_sheet_name=today_date)

            # Prepare the data for insertion
            rows = []
            for game in data:
                # Add the away team row
                rows.append([
                    game['game_id'],  # Column A: Game ID (only for the first row)
                    game['start_time'],  # Column B: Start Time (only for the first row)
                    game['away_team'],  # Column C: Away Team
                    game['away_team_odds'],  # Column D: Away Team Odds
                    game['away_team_win_percentage']  # Column E: Away Team Win Percentage
                ])
                # Add the home team row
                rows.append([
                    "",  # Column A: Empty for the second row
                    "",  # Column B: Empty for the second row
                    game['home_team'],  # Column C: Home Team
                    game['home_team_odds'],  # Column D: Home Team Odds
                    game['home_team_win_percentage']  # Column E: Home Team Win Percentage
                ])

            # Calculate the starting row and ensure the table has enough rows
            start_row = 16
            existing_rows = len(new_worksheet.get_all_values())
            # Subtract 1 from the required rows since the first row already exists
            required_rows = start_row + len(rows) - existing_rows - 1
            if required_rows > 0:
                # Add empty rows to ensure the table has enough space
                new_worksheet.add_rows(required_rows)

            # Update the worksheet with the data starting at row 16
            cell_range = f"A{start_row}:E{start_row + len(rows) - 1}"
            new_worksheet.update(cell_range, rows)
            print(f"Spreadsheet '{spreadsheet_name}' updated successfully with worksheet '{today_date}'.")
        except Exception as e:
            print(f"Failed to update Google Sheet: {e}")