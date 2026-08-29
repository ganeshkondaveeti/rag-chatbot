import os
import json
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any

try:
    from playwright.async_api import async_playwright
except ImportError:
    # Handle environment where playwright might not be installed yet
    pass

from .content_cleaner import ContentCleaner

SCHEMES = [
    {
        "name": "HDFC Mid Cap Fund",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    },
    {
        "name": "HDFC Small Cap Fund",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
    },
    {
        "name": "HDFC Gold ETF FoF",
        "url": "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    },
    {
        "name": "HDFC Large Cap Fund",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    },
    {
        "name": "HDFC ELSS Tax Saver Fund",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"
    }
]

class GrowwScraper:
    def __init__(self):
        self.cleaner = ContentCleaner()
        self.raw_dir = os.path.join(os.path.dirname(__file__), '../../data/raw')
        self.processed_dir = os.path.join(os.path.dirname(__file__), '../../data/processed')
        
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    def extract_sections(self, html_content: str) -> List[Dict[str, Any]]:
        """Parses HTML and extracts structured sections."""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove nav, header, footer, scripts, and styles to reduce noise
        for elements in soup(['nav', 'header', 'footer', 'script', 'style', 'aside']):
            elements.decompose()
            
        sections = []
        
        # Fund Overview
        overview = soup.find('div', class_=lambda c: c and 'fundOverview' in c)
        if overview:
            sections.append(self.cleaner.process_section("Fund Overview", overview.get_text(separator='\n')))
        else:
            # Fallback for generic text extraction if classes change
            h1 = soup.find('h1')
            if h1 and h1.parent:
                sections.append(self.cleaner.process_section("Fund Overview", h1.parent.get_text(separator='\n')))
                
        # Fund Details (Expense, Exit load, etc)
        details = soup.find(text=lambda t: t and 'Expense Ratio' in t)
        if details and details.parent and details.parent.parent:
            # Climb up the tree a bit to capture the whole table/section
            sections.append(self.cleaner.process_section("Fund Details", details.parent.parent.parent.get_text(separator='\n')))
            
        # Returns & NAV
        nav = soup.find(text=lambda t: t and 'NAV' in t)
        if nav and nav.parent and nav.parent.parent:
            sections.append(self.cleaner.process_section("NAV & AUM", nav.parent.parent.parent.get_text(separator='\n')))
            
        # If we failed to get structured sections, just chunk the main body text heuristically
        if not sections:
            main_content = soup.find('main') or soup.find('body')
            if main_content:
                sections.append(self.cleaner.process_section("General Info", main_content.get_text(separator='\n')))

        return sections

    async def scrape_url(self, scheme: Dict[str, str]):
        """Scrapes a single URL using Playwright."""
        url = scheme["url"]
        scheme_name = scheme["name"]
        scrape_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"Scraping {scheme_name} at {url}...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                html_content = await page.content()
                await browser.close()
                
                # Save Raw HTML
                safe_name = scheme_name.replace(" ", "_").lower()
                raw_path = os.path.join(self.raw_dir, f"{safe_name}_{scrape_date}.html")
                with open(raw_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                    
                # Process and Extract Sections
                sections = self.extract_sections(html_content)
                
                output = {
                    "scheme_name": scheme_name,
                    "source_url": url,
                    "scrape_date": scrape_date,
                    "sections": sections
                }
                
                # Save Processed JSON
                processed_path = os.path.join(self.processed_dir, f"{safe_name}.json")
                with open(processed_path, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                    
                print(f"Successfully processed {scheme_name}")
                return output
                
        except Exception as e:
            print(f"Failed to scrape {scheme_name}: {str(e)}")
            return None

    async def run_all(self):
        """Scrapes all configured schemes."""
        tasks = [self.scrape_url(scheme) for scheme in SCHEMES]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

if __name__ == "__main__":
    scraper = GrowwScraper()
    asyncio.run(scraper.run_all())
