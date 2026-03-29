"""
Google Sheets Exporter v2.0
===========================
Export data to Google Sheets.

Features:
- Export pages, posts, comments
- Append or overwrite modes
- Batch operations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try importing Google API
HAS_GSPREAD = False
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_GSPREAD = True
except ImportError:
    logger.info("gspread not installed. Install with: pip install gspread oauth2client")


class GoogleSheetsExporter:
    """
    Export scraped data to Google Sheets.
    
    Requires:
    - Service account credentials JSON
    - Sheet shared with service account email
    """
    
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
    ):
        """
        Initialize GoogleSheetsExporter.
        
        Args:
            credentials_path: Path to service account JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self._client = None
        self._spreadsheet = None
        
        if not HAS_GSPREAD:
            logger.warning("gspread not available. Export will be disabled.")
            
    def _get_client(self):
        """Get or create Google Sheets client."""
        if self._client is None and HAS_GSPREAD and self.credentials_path:
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    self.credentials_path,
                    self.SCOPES,
                )
                self._client = gspread.authorize(creds)
            except Exception as e:
                logger.error(f"Failed to create client: {e}")
                
        return self._client
        
    def _get_spreadsheet(self):
        """Get spreadsheet by ID."""
        if self._spreadsheet is None:
            client = self._get_client()
            if client and self.spreadsheet_id:
                try:
                    self._spreadsheet = client.open_by_key(self.spreadsheet_id)
                except Exception as e:
                    logger.error(f"Failed to open spreadsheet: {e}")
                    
        return self._spreadsheet
        
    def _get_or_create_worksheet(self, name: str, rows: int = 1000, cols: int = 26):
        """Get or create worksheet."""
        spreadsheet = self._get_spreadsheet()
        if not spreadsheet:
            return None
            
        try:
            return spreadsheet.worksheet(name)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
            
    def export_pages(
        self,
        pages: List[Dict],
        worksheet_name: str = "Pages",
        overwrite: bool = False,
    ) -> bool:
        """
        Export pages to worksheet.
        
        Args:
            pages: List of page dictionaries
            worksheet_name: Target worksheet name
            overwrite: Clear existing data
            
        Returns:
            True if successful
        """
        if not HAS_GSPREAD:
            logger.error("gspread not available")
            return False
            
        worksheet = self._get_or_create_worksheet(worksheet_name)
        if not worksheet:
            return False
            
        try:
            headers = ['ID', 'URL', 'Name', 'Created At', 'Post Count']
            
            rows = [headers]
            for page in pages:
                rows.append([
                    str(page.get('id', '')),
                    page.get('url', ''),
                    page.get('name', ''),
                    str(page.get('created_at', '')),
                    str(page.get('post_count', 0)),
                ])
                
            if overwrite:
                worksheet.clear()
                
            worksheet.update(range_name='A1', values=rows)
            logger.info(f"Exported {len(pages)} pages to {worksheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
            
    def export_posts(
        self,
        posts: List[Dict],
        worksheet_name: str = "Posts",
        overwrite: bool = False,
    ) -> bool:
        """
        Export posts to worksheet.
        
        Args:
            posts: List of post dictionaries
            worksheet_name: Target worksheet name
            overwrite: Clear existing data
            
        Returns:
            True if successful
        """
        if not HAS_GSPREAD:
            logger.error("gspread not available")
            return False
            
        worksheet = self._get_or_create_worksheet(worksheet_name)
        if not worksheet:
            return False
            
        try:
            headers = [
                'ID', 'Page ID', 'Facebook ID', 'Text', 'Likes', 
                'Comments', 'Shares', 'Created At', 'Scraped At', 'Sentiment'
            ]
            
            rows = [headers]
            for post in posts:
                text = post.get('text', '')
                if len(text) > 500:
                    text = text[:500] + '...'
                    
                rows.append([
                    str(post.get('id', '')),
                    str(post.get('page_id', '')),
                    post.get('facebook_id', ''),
                    text,
                    str(post.get('likes', 0)),
                    str(post.get('comments_count', 0)),
                    str(post.get('shares', 0)),
                    str(post.get('created_at', '')),
                    str(post.get('scraped_at', '')),
                    str(post.get('sentiment_score', '')),
                ])
                
            if overwrite:
                worksheet.clear()
                
            worksheet.update(range_name='A1', values=rows)
            logger.info(f"Exported {len(posts)} posts to {worksheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
            
    def export_comments(
        self,
        comments: List[Dict],
        worksheet_name: str = "Comments",
        overwrite: bool = False,
    ) -> bool:
        """
        Export comments to worksheet.
        
        Args:
            comments: List of comment dictionaries
            worksheet_name: Target worksheet name
            overwrite: Clear existing data
            
        Returns:
            True if successful
        """
        if not HAS_GSPREAD:
            logger.error("gspread not available")
            return False
            
        worksheet = self._get_or_create_worksheet(worksheet_name, rows=5000)
        if not worksheet:
            return False
            
        try:
            headers = [
                'ID', 'Post ID', 'Author', 'Text', 'Likes',
                'Created At', 'Scraped At', 'Sentiment'
            ]
            
            rows = [headers]
            for comment in comments:
                text = comment.get('text', '')
                if len(text) > 300:
                    text = text[:300] + '...'
                    
                rows.append([
                    str(comment.get('id', '')),
                    str(comment.get('post_id', '')),
                    comment.get('author', ''),
                    text,
                    str(comment.get('likes', 0)),
                    str(comment.get('created_at', '')),
                    str(comment.get('scraped_at', '')),
                    str(comment.get('sentiment_score', '')),
                ])
                
            if overwrite:
                worksheet.clear()
                
            # Batch update for large datasets
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                start_row = i + 1
                worksheet.update(range_name=f'A{start_row}', values=batch)
                
            logger.info(f"Exported {len(comments)} comments to {worksheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
            
    def export_analysis(
        self,
        analysis: Dict[str, Any],
        worksheet_name: str = "Analysis",
    ) -> bool:
        """
        Export analysis results.
        
        Args:
            analysis: Analysis results dictionary
            worksheet_name: Target worksheet name
            
        Returns:
            True if successful
        """
        if not HAS_GSPREAD:
            logger.error("gspread not available")
            return False
            
        worksheet = self._get_or_create_worksheet(worksheet_name)
        if not worksheet:
            return False
            
        try:
            worksheet.clear()
            
            rows = [
                ['Analysis Report'],
                ['Generated At', datetime.now().isoformat()],
                [''],
                ['Metric', 'Value'],
            ]
            
            # Add metrics
            for key, value in analysis.items():
                if isinstance(value, dict):
                    rows.append([key, ''])
                    for k, v in value.items():
                        rows.append([f'  {k}', str(v)])
                elif isinstance(value, list):
                    rows.append([key, str(len(value))])
                else:
                    rows.append([key, str(value)])
                    
            worksheet.update(range_name='A1', values=rows)
            logger.info(f"Exported analysis to {worksheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
            
    def append_row(
        self,
        worksheet_name: str,
        row: List[Any],
    ) -> bool:
        """
        Append a single row to worksheet.
        
        Args:
            worksheet_name: Target worksheet name
            row: Row data
            
        Returns:
            True if successful
        """
        if not HAS_GSPREAD:
            return False
            
        worksheet = self._get_or_create_worksheet(worksheet_name)
        if not worksheet:
            return False
            
        try:
            worksheet.append_row(row)
            return True
        except Exception as e:
            logger.error(f"Append failed: {e}")
            return False
            
    def get_all_data(self, worksheet_name: str) -> List[List[str]]:
        """
        Get all data from worksheet.
        
        Args:
            worksheet_name: Worksheet name
            
        Returns:
            List of rows
        """
        if not HAS_GSPREAD:
            return []
            
        worksheet = self._get_or_create_worksheet(worksheet_name)
        if not worksheet:
            return []
            
        try:
            return worksheet.get_all_values()
        except Exception as e:
            logger.error(f"Get data failed: {e}")
            return []
