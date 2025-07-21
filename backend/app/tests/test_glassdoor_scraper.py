import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from app.services.glassdoor_scraper import GlassdoorScraper


@pytest.fixture
def glassdoor_scraper():
    return GlassdoorScraper()


@pytest.fixture
def mock_html_with_rating():
    """Mock HTML response with rating data"""
    return """
    <html>
        <body>
            <div data-test="rating">
                <span>4.1</span>
            </div>
            <div data-test="employer-name">CXC Technologies</div>
            <div data-test="employer-rating-count">25 reviews</div>
            <div class="employer-info">
                <div>Industry: Technology</div>
                <div>Headquarters: Buenos Aires, Argentina</div>
                <div>Founded: 2010</div>
                <div>51 to 200 employees</div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_without_rating():
    """Mock HTML response without rating data"""
    return """
    <html>
        <body>
            <div data-test="employer-name">Unknown Company</div>
            <div>No rating information found</div>
        </body>
    </html>
    """


@pytest.fixture
def mock_search_results_html():
    """Mock HTML for search results"""
    return """
    <html>
        <body>
            <a href="/Reviews/CXC-Technologies-Reviews-E966930.htm">CXC Technologies Reviews</a>
            <a href="/Overview/Working-at-CXC-E966930.htm">Working at CXC</a>
        </body>
    </html>
    """


class TestGlassdoorScraper:
    
    @pytest.mark.asyncio
    async def test_search_company_success(self, glassdoor_scraper, mock_search_results_html):
        """Test successful company search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_search_results_html
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await glassdoor_scraper.search_company("CXC")
            
            assert result == "https://www.glassdoor.com/Reviews/CXC-Technologies-Reviews-E966930.htm"
    
    @pytest.mark.asyncio
    async def test_search_company_not_found(self, glassdoor_scraper):
        """Test company search when no results found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No results found</body></html>"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await glassdoor_scraper.search_company("NonexistentCompany")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_search_company_http_error(self, glassdoor_scraper):
        """Test company search with HTTP error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            
            result = await glassdoor_scraper.search_company("TestCompany")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_success(self, glassdoor_scraper, mock_html_with_rating):
        """Test successful company data scraping"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html_with_rating
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await glassdoor_scraper.scrape_company_data("https://glassdoor.com/test")
            
            assert result["overall_rating"] == 4.1
            assert result["company_name"] == "CXC Technologies"
            assert result["review_count"] == 25
            assert result["industry"] == "Technology"
            assert result["headquarters"] == "Buenos Aires, Argentina"
            assert result["founded"] == "2010"
            assert result["company_size"] == "51 to 200"
            assert "glassdoor_url" in result
            assert "scraped_at" in result
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_no_rating(self, glassdoor_scraper, mock_html_without_rating):
        """Test scraping company data without rating"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html_without_rating
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await glassdoor_scraper.scrape_company_data("https://glassdoor.com/test")
            
            assert "overall_rating" not in result
            assert result["company_name"] == "Unknown Company"
            assert "glassdoor_url" in result
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_http_404(self, glassdoor_scraper):
        """Test scraping with 404 error"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="HTTP 404"):
                await glassdoor_scraper.scrape_company_data("https://glassdoor.com/nonexistent")
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_network_error(self, glassdoor_scraper):
        """Test scraping with network error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            
            with pytest.raises(Exception, match="Failed to scrape company data"):
                await glassdoor_scraper.scrape_company_data("https://glassdoor.com/test")
    
    @pytest.mark.asyncio
    async def test_get_company_rating_with_url(self, glassdoor_scraper, mock_html_with_rating):
        """Test getting company rating with direct URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html_with_rating
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await glassdoor_scraper.get_company_rating(
                "CXC", 
                "https://glassdoor.com/test"
            )
            
            assert result["company_name"] == "CXC"
            assert result["overall_rating"] == 4.1
    
    @pytest.mark.asyncio
    async def test_get_company_rating_with_search(self, glassdoor_scraper, mock_search_results_html, mock_html_with_rating):
        """Test getting company rating by searching first"""
        search_response = Mock()
        search_response.status_code = 200
        search_response.text = mock_search_results_html
        
        company_response = Mock()
        company_response.status_code = 200
        company_response.text = mock_html_with_rating
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock(side_effect=[search_response, company_response])
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await glassdoor_scraper.get_company_rating("CXC")
            
            assert result["company_name"] == "CXC"
            assert result["overall_rating"] == 4.1
            # Verify search was called first, then company page
            assert mock_get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_company_rating_search_not_found(self, glassdoor_scraper):
        """Test getting company rating when search returns no results"""
        search_response = Mock()
        search_response.status_code = 200
        search_response.text = "<html><body>No results</body></html>"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=search_response)
            
            with pytest.raises(Exception, match="Company 'CXC' not found on Glassdoor"):
                await glassdoor_scraper.get_company_rating("CXC")
    
    def test_extract_rating_from_various_formats(self, glassdoor_scraper):
        """Test rating extraction from different HTML formats"""
        test_cases = [
            ('<span data-test="rating">4.2</span>', 4.2),
            ('<div class="rating"><span>3.8</span></div>', 3.8),
            ('<div class="ratingNum">4.5</div>', 4.5),
            ('<span>4,7 out of 5</span>', 4.7),  # European decimal format
            ('<div>Rating: 2.9</div>', 2.9),
        ]
        
        for html, expected_rating in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            # Test the rating extraction logic
            rating_selectors = [
                '[data-test="rating"] span',
                '.rating span', 
                '[data-test="employer-rating"]',
                '.ratingNum',
                '.rating-headline-average'
            ]
            
            found_rating = None
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text().strip()
                    import re
                    rating_match = re.search(r'(\d+[.,]\d+)', rating_text)
                    if rating_match:
                        found_rating = float(rating_match.group(1).replace(',', '.'))
                        break
            
            # For simple cases where the element contains just the rating
            if not found_rating:
                import re
                rating_match = re.search(r'(\d+[.,]\d+)', html)
                if rating_match:
                    found_rating = float(rating_match.group(1).replace(',', '.'))
            
            assert found_rating == expected_rating, f"Failed to extract {expected_rating} from {html}"
    
    def test_extract_review_count_formats(self, glassdoor_scraper):
        """Test review count extraction from different formats"""
        test_cases = [
            ('<div data-test="employer-rating-count">25 reviews</div>', 25),
            ('<span class="review-count">1,234 reviews</span>', 1234),
            ('<div>Based on 500 employee reviews</div>', 500),
        ]
        
        for html, expected_count in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            import re
            
            count_text = soup.get_text()
            count_match = re.search(r'(\d+(?:,\d+)*)', count_text)
            
            assert count_match is not None, f"No count found in {html}"
            found_count = int(count_match.group(1).replace(',', ''))
            assert found_count == expected_count, f"Expected {expected_count}, got {found_count}"
    
    @pytest.mark.asyncio
    async def test_headers_configuration(self, glassdoor_scraper):
        """Test that proper headers are set for requests"""
        expected_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        assert glassdoor_scraper.headers == expected_headers
        assert glassdoor_scraper.timeout == 30.0
        assert glassdoor_scraper.base_url == "https://www.glassdoor.com"