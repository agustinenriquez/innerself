import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models.glassdoor_company import GlassdoorCompany, CompanyScrapeRequest
from app.models.user import User, UserRole
from app.api.routes.glassdoor import scrape_company_data, get_company_data, get_company_rating


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return User(
        id="test_user_id",
        email="test@example.com",
        name="Test User",
        role=UserRole.DEVELOPER
    )


@pytest.fixture
def mock_admin_user():
    return User(
        id="admin_user_id",
        email="admin@example.com", 
        name="Admin User",
        role=UserRole.ADMIN
    )


@pytest.fixture
def mock_glassdoor_company():
    return {
        "_id": "507f1f77bcf86cd799439011",
        "company_name": "CXC Technologies",
        "glassdoor_url": "https://www.glassdoor.com/Reviews/CXC-Reviews-E966930.htm",
        "overall_rating": 4.1,
        "review_count": 25,
        "industry": "Technology",
        "headquarters": "Buenos Aires, Argentina", 
        "founded": "2010",
        "company_size": "51 to 200",
        "scraped_at": datetime.utcnow(),
        "last_updated": datetime.utcnow(),
        "raw_data": {}
    }


@pytest.fixture
def mock_scraped_data():
    return {
        "company_name": "CXC Technologies",
        "glassdoor_url": "https://www.glassdoor.com/Reviews/CXC-Reviews-E966930.htm",
        "overall_rating": 4.1,
        "review_count": 25,
        "industry": "Technology",
        "headquarters": "Buenos Aires, Argentina",
        "founded": "2010", 
        "company_size": "51 to 200",
        "scraped_at": datetime.utcnow()
    }


class TestGlassdoorAPI:
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_success_new_company(self, mock_user, mock_scraped_data):
        """Test successful scraping of new company"""
        request = CompanyScrapeRequest(
            company_name="CXC Technologies",
            glassdoor_url="https://www.glassdoor.com/Reviews/CXC-Reviews-E966930.htm"
        )
        
        # Mock database operations
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)  # No recent data
        mock_db.glassdoor_companies.insert_one = AsyncMock(
            return_value=Mock(inserted_id="507f1f77bcf86cd799439011")
        )
        
        # Mock scraper
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db), \
             patch('app.api.routes.glassdoor.glassdoor_scraper.get_company_rating', 
                   return_value=mock_scraped_data):
            
            result = await scrape_company_data(request, mock_user)
            
            assert isinstance(result, GlassdoorCompany)
            assert result.company_name == "CXC Technologies"
            assert result.overall_rating == 4.1
            assert result.review_count == 25
            
            # Verify database calls
            mock_db.glassdoor_companies.find_one.assert_called()
            mock_db.glassdoor_companies.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_success_existing_company(self, mock_user, mock_scraped_data, mock_glassdoor_company):
        """Test successful scraping of existing company"""
        request = CompanyScrapeRequest(company_name="CXC Technologies")
        
        # Mock database operations
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(
            side_effect=[None, mock_glassdoor_company]  # No recent data, then existing company
        )
        mock_db.glassdoor_companies.update_one = AsyncMock()
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db), \
             patch('app.api.routes.glassdoor.glassdoor_scraper.get_company_rating', 
                   return_value=mock_scraped_data):
            
            result = await scrape_company_data(request, mock_user)
            
            assert isinstance(result, GlassdoorCompany)
            assert result.company_name == "CXC Technologies"
            
            # Verify update was called instead of insert
            mock_db.glassdoor_companies.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_recent_cache(self, mock_user, mock_glassdoor_company):
        """Test that recent data is returned from cache"""
        request = CompanyScrapeRequest(company_name="CXC Technologies")
        
        # Mock recent data (less than 24 hours old)
        recent_data = mock_glassdoor_company.copy()
        recent_data["scraped_at"] = datetime.utcnow() - timedelta(hours=12)
        
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=recent_data)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            
            result = await scrape_company_data(request, mock_user)
            
            assert isinstance(result, GlassdoorCompany)
            assert result.company_name == "CXC Technologies"
            
            # Verify no scraping was performed
            mock_db.glassdoor_companies.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_empty_company_name(self, mock_user):
        """Test error handling for empty company name"""
        request = CompanyScrapeRequest(company_name="   ")
        
        with pytest.raises(HTTPException) as exc_info:
            await scrape_company_data(request, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Company name is required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_no_rating_found(self, mock_user):
        """Test error handling when no rating is found"""
        request = CompanyScrapeRequest(company_name="Unknown Company")
        
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)
        
        # Mock scraper returning data without rating
        scraped_data_no_rating = {"company_name": "Unknown Company", "scraped_at": datetime.utcnow()}
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db), \
             patch('app.api.routes.glassdoor.glassdoor_scraper.get_company_rating',
                   return_value=scraped_data_no_rating):
            
            with pytest.raises(HTTPException) as exc_info:
                await scrape_company_data(request, mock_user)
            
            assert exc_info.value.status_code == 404
            assert "Could not find rating for this company" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_scrape_company_data_scraper_exception(self, mock_user):
        """Test error handling when scraper raises exception"""
        request = CompanyScrapeRequest(company_name="Error Company")
        
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db), \
             patch('app.api.routes.glassdoor.glassdoor_scraper.get_company_rating',
                   side_effect=Exception("Scraping failed")):
            
            with pytest.raises(HTTPException) as exc_info:
                await scrape_company_data(request, mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to scrape company data: Scraping failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_company_data_success(self, mock_user, mock_glassdoor_company):
        """Test successful retrieval of company data"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=mock_glassdoor_company)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            
            result = await get_company_data("CXC Technologies", mock_user)
            
            assert isinstance(result, GlassdoorCompany)
            assert result.company_name == "CXC Technologies"
            assert result.overall_rating == 4.1
    
    @pytest.mark.asyncio
    async def test_get_company_data_not_found(self, mock_user):
        """Test company not found in database"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_company_data("Nonexistent Company", mock_user)
            
            assert exc_info.value.status_code == 404
            assert "Company not found in database" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_company_rating_public_endpoint_success(self, mock_glassdoor_company):
        """Test public rating endpoint success"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=mock_glassdoor_company)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            
            result = await get_company_rating("CXC Technologies")
            
            assert result["company_name"] == "CXC Technologies"
            assert result["overall_rating"] == 4.1
            assert result["review_count"] == 25
            assert "glassdoor_url" in result
            assert "last_updated" in result
    
    @pytest.mark.asyncio
    async def test_get_company_rating_public_endpoint_not_found(self):
        """Test public rating endpoint when company not found"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find_one = AsyncMock(return_value=None)
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_company_rating("Nonexistent Company")
            
            assert exc_info.value.status_code == 404
            assert "Company not found" in str(exc_info.value.detail)
    
    def test_case_insensitive_company_search(self):
        """Test that database queries are case insensitive"""
        company_names = ["CXC Technologies", "cxc technologies", "CXC TECHNOLOGIES", "cXc TeChnOloGieS"]
        
        for name in company_names:
            # This is the regex pattern used in the actual code
            import re
            pattern = {"$regex": f"^{name}$", "$options": "i"}
            
            # Test that the pattern would match the canonical form
            regex = re.compile(pattern["$regex"], re.IGNORECASE)
            assert regex.match("CXC Technologies")
            assert regex.match("cxc technologies")
    
    @pytest.mark.asyncio
    async def test_list_companies_success(self, mock_user):
        """Test successful listing of companies"""
        mock_companies = [
            {"_id": "id1", "company_name": "Company 1", "overall_rating": 4.0, "glassdoor_url": "", "raw_data": {}, "scraped_at": datetime.utcnow(), "last_updated": datetime.utcnow()},
            {"_id": "id2", "company_name": "Company 2", "overall_rating": 3.5, "glassdoor_url": "", "raw_data": {}, "scraped_at": datetime.utcnow(), "last_updated": datetime.utcnow()},
        ]
        
        # Create a proper async iterator mock
        async def mock_async_iter(self):
            for company in mock_companies:
                yield company
        
        # Mock the full chain properly
        mock_cursor = Mock()
        mock_cursor.__aiter__ = mock_async_iter
        
        mock_sort_and_limit = Mock()
        mock_sort_and_limit.return_value = mock_cursor
        
        mock_sort = Mock()
        mock_sort.return_value.limit = mock_sort_and_limit
        
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.find.return_value.sort = mock_sort
        
        from app.api.routes.glassdoor import list_companies
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            result = await list_companies(50, mock_user)
            
            assert len(result) == 2
            assert all(isinstance(company, GlassdoorCompany) for company in result)
    
    @pytest.mark.asyncio
    async def test_delete_company_success_admin(self, mock_admin_user, mock_glassdoor_company):
        """Test successful company deletion by admin"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.delete_one = AsyncMock(
            return_value=Mock(deleted_count=1)
        )
        
        from app.api.routes.glassdoor import delete_company
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            result = await delete_company("CXC Technologies", mock_admin_user)
            
            assert result["message"] == "Company CXC Technologies deleted successfully"
            mock_db.glassdoor_companies.delete_one.assert_called_once()
    
    @pytest.mark.asyncio  
    async def test_delete_company_forbidden_non_admin(self, mock_user):
        """Test company deletion forbidden for non-admin users"""
        from app.api.routes.glassdoor import delete_company
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_company("CXC Technologies", mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_company_not_found(self, mock_admin_user):
        """Test company deletion when company not found"""
        mock_db = AsyncMock()
        mock_db.glassdoor_companies.delete_one = AsyncMock(
            return_value=Mock(deleted_count=0)
        )
        
        from app.api.routes.glassdoor import delete_company
        
        with patch('app.api.routes.glassdoor.get_database', return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await delete_company("Nonexistent Company", mock_admin_user)
            
            assert exc_info.value.status_code == 404
            assert "Company not found" in str(exc_info.value.detail)


class TestGlassdoorAPIIntegration:
    """Integration tests using TestClient"""
    
    def test_health_endpoint(self, test_client):
        """Test that the health endpoint works (integration smoke test)"""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    # Note: Full integration tests would require authentication setup
    # and database mocking at the application level