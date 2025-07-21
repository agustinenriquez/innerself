import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.glassdoor_company import GlassdoorCompany


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = AsyncMock()
    
    # Mock collections
    db.users = AsyncMock()
    db.glassdoor_companies = AsyncMock()
    db.github_users = AsyncMock()
    db.messages = AsyncMock()
    db.essence_logs = AsyncMock()
    
    return db


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id="507f1f77bcf86cd799439011",
        email="john.doe@example.com",
        name="John Doe",
        role=UserRole.DEVELOPER
    )


@pytest.fixture
def sample_admin_user():
    """Sample admin user for testing"""
    return User(
        id="507f1f77bcf86cd799439012",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN
    )


@pytest.fixture
def sample_glassdoor_company():
    """Sample Glassdoor company data"""
    return {
        "_id": "507f1f77bcf86cd799439020",
        "company_name": "CXC Technologies",
        "glassdoor_url": "https://www.glassdoor.com/Reviews/CXC-Technologies-Reviews-E966930.htm",
        "overall_rating": 4.1,
        "ceo_approval": 85.0,
        "recommend_to_friend": 78.0,
        "culture_rating": 4.2,
        "career_opportunities": 3.9,
        "compensation_benefits": 4.0,
        "work_life_balance": 4.3,
        "senior_management": 3.8,
        "review_count": 25,
        "company_size": "51 to 200 employees",
        "industry": "Information Technology",
        "headquarters": "Buenos Aires, Argentina",
        "founded": "2010",
        "raw_data": {
            "scraped_html": "<html>...</html>",
            "additional_data": {}
        },
        "scraped_at": datetime.utcnow() - timedelta(hours=2),
        "last_updated": datetime.utcnow() - timedelta(hours=2)
    }


@pytest.fixture
def sample_company_html():
    """Sample HTML content from Glassdoor company page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CXC Technologies Reviews | Glassdoor</title>
    </head>
    <body>
        <div class="employer-overview">
            <div data-test="employer-name">CXC Technologies</div>
            <div data-test="rating">
                <span>4.1</span>
            </div>
            <div data-test="employer-rating-count">25 reviews</div>
            
            <div class="employer-info">
                <div class="info-item">
                    <label>Industry</label>
                    <span>Information Technology</span>
                </div>
                <div class="info-item">
                    <label>Headquarters</label>
                    <span>Buenos Aires, Argentina</span>
                </div>
                <div class="info-item">
                    <label>Founded</label>
                    <span>2010</span>
                </div>
                <div class="info-item">
                    <label>Company Size</label>
                    <span>51 to 200 employees</span>
                </div>
            </div>
            
            <div class="ratings-breakdown">
                <div class="rating-item">
                    <span class="rating-label">Culture & Values</span>
                    <span class="rating-value">4.2</span>
                </div>
                <div class="rating-item">
                    <span class="rating-label">Career Opportunities</span>
                    <span class="rating-value">3.9</span>
                </div>
                <div class="rating-item">
                    <span class="rating-label">Comp & Benefits</span>
                    <span class="rating-value">4.0</span>
                </div>
                <div class="rating-item">
                    <span class="rating-label">Work/Life Balance</span>
                    <span class="rating-value">4.3</span>
                </div>
                <div class="rating-item">
                    <span class="rating-label">Senior Management</span>
                    <span class="rating-value">3.8</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_search_html():
    """Sample HTML content from Glassdoor search results"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Company Reviews | Glassdoor</title>
    </head>
    <body>
        <div class="search-results">
            <div class="search-result">
                <a href="/Reviews/CXC-Technologies-Reviews-E966930.htm">
                    CXC Technologies Reviews and Ratings
                </a>
            </div>
            <div class="search-result">
                <a href="/Overview/Working-at-Another-Company-E123456.htm">
                    Another Company Overview
                </a>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response factory"""
    def _create_response(status_code=200, content="", json_data=None):
        response = Mock()
        response.status_code = status_code
        response.text = content
        if json_data:
            response.json.return_value = json_data
        return response
    return _create_response


@pytest.fixture
def sample_company_variations():
    """Different variations of company data for testing edge cases"""
    return [
        {
            "name": "Company with European decimal",
            "html": '<div data-test="rating"><span>4,5</span></div>',
            "expected_rating": 4.5
        },
        {
            "name": "Company with rating in text",
            "html": '<div>Overall rating: 3.7 out of 5 stars</div>',
            "expected_rating": 3.7
        },
        {
            "name": "Company with large review count",
            "html": '<div data-test="employer-rating-count">1,234 reviews</div>',
            "expected_count": 1234
        },
        {
            "name": "Company with minimal data",
            "html": '<div><h1>Simple Company</h1><span class="rating">2.8</span></div>',
            "expected_rating": 2.8
        }
    ]