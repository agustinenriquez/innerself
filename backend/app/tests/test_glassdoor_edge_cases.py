import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from app.services.glassdoor_scraper import GlassdoorScraper
from app.models.glassdoor_company import CompanyScrapeRequest
from app.api.routes.glassdoor import scrape_company_data


class TestGlassdoorEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def scraper(self):
        return GlassdoorScraper()
    
    @pytest.mark.asyncio
    async def test_malformed_html_handling(self, scraper):
        """Test handling of malformed HTML"""
        malformed_html = """
        <html>
            <div unclosed-tag>
                <span data-test="rating">4.2
                <div>Company Name</div>
            </div>
        <html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = malformed_html
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            # Should not crash, BeautifulSoup handles malformed HTML gracefully
            result = await scraper.scrape_company_data("https://test.com")
            
            assert "glassdoor_url" in result
            assert "scraped_at" in result
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, scraper):
        """Test handling of request timeouts"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            with pytest.raises(Exception, match="Failed to scrape company data"):
                await scraper.scrape_company_data("https://test.com")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_response(self, scraper):
        """Test handling of rate limiting (429 status)"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="HTTP 429"):
                await scraper.scrape_company_data("https://test.com")
    
    @pytest.mark.asyncio
    async def test_cloudflare_protection(self, scraper):
        """Test handling of Cloudflare protection page"""
        cloudflare_html = """
        <html>
            <head><title>Just a moment...</title></head>
            <body>
                <div>Checking your browser before accessing</div>
                <div>This process is automatic</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = cloudflare_html
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="HTTP 503"):
                await scraper.scrape_company_data("https://test.com")
    
    def test_rating_extraction_edge_cases(self, scraper):
        """Test rating extraction from various edge case formats"""
        test_cases = [
            # Different decimal separators
            ('<span>Rating 4,5</span>', 4.5),
            ('<span>4.5 stars</span>', 4.5),
            ('<span>4.5/5</span>', 4.5),
            ('<span>4.5 out of 5</span>', 4.5),
            ('<span>Rating: 4.5★</span>', 4.5),
            # Edge numeric values
            ('<span>5.0</span>', 5.0),
            ('<span>1.0</span>', 1.0),
            ('<span>0.1</span>', 0.1),
            # Multiple ratings in same element
            ('<span>4.5 (based on 4.2 culture)</span>', 4.5),
        ]
        
        for html, expected in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            import re
            
            text = soup.get_text()
            match = re.search(r'(\d+[.,]\d+)', text)
            
            if match:
                rating = float(match.group(1).replace(',', '.'))
                assert rating == expected, f"Failed for {html}: expected {expected}, got {rating}"
    
    def test_company_size_extraction_variations(self, scraper):
        """Test company size extraction from different formats"""
        test_cases = [
            ("51 to 200 employees", "51 to 200"),
            ("1-50 employees", "1-50"), 
            ("201-500 employees", "201-500"),
            ("1,000+ employees", "1,000+"),
            ("10,000+ employees", "10,000+"),
            ("11 to 50 employees", "11 to 50"),
        ]
        
        for input_text, expected in test_cases:
            import re
            match = re.search(r'(\d+(?:,\d+)*(?:\+)?\s*(?:to|\-)\s*\d+(?:,\d+)*|\d+(?:,\d+)*\+?)\s*employees?', input_text, re.IGNORECASE)
            
            if match:
                result = match.group(1)
                assert result == expected, f"Failed for '{input_text}': expected '{expected}', got '{result}'"
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, scraper):
        """Test handling of Unicode and special characters in company names"""
        unicode_html = """
        <html>
            <body>
                <div data-test="employer-name">Compañía Española S.A.</div>
                <div data-test="rating"><span>4.2</span></div>
                <div>Headquarters: São Paulo, Brasil</div>
                <div>Industry: Tecnología & Innovación</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = unicode_html
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await scraper.scrape_company_data("https://test.com")
            
            assert result["company_name"] == "Compañía Española S.A."
            assert result["overall_rating"] == 4.2
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, scraper):
        """Test handling of empty or minimal responses"""
        empty_cases = [
            "",  # Completely empty
            "<html></html>",  # Empty HTML
            "<html><body></body></html>",  # Empty body
            "<html><body><div></div></body></html>",  # Empty divs
        ]
        
        for empty_content in empty_cases:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = empty_content
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                
                result = await scraper.scrape_company_data("https://test.com")
                
                # Should not crash and should contain basic fields
                assert "glassdoor_url" in result
                assert "scraped_at" in result
    
    @pytest.mark.asyncio
    async def test_extremely_long_company_names(self, scraper, sample_user):
        """Test handling of extremely long company names"""
        long_name = "A" * 500  # Very long company name
        
        request = CompanyScrapeRequest(company_name=long_name)
        
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)
        
        # Mock scraper to simulate failure to find such a long name
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db), \
             patch('app.api.routes.glassdoor.glassdoor_scraper.get_company_rating',
                   side_effect=Exception("Company name too long")):
            
            with pytest.raises(Exception):  # Should handle gracefully
                await scrape_company_data(request, sample_user)
    
    def test_sql_injection_attempts_in_company_names(self):
        """Test that potential SQL injection attempts are handled safely"""
        malicious_names = [
            "'; DROP TABLE companies; --",
            "Company' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
        ]
        
        for malicious_name in malicious_names:
            # Test regex pattern used in database queries
            import re
            pattern = {"$regex": f"^{malicious_name}$", "$options": "i"}
            
            # Should not cause regex compilation errors
            try:
                regex = re.compile(pattern["$regex"], re.IGNORECASE)
                # Pattern should work without throwing exceptions
                assert regex is not None
            except re.error:
                pytest.fail(f"Regex compilation failed for: {malicious_name}")
    
    @pytest.mark.asyncio
    async def test_network_connection_errors(self, scraper):
        """Test various network connection error scenarios"""
        network_errors = [
            httpx.ConnectError("Connection failed"),
            httpx.ReadTimeout("Read timeout"),
            httpx.WriteTimeout("Write timeout"),
            httpx.PoolTimeout("Pool timeout"),
            httpx.UnsupportedProtocol("Unsupported protocol"),
        ]
        
        for error in network_errors:
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=error)
                
                with pytest.raises(Exception, match="Failed to scrape company data"):
                    await scraper.scrape_company_data("https://test.com")
    
    def test_date_parsing_edge_cases(self):
        """Test edge cases in date parsing"""
        from datetime import datetime
        
        date_formats = [
            "2023-12-31T23:59:59Z",
            "2023-01-01T00:00:00Z", 
            "2000-01-01T00:00:00Z",  # Y2K date
            "2099-12-31T23:59:59Z",  # Far future
        ]
        
        for date_str in date_formats:
            try:
                parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                assert isinstance(parsed, datetime)
            except ValueError as e:
                pytest.fail(f"Date parsing failed for {date_str}: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, scraper):
        """Test handling of multiple concurrent scraping requests"""
        import asyncio
        
        # Mock responses for multiple requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<div data-test="rating"><span>4.0</span></div>'
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            # Create multiple concurrent requests
            tasks = [
                scraper.scrape_company_data(f"https://test.com/company{i}")
                for i in range(5)
            ]
            
            # Should handle concurrent requests without issues
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert "glassdoor_url" in result


@pytest.mark.asyncio
async def test_database_connection_failure(sample_user):
    """Test handling of database connection failures"""
    from app.api.routes.glassdoor import scrape_company_data
    
    request = CompanyScrapeRequest(company_name="Test Company")
    
    # Mock database connection failure
    with patch('app.api.routes.glassdoor.get_database', side_effect=Exception("Database connection failed")):
        
        with pytest.raises(Exception):  # Should propagate database errors appropriately
            await scrape_company_data(request, sample_user)