import httpx
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import quote
import asyncio
from datetime import datetime

class GlassdoorScraper:
    """Service for scraping Glassdoor company data"""
    
    def __init__(self):
        self.base_url = "https://www.glassdoor.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.timeout = 30.0
    
    async def search_company(self, company_name: str) -> Optional[str]:
        """
        Search for a company on Glassdoor and return the first result URL
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            Company URL or None if not found
        """
        search_url = f"{self.base_url}/Reviews/company-reviews.htm"
        params = {"sc.keyword": company_name}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    search_url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for company links in search results
                    company_links = soup.find_all('a', href=re.compile(r'/Overview/Working-at-.*\.htm'))
                    if company_links:
                        return self.base_url + company_links[0]['href']
                    
                    # Alternative: look for review links
                    review_links = soup.find_all('a', href=re.compile(r'/Reviews/.*-Reviews-.*\.htm'))
                    if review_links:
                        return self.base_url + review_links[0]['href']
                        
                return None
                
            except Exception as e:
                print(f"Error searching for company {company_name}: {str(e)}")
                return None
    
    async def scrape_company_data(self, url: str) -> Dict[str, Any]:
        """
        Scrape company data from a Glassdoor company page
        
        Args:
            url: Glassdoor company page URL
            
        Returns:
            Dictionary with scraped company data
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: Failed to fetch page")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                data = {
                    "glassdoor_url": url,
                    "scraped_at": datetime.utcnow()
                }
                
                # Extract overall rating - multiple possible selectors
                rating_selectors = [
                    '[data-test="rating"] span',
                    '.rating span',
                    '[data-test="employer-rating"]',
                    '.ratingNum',
                    '.rating-headline-average'
                ]
                
                for selector in rating_selectors:
                    rating_elem = soup.select_one(selector)
                    if rating_elem:
                        rating_text = rating_elem.get_text().strip()
                        # Extract numeric rating (e.g., "4.1" from "4.1 out of 5")
                        rating_match = re.search(r'(\d+[.,]\d+)', rating_text)
                        if rating_match:
                            data["overall_rating"] = float(rating_match.group(1).replace(',', '.'))
                            break
                
                # Extract company name
                name_selectors = [
                    '[data-test="employer-name"]',
                    '.employer-name',
                    '.empName',
                    'h1'
                ]
                
                for selector in name_selectors:
                    name_elem = soup.select_one(selector)
                    if name_elem:
                        data["company_name"] = name_elem.get_text().strip()
                        break
                
                # Extract review count
                review_count_selectors = [
                    '[data-test="employer-rating-count"]',
                    '.review-count',
                    '.reviewCount'
                ]
                
                for selector in review_count_selectors:
                    count_elem = soup.select_one(selector)
                    if count_elem:
                        count_text = count_elem.get_text().strip()
                        count_match = re.search(r'(\d+(?:,\d+)*)', count_text)
                        if count_match:
                            data["review_count"] = int(count_match.group(1).replace(',', ''))
                            break
                
                # Extract detailed ratings
                rating_categories = {
                    "culture_rating": ["Culture & Values", "cultura", "culture"],
                    "career_opportunities": ["Career Opportunities", "carrera", "career"],
                    "compensation_benefits": ["Comp & Benefits", "compensation", "benefits"],
                    "work_life_balance": ["Work/Life Balance", "work-life", "balance"],
                    "senior_management": ["Senior Management", "management", "gerencia"]
                }
                
                for category, keywords in rating_categories.items():
                    for keyword in keywords:
                        # Look for rating elements near text containing the keyword
                        rating_containers = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                        for container in rating_containers:
                            parent = container.parent
                            if parent:
                                # Look for rating in the same or nearby elements
                                rating_elem = parent.find_next(text=re.compile(r'\d+[.,]\d+'))
                                if rating_elem:
                                    rating_match = re.search(r'(\d+[.,]\d+)', rating_elem)
                                    if rating_match:
                                        data[category] = float(rating_match.group(1).replace(',', '.'))
                                        break
                        if category in data:
                            break
                
                # Extract company info
                info_selectors = [
                    '.employer-info',
                    '.company-details',
                    '.overview-section'
                ]
                
                for selector in info_selectors:
                    info_section = soup.select_one(selector)
                    if info_section:
                        info_text = info_section.get_text()
                        
                        # Extract company size
                        size_match = re.search(r'(\d+(?:,\d+)*(?:\+)?\s*(?:to|\-)\s*\d+(?:,\d+)*|\d+(?:,\d+)*\+?)\s*employees?', info_text, re.IGNORECASE)
                        if size_match:
                            data["company_size"] = size_match.group(1)
                        
                        # Extract industry
                        industry_match = re.search(r'Industry[:\s]+([^•\n]+)', info_text, re.IGNORECASE)
                        if industry_match:
                            data["industry"] = industry_match.group(1).strip()
                        
                        # Extract headquarters
                        hq_match = re.search(r'Headquarters[:\s]+([^•\n]+)', info_text, re.IGNORECASE)
                        if hq_match:
                            data["headquarters"] = hq_match.group(1).strip()
                        
                        # Extract founded year
                        founded_match = re.search(r'Founded[:\s]+(\d{4})', info_text, re.IGNORECASE)
                        if founded_match:
                            data["founded"] = founded_match.group(1)
                        
                        break
                
                return data
                
            except Exception as e:
                raise Exception(f"Failed to scrape company data: {str(e)}")
    
    async def get_company_rating(self, company_name: str, glassdoor_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get company rating by name or URL
        
        Args:
            company_name: Name of the company
            glassdoor_url: Optional direct URL to company page
            
        Returns:
            Dictionary with company data including rating
        """
        url = glassdoor_url
        
        if not url:
            # Search for the company
            url = await self.search_company(company_name)
            if not url:
                raise Exception(f"Company '{company_name}' not found on Glassdoor")
        
        # Scrape the company data
        data = await self.scrape_company_data(url)
        data["company_name"] = company_name
        
        return data

glassdoor_scraper = GlassdoorScraper()