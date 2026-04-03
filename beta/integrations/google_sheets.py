"""
Google Sheets Integration Module
Export Facebook scraper data and analysis results to Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import os
import json


class GoogleSheetsExporter:
    """Export data to Google Sheets for easy viewing and sharing"""
    
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets connection
        
        Args:
            credentials_path: Path to Google service account JSON file
                            If None, looks for GOOGLE_SHEETS_CREDENTIALS env var or
                            'google_credentials.json' in project root
        """
        self.client = None
        self._initialize_client(credentials_path)
    
    def _initialize_client(self, credentials_path: Optional[str] = None):
        """Initialize gspread client"""
        # Find credentials file
        if credentials_path is None:
            credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        
        if credentials_path is None:
            # Look in common locations
            possible_paths = [
                Path(__file__).parent.parent / 'google_credentials.json',
                Path(__file__).parent.parent / 'service_account.json',
                Path.home() / '.google' / 'sheets_credentials.json'
            ]
            for path in possible_paths:
                if path.exists():
                    credentials_path = str(path)
                    break
        
        if credentials_path is None or not Path(credentials_path).exists():
            raise FileNotFoundError(
                "Google Sheets credentials not found. Please provide credentials_path, "
                "set GOOGLE_SHEETS_CREDENTIALS environment variable, or place "
                "'google_credentials.json' in the project root."
            )
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, 
            self.SCOPES
        )
        self.client = gspread.authorize(creds)
        print("✓ Google Sheets client initialized successfully")
    
    def _format_datetime(self, dt: Any) -> str:
        """Format datetime for spreadsheet"""
        if dt is None:
            return ""
        if isinstance(dt, str):
            return dt
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return str(dt)
    
    def export_posts(self, posts: List[Dict[str, Any]], 
                     spreadsheet_name: str,
                     analysis_data: List[Dict[str, Any]] = None) -> str:
        """
        Export posts to a Google Spreadsheet
        
        Args:
            posts: List of post dictionaries
            spreadsheet_name: Name for the spreadsheet
            analysis_data: Optional analysis results to include
            
        Returns:
            URL of the created/updated spreadsheet
        """
        # Try to open existing spreadsheet or create new one
        try:
            spreadsheet = self.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(spreadsheet_name)
            # Make it publicly viewable (optional)
            spreadsheet.share(None, perm_type='anyone', role='reader')
        
        # Create/update Posts sheet
        self._update_posts_sheet(spreadsheet, posts)
        
        # Create Analysis sheet if data provided
        if analysis_data:
            self._update_analysis_sheet(spreadsheet, analysis_data)
        
        # Create Summary sheet
        self._update_summary_sheet(spreadsheet, posts, analysis_data)
        
        return spreadsheet.url
    
    def _update_posts_sheet(self, spreadsheet, posts: List[Dict[str, Any]]):
        """Update or create Posts worksheet"""
        try:
            worksheet = spreadsheet.worksheet("Posts")
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet("Posts", rows=len(posts) + 10, cols=15)
        
        # Headers
        headers = [
            "Post ID", "Page Name", "Content", "Timestamp", 
            "Likes", "Shares", "Comments", "Post URL", "Scraped At"
        ]
        
        # Prepare data rows
        rows = [headers]
        for post in posts:
            row = [
                post.get('post_id', ''),
                post.get('page_name', ''),
                (post.get('content', '') or '')[:500],  # Truncate long content
                self._format_datetime(post.get('timestamp')),
                post.get('likes', 0),
                post.get('shares', 0),
                post.get('comment_count', 0),
                post.get('post_url', ''),
                self._format_datetime(post.get('scraped_at'))
            ]
            rows.append(row)
        
        # Update sheet
        worksheet.update(rows, value_input_option='USER_ENTERED')
        
        # Format header row
        worksheet.format('A1:I1', {
            'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    
    def _update_analysis_sheet(self, spreadsheet, analysis_data: List[Dict[str, Any]]):
        """Update or create Analysis worksheet"""
        try:
            worksheet = spreadsheet.worksheet("Analysis")
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet("Analysis", rows=len(analysis_data) + 10, cols=10)
        
        # Headers
        headers = ["Post ID", "Analysis Type", "Result", "Analyzed At"]
        
        # Prepare data rows
        rows = [headers]
        for analysis in analysis_data:
            result = analysis.get('result', {})
            result_str = json.dumps(result) if isinstance(result, dict) else str(result)
            
            row = [
                analysis.get('post_id', ''),
                analysis.get('analysis_type', ''),
                result_str[:500],  # Truncate long results
                self._format_datetime(analysis.get('analyzed_at'))
            ]
            rows.append(row)
        
        # Update sheet
        worksheet.update(rows, value_input_option='USER_ENTERED')
        
        # Format header row
        worksheet.format('A1:D1', {
            'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.3},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    
    def _update_summary_sheet(self, spreadsheet, posts: List[Dict[str, Any]], 
                              analysis_data: List[Dict[str, Any]] = None):
        """Update or create Summary worksheet"""
        try:
            worksheet = spreadsheet.worksheet("Summary")
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet("Summary", rows=30, cols=5)
        
        # Calculate statistics
        total_posts = len(posts)
        unique_pages = set(p.get('page_name', '') for p in posts)
        total_likes = sum(p.get('likes', 0) for p in posts)
        total_shares = sum(p.get('shares', 0) for p in posts)
        total_comments = sum(p.get('comment_count', 0) for p in posts)
        
        # Prepare summary data
        rows = [
            ["Facebook Scraper Data Summary", ""],
            ["Generated At", datetime.now().isoformat()],
            ["", ""],
            ["Metric", "Value"],
            ["Total Posts", total_posts],
            ["Unique Pages", len(unique_pages)],
            ["Total Likes", total_likes],
            ["Total Shares", total_shares],
            ["Total Comments", total_comments],
            ["Average Likes per Post", round(total_likes / total_posts, 2) if total_posts > 0 else 0],
            ["Average Shares per Post", round(total_shares / total_posts, 2) if total_posts > 0 else 0],
            ["Average Comments per Post", round(total_comments / total_posts, 2) if total_posts > 0 else 0],
            ["", ""],
            ["Pages Scraped:", ""]
        ]
        
        for page in sorted(unique_pages):
            page_posts = [p for p in posts if p.get('page_name') == page]
            rows.append([page, len(page_posts)])
        
        # Add sentiment analysis summary if available
        if analysis_data:
            sentiment_results = [a for a in analysis_data if a.get('analysis_type') == 'sentiment']
            if sentiment_results:
                rows.append(["", ""])
                rows.append(["Sentiment Analysis", ""])
                
                sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
                for result in sentiment_results:
                    sentiment = result.get('result', {}).get('sentiment', 'neutral')
                    if sentiment in sentiments:
                        sentiments[sentiment] += 1
                
                for sentiment, count in sentiments.items():
                    rows.append([sentiment.capitalize(), count])
        
        # Update sheet
        worksheet.update(rows, value_input_option='USER_ENTERED')
        
        # Format title
        worksheet.format('A1', {
            'textFormat': {'bold': True, 'fontSize': 14}
        })
        worksheet.format('A4:B4', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True}
        })
    
    def export_comments(self, post_id: str, comments: List[Dict[str, Any]], 
                        spreadsheet_name: str) -> str:
        """Export comments for a specific post"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(spreadsheet_name)
        
        sheet_name = f"Comments_{post_id[:20]}"
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(sheet_name, rows=len(comments) + 10, cols=8)
        
        headers = ["Comment ID", "Author", "Content", "Timestamp", "Likes", "Reply To", "Scraped At"]
        
        rows = [headers]
        for comment in comments:
            row = [
                comment.get('comment_id', ''),
                comment.get('author_name', ''),
                (comment.get('content', '') or '')[:300],
                self._format_datetime(comment.get('timestamp')),
                comment.get('likes', 0),
                comment.get('reply_to_id', ''),
                self._format_datetime(comment.get('scraped_at'))
            ]
            rows.append(row)
        
        worksheet.update(rows, value_input_option='USER_ENTERED')
        
        return spreadsheet.url
    
    def list_spreadsheets(self) -> List[Dict[str, str]]:
        """List all spreadsheets created by this service account"""
        spreadsheets = self.client.openall()
        return [
            {
                "title": s.title,
                "url": s.url,
                "id": s.id
            }
            for s in spreadsheets
        ]
    
    def append_row(self, spreadsheet_name: str, worksheet_name: str, 
                   row_data: List[Any]) -> bool:
        """Append a single row to an existing worksheet"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f"Error appending row: {e}")
            return False
    
    def create_realtime_log(self, spreadsheet_name: str = "Scraper_Log") -> str:
        """Create a spreadsheet for real-time logging during scraping"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(spreadsheet_name)
            spreadsheet.share(None, perm_type='anyone', role='reader')
        
        # Create worksheets for different log types
        worksheets = {
            "Scrape_Log": ["Timestamp", "Page", "Post ID", "Status", "Message"],
            "Errors": ["Timestamp", "Page", "Error Type", "Message"],
            "Stats": ["Timestamp", "Total Posts", "New Posts", "Errors"]
        }
        
        for sheet_name, headers in worksheets.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(sheet_name, rows=1000, cols=10)
                worksheet.update([headers], value_input_option='USER_ENTERED')
        
        return spreadsheet.url


# Convenience function
def get_sheets_exporter(credentials_path: Optional[str] = None) -> GoogleSheetsExporter:
    """Get a GoogleSheetsExporter instance"""
    return GoogleSheetsExporter(credentials_path)
