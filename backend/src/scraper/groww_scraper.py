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

    def extract_sections(self, html_content: str, scheme_name: str) -> List[Dict[str, Any]]:
        """Parses HTML and extracts structured sections."""
        import re
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove nav, header, footer, scripts, and styles to reduce noise
        for elements in soup(['nav', 'header', 'footer', 'script', 'style', 'aside']):
            elements.decompose()
            
        text = soup.get_text(separator='\n', strip=True)
        sections = []
        
        # Fund Overview
        about_match = re.search(fr'About {re.escape(scheme_name)}(.*?)(?=Investment Objective|Fund benchmark|Scheme Information Document)', text, re.IGNORECASE | re.DOTALL)
        if about_match:
            sections.append(self.cleaner.process_section("Fund Overview", about_match.group(1).strip()))
            
        # Fund Details
        details_match = re.search(r'(Min\. for SIP.*?)(?=Holdings|Return calculator|Annualised returns|Understand terms)', text, re.IGNORECASE | re.DOTALL)
        if details_match:
            sections.append(self.cleaner.process_section("Fund Details", details_match.group(1).strip()))
            
        # NAV & AUM
        nav_match = re.search(r'(NAV:.*?)(?=Return calculator|Holdings|Min\. for SIP)', text, re.IGNORECASE | re.DOTALL)
        if nav_match:
            sections.append(self.cleaner.process_section("NAV & AUM", nav_match.group(1).strip()))
            
        # Tax Info
        tax_match = re.search(r'(Tax implication.*?)(?=Check past data|Compare similar funds|Fund management)', text, re.IGNORECASE | re.DOTALL)
        if tax_match:
            sections.append(self.cleaner.process_section("Tax Info", tax_match.group(1).strip()))
            
        # Fallback
        if not sections:
            sections.append(self.cleaner.process_section("General Info", text[:2000]))

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
                sections = self.extract_sections(html_content, scheme_name)
                
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
