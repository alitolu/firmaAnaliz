import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper_log.txt'
)

# User agent list to rotate and avoid being blocked
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

def get_random_headers():
    """Generate random headers for HTTP requests"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

def clean_url(url):
    """Ensure URL has proper format"""
    if not url:
        return None
    
    url = url.strip().lower()
    
    # Add http:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
        
    return url

def get_base_domain(url):
    """Extract base domain from URL"""
    if not url:
        return None
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def extract_website_from_social_media(url):
    """
    Sosyal medya profilinden web sitesi URL'sini çıkarır.
    
    Args:
        url: Sosyal medya profil URL'si
    
    Returns:
        Bulunan web sitesi URL'si veya None
    """
    logging.info(f"Sosyal medya profilinden web sitesi çıkarılıyor: {url}")
    
    try:
        headers = get_random_headers()
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logging.warning(f"Sosyal medya URL'sine erişilemedi, durum kodu: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Facebook sayfasından web sitesi URL'si çıkarma
        if 'facebook.com' in url:
            # Facebook sayfalarında genellikle "Website" şeklinde bir link bulunur
            website_links = soup.select('a[href*="l.facebook.com/l.php"]')
            
            for link in website_links:
                href = link.get('href', '')
                # Facebook dış bağlantılarını kontrol et
                if 'l.facebook.com/l.php' in href and 'u=' in href:
                    # URL parametrelerinden gerçek URL'yi çıkar
                    try:
                        from urllib.parse import parse_qs, urlparse
                        parsed = urlparse(href)
                        target_url = parse_qs(parsed.query).get('u', [None])[0]
                        if target_url:
                            if not (target_url.endswith('.facebook.com') or 'facebook.com' in target_url):
                                logging.info(f"Facebook'tan web sitesi bulundu: {target_url}")
                                return target_url
                    except Exception as e:
                        logging.error(f"Facebook URL ayrıştırma hatası: {e}")
            
            # Alternatif yöntem - "Website" veya "Web Sitesi" adlı bağlantıları ara
            website_text_links = soup.find_all('a', string=re.compile(r'website|web site|web sitesi', re.I))
            for link in website_text_links:
                href = link.get('href', '')
                if href and 'http' in href and 'facebook.com' not in href:
                    logging.info(f"Facebook'tan web sitesi bulundu (alternatif): {href}")
                    return href
        
        # Instagram profilinden web sitesi URL'si çıkarma
        elif 'instagram.com' in url:
            # Instagram bio'sunda web sitesi genellikle metin olarak bulunur
            bio_section = soup.select_one('div.-vDIg')
            if bio_section:
                links = bio_section.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    if href and 'http' in href and 'instagram.com' not in href:
                        logging.info(f"Instagram'dan web sitesi bulundu: {href}")
                        return href
            
            # Instagram yeni tasarımı için
            bio_links = soup.select('a[href*="linktr.ee"], a[href*="linkin.bio"], a[href*="linkpop.com"]')
            if not bio_links:
                bio_links = soup.select('a[target="_blank"]')
                
            for link in bio_links:
                href = link.get('href', '')
                # Instagram dışı bir link ise ve "http" içeriyorsa
                if href and 'http' in href and 'instagram.com' not in href:
                    logging.info(f"Instagram'dan web sitesi bulundu: {href}")
                    return href
                    
            # Alternatif yöntem - HTML metin içeriğinde URL pattern'ı ara
            text_content = soup.get_text()
            url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)(?:/[^\s]*)?'
            url_matches = re.findall(url_pattern, text_content)
            
            for domain in url_matches:
                if ('instagram' not in domain and 
                    'facebook' not in domain and 
                    'twitter' not in domain and 
                    'youtube' not in domain and
                    'linkedin' not in domain and
                    len(domain) > 5):
                    website = f"http://{domain}"
                    logging.info(f"Instagram metin içeriğinden web sitesi bulundu: {website}")
                    return website
        
        # LinkedIn profilinden web sitesi URL'si çıkarma
        elif 'linkedin.com' in url:
            # LinkedIn şirket sayfalarında "Website" bölümü bulunur
            website_section = soup.select_one('.org-top-card-primary-actions__inner')
            if website_section:
                links = website_section.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    # LinkedIn dışı bir link ise
                    if href and 'linkedin.com' not in href:
                        logging.info(f"LinkedIn'den web sitesi bulundu: {href}")
                        return href
            
            # Alternatif yöntem - tüm harici bağlantıları kontrol et
            all_links = soup.select('a[href*="://"]')
            for link in all_links:
                href = link.get('href', '')
                if (href and 
                    'linkedin.com' not in href and 
                    'javascript:' not in href and
                    not href.startswith('#')):
                    logging.info(f"LinkedIn'den web sitesi bulundu (alternatif): {href}")
                    return href
        
        return None
    
    except Exception as e:
        logging.error(f"Sosyal medya profilinden web sitesi çıkarma hatası: {e}")
        return None

def find_website_via_google(company_name, result_index=0, max_results=10):
    """Search for company website using Bing search
    
    Args:
        company_name: The company name to search for
        result_index: Which search result to use (0 = first result)
        max_results: Maximum number of results to fetch
    """
    try:
        query = f"{company_name} resmi sitesi"
        logging.info(f"Searching for: {query}")
        
        # Use Bing instead of Google (less restrictive for web scraping)
        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count={max_results}"
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.bing.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        
        # Save the search result HTML for debugging
        with open(f"{company_name.replace(' ', '_')}_search_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        if response.status_code != 200:
            logging.warning(f"Search failed, status code: {response.status_code}")
            return None
            
        # Parse results
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find search results - Bing structure
        search_results = []
        social_media_results = []
        
        # Bing search results are in <li class="b_algo">
        result_elements = soup.find_all('li', class_='b_algo')
        
        if not result_elements:
            # Try alternative selectors
            result_elements = soup.select('#b_results > li')
            
        for result in result_elements:
            # Find the main link in each result
            link = result.find('a')
            if link and link.get('href'):
                url = link.get('href')
                
                # Sosyal medya URL'lerini ayrı bir listede topla
                if ('facebook.com' in url or 
                    'linkedin.com' in url or 
                    'instagram.com' in url):
                    social_media_results.append(url)
                    continue
                    
                # Skip certain URLs
                if (url.startswith('http') and 
                    'bing.com' not in url and 
                    'microsoft.com' not in url and
                    'facebook.com' not in url and
                    'linkedin.com' not in url and
                    'youtube.com' not in url and
                    'instagram.com' not in url):
                    search_results.append(url)
        
        # Eğer web sitesi bulunamadıysa ve sosyal medya sonuçları varsa
        if not search_results and social_media_results:
            logging.info(f"Doğrudan web sitesi bulunamadı, sosyal medya profillerinden çıkarılıyor: {company_name}")
            
            for social_url in social_media_results:
                website_from_social = extract_website_from_social_media(social_url)
                if website_from_social:
                    logging.info(f"Sosyal medyadan web sitesi bulundu: {website_from_social}")
                    return website_from_social
        
        # If still no results, try a more general approach
        if not search_results:
            logging.info("Using fallback method to find search results")
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                if (href and 
                    href.startswith('http') and 
                    'bing.com' not in href and 
                    'microsoft.com' not in href and
                    'go.microsoft.com' not in href and
                    'facebook.com' not in href and 
                    'linkedin.com' not in href and
                    'youtube.com' not in href and
                    'instagram.com' not in href):
                    search_results.append(href)
        
        # Sosyal medya profil bağlantılarını son çare olarak kontrol et
        if not search_results and not social_media_results:
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                if (href and 
                    href.startswith('http') and 
                    ('facebook.com' in href or 
                     'linkedin.com' in href or 
                     'instagram.com' in href)):
                    website_from_social = extract_website_from_social_media(href)
                    if website_from_social:
                        logging.info(f"Son çare sosyal medyadan web sitesi bulundu: {website_from_social}")
                        return website_from_social
                
        if not search_results:
            # Last resort: try direct DNS lookup
            potential_domains = [
                f"{company_name.lower().replace(' ', '')}.com",
                f"{company_name.lower().replace(' ', '')}.com.tr",
                f"www.{company_name.lower().replace(' ', '')}.com",
                f"www.{company_name.lower().replace(' ', '')}.com.tr"
            ]
            
            for domain in potential_domains:
                try:
                    import socket
                    socket.gethostbyname(domain)
                    url = f"http://{domain}"
                    logging.info(f"Found domain via DNS lookup: {url}")
                    return url
                except:
                    continue
            
            logging.warning(f"No search results found for {company_name}")
            return None
        
        # Log all results for debugging
        for i, result in enumerate(search_results[:max_results]):
            domain = get_base_domain(result)
            logging.info(f"Search result #{i+1} for {company_name}: {domain} - {result}")
            
        # Filter results that likely belong to the company
        company_name_simplified = company_name.lower().replace(' ', '')
        match_results = []
        
        for result in search_results:
            domain = get_base_domain(result)
            if domain and company_name_simplified in domain.replace('www.', ''):
                match_results.append(result)
        
        # If we found matches, use those first
        if match_results:
            # If requested index is within matches, return that
            if result_index < len(match_results):
                logging.info(f"Using match #{result_index+1} for {company_name}: {match_results[result_index]}")
                return match_results[result_index]
            # Otherwise use first match
            logging.info(f"Using first match for {company_name}: {match_results[0]}")
            return match_results[0]
                
        # If no matches and requested index is valid
        if result_index < len(search_results):
            logging.info(f"Using result #{result_index+1} for {company_name}: {search_results[result_index]}")
            return search_results[result_index]
        
        # Fallback to first result
        if search_results:
            logging.info(f"Using first result for {company_name}: {search_results[0]}")
            return search_results[0]
        
        return None
        
    except Exception as e:
        logging.error(f"Error searching for {company_name}: {e}")
        return None

def extract_emails(text, email_pattern=r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'):
    """Extract email addresses from text"""
    if not text:
        return []
        
    emails = re.findall(email_pattern, text)
    return list(set(emails))  # Remove duplicates

def extract_instagram(soup, website_url):
    """Extract Instagram handle"""
    # Look for links to Instagram
    instagram_links = soup.select('a[href*="instagram.com"]')
    
    for link in instagram_links:
        href = link.get('href', '')
        # Extract username from URL
        username_match = re.search(r'instagram\.com/([^/?]+)', href)
        if username_match:
            username = username_match.group(1)
            if username not in ['p', 'explore', 'reels']:  # Filter out non-profile pages
                return '@' + username if not username.startswith('@') else username
    
    return None

def extract_linkedin(soup, website_url):
    """Extract LinkedIn profile"""
    linkedin_links = soup.select('a[href*="linkedin.com"]')
    
    for link in linkedin_links:
        href = link.get('href', '')
        if '/company/' in href or '/in/' in href:
            return href
    
    return None

def extract_phone_numbers(text, phone_patterns=None):
    """Extract phone numbers with various formats"""
    if not text:
        return []
        
    # Default patterns if none specified
    if not phone_patterns:
        phone_patterns = [
            r'(?:\+90|0)?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
            r'(?:\+90|0)?\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',
            r'(?:\+90|0)?\s*\d{3}\s*\d{3}\s*\d{4}'
        ]
    
    results = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        results.extend(matches)
    
    # Clean up and standardize
    cleaned = []
    for phone in results:
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Format consistently (assuming Turkish numbers)
        if len(digits) >= 10:
            if digits.startswith('90') and len(digits) >= 12:
                digits = digits[2:]  # Remove country code
            elif digits.startswith('0'):
                digits = digits[1:]  # Remove leading 0
            
            if len(digits) == 10:  # Standard 10-digit Turkish number
                formatted = f"+90 {digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
                cleaned.append(formatted)
    
    return list(set(cleaned))  # Remove duplicates

def extract_address(soup):
    """Extract company address with improved accuracy"""
    # Common elements containing address information
    address_selectors = [
        'address', '.address', '.contact-address', '.footer-address',
        'div[itemtype="http://schema.org/PostalAddress"]', 'div[itemprop="address"]',
        'p:contains("Adres")', 'div:contains("Adres")', 'li:contains("Adres")',
        '.address-info', '.contact-info', '.iletisim', '#iletisim', '.iletişim', '#iletişim',
        '.footer-contact', '.footer li:contains("Adres")'
    ]
    
    for selector in address_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                # Look for text containing address indicators in Turkish
                address_text = ""
                
                # If we find an explicit address label, use the text that follows it
                address_labels = element.find_all(text=re.compile(r'adres|adress|address', re.I))
                for label in address_labels:
                    # Get the parent element
                    parent = label.parent
                    if parent:
                        # Get all text after the label
                        siblings = list(parent.find_next_siblings())
                        if siblings:
                            for sibling in siblings:
                                sibling_text = sibling.get_text(strip=True)
                                if sibling_text and len(sibling_text) > 10:
                                    return sibling_text
                        else:
                            # If no siblings, maybe the address is in the same element
                            full_text = parent.get_text(strip=True)
                            address_part = re.sub(r'.*adres[^:]*:', '', full_text, flags=re.I)
                            if address_part != full_text:  # If we found and removed "Adres:" or similar
                                return address_part.strip()
                
                # If no explicit label found, look for text that looks like an address
                text = element.get_text(strip=True)
                
                # Look for common Turkish address patterns (post code, city names)
                if re.search(r'\b\d{5}\b', text) or re.search(r'\b(İstanbul|Ankara|İzmir|Antalya|Bursa)\b', text, re.I):
                    # Clean up the text
                    address_text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
                    address_text = re.sub(r'^adres[^:]*:\s*', '', address_text, flags=re.I)  # Remove "Adres:" prefix
                    
                    # Remove phone/email info from address text
                    address_text = re.sub(r'(tel|telefon|phone|e-mail|email|mail|fax)[^:]*:.*', '', address_text, flags=re.I)
                    
                    if len(address_text) > 10 and len(address_text) < 200:
                        return address_text

                # Sometimes address is in a more structured format
                if (('mahalle' in text.lower() or 'cadde' in text.lower() or 'sokak' in text.lower() or 
                     'mah.' in text.lower() or 'cad.' in text.lower() or 'sok.' in text.lower()) and
                    (len(text) > 15 and len(text) < 200)):
                    return text
        except Exception as e:
            logging.debug(f"Error extracting address with selector {selector}: {e}")
            continue
    
    # Look for structured data
    script_tags = soup.find_all('script', {'type': 'application/ld+json'})
    for script in script_tags:
        try:
            if 'address' in script.text.lower() or 'postaladdress' in script.text.lower():
                # Try to parse JSON
                import json
                json_data = json.loads(script.text)
                
                # Look for address in the JSON structure
                if isinstance(json_data, dict):
                    if 'address' in json_data:
                        address_obj = json_data['address']
                        if isinstance(address_obj, dict):
                            address_parts = []
                            for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode']:
                                if key in address_obj and address_obj[key]:
                                    address_parts.append(address_obj[key])
                            return ' '.join(address_parts)
        except Exception as e:
            logging.debug(f"Error parsing JSON-LD address data: {e}")
            continue
    
    return None

def extract_about(soup):
    """Extract about/company info with improved cleaning"""
    about_selectors = [
        '.about-us', '.about', '.hakkimizda', '#about', '#hakkimizda', '.kurumsal',
        'section:contains("Hakkımızda")', 'div:contains("Hakkımızda")',
        'div:contains("Hakkında")', 'div:contains("Kurumsal")',
        'div[itemtype="http://schema.org/Organization"]',
    ]
    
    # First try to find dedicated about sections
    for selector in about_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                # Deep clean the element by removing all navigation, menu, and footer elements
                for nav_element in element.select('nav, .menu, .navbar, .navigation, header, footer, .footer, .header, .sidebar, ul.menu, .social-links, .contact-info, .copyright, form, iframe'):
                    nav_element.decompose()
                
                # Remove any elements with common unwanted class names
                for unwanted in element.select('[class*="menu"], [class*="nav"], [class*="social"], [id*="menu"], [id*="nav"], [class*="button"]'):
                    unwanted.decompose()
                    
                # Remove elements that are likely navigation links
                for link in element.find_all('a'):
                    # If link text is short, likely a navigation item
                    if len(link.get_text(strip=True)) < 20:
                        link.decompose()
                
                # Get cleaned text
                text = element.get_text(strip=True)
                if len(text) > 50:  # Likely an about section if it's substantial
                    # Clean up the text
                    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
                    text = re.sub(r'(Hakkımızda|About Us|Kurumsal)[^\w]*', '', text)  # Remove headings
                    
                    # Remove common unwanted text patterns
                    text = re.sub(r'(Ana Sayfa|Home|Anasayfa)[^\w]*', '', text)
                    text = re.sub(r'(İletişim|Contact|Bize Ulaşın)[^\w]*', '', text)
                    text = re.sub(r'(Ürünler|Products|Ürünlerimiz)[^\w]*', '', text)
                    
                    # If text is still too long, extract the most relevant part
                    # Look for paragraphs with company name mentions or "hakkında" etc.
                    if len(text) > 800:
                        sentences = text.split('. ')
                        company_name_pattern = soup.title.string.split('-')[0].strip() if soup.title else ""
                        relevant_sentences = []
                        
                        for sentence in sentences:
                            lower_sentence = sentence.lower()
                            if (company_name_pattern.lower() in lower_sentence or 
                                'hakkında' in lower_sentence or 
                                'kuruluş' in lower_sentence or 
                                'tarih' in lower_sentence or
                                'misyon' in lower_sentence or
                                'vizyon' in lower_sentence):
                                relevant_sentences.append(sentence)
                        
                        if relevant_sentences:
                            text = '. '.join(relevant_sentences[:3]) + '.'
                        else:
                            text = text[:500] + '...'  # First 500 chars with ellipsis
                    
                    return text
        except Exception as e:
            logging.debug(f"Error extracting about info with selector {selector}: {e}")
            continue
    
    # If specific selectors fail, look for meta description as fallback
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and 'content' in meta_desc.attrs:
        content = meta_desc['content']
        if len(content) > 10:  # Only if it's substantial
            return content
    
    # Try to find paragraph with company name
    try:
        company_name_pattern = soup.title.string.split('-')[0].strip() if soup.title else ""
        if company_name_pattern and len(company_name_pattern) > 3:
            for p in soup.find_all('p'):
                p_text = p.get_text(strip=True)
                if company_name_pattern in p_text and len(p_text) > 100:
                    return p_text
    except Exception as e:
        logging.debug(f"Error finding paragraph with company name: {e}")
    
    return None

def scrape_company_website(url, email_pattern=None, phone_patterns=None):
    """Scrape company information from website"""
    if not url:
        return {}
        
    url = clean_url(url)
    if not url:
        return {}
        
    try:
        logging.info(f"Scraping website: {url}")
        
        # Make request with random user agent
        response = requests.get(url, headers=get_random_headers(), timeout=20)
        
        # Check if request was successful
        if response.status_code != 200:
            logging.warning(f"Failed to access {url}, status code: {response.status_code}")
            return {}
            
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all text for email and phone searches
        all_text = soup.get_text()
        
        # Get contact page for better data
        contact_links = soup.select('a[href*="contact"], a[href*="iletisim"], a[href*="iletişim"], a[href*="contact-us"]')
        contact_data = {}
        
        for link in contact_links:
            href = link.get('href')
            if href:
                if href.startswith(('http://', 'https://')):
                    contact_url = href
                else:
                    base_url = url.rstrip('/')
                    href = href.lstrip('/')
                    contact_url = f"{base_url}/{href}"
                    
                try:
                    contact_response = requests.get(contact_url, headers=get_random_headers(), timeout=10)
                    if contact_response.status_code == 200:
                        contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                        contact_text = contact_soup.get_text()
                        all_text += " " + contact_text
                        
                        # Extract data from contact page
                        contact_data = {
                            'emails': extract_emails(contact_text, email_pattern),
                            'instagram': extract_instagram(contact_soup, url),
                            'linkedin': extract_linkedin(contact_soup, url),
                            'phones': extract_phone_numbers(contact_text, phone_patterns),
                            'address': extract_address(contact_soup)
                        }
                        break  # Use the first successful contact page
                except Exception as e:
                    logging.error(f"Error accessing contact page {contact_url}: {e}")
        
        # Get data from main page if contact page didn't provide it
        main_data = {
            'emails': extract_emails(all_text, email_pattern),
            'instagram': extract_instagram(soup, url),
            'linkedin': extract_linkedin(soup, url),
            'phones': extract_phone_numbers(all_text, phone_patterns),
            'address': extract_address(soup),
            'about': extract_about(soup)
        }
        
        # Merge data, preferring contact page data where available
        result = {}
        for key in main_data:
            if key in contact_data and contact_data[key]:
                result[key] = contact_data[key]
            else:
                result[key] = main_data[key]
        
        # Format output
        final_data = {
            'Mail': ', '.join(result.get('emails', [])) if result.get('emails') else None,
            'Instagram': result.get('instagram'),
            'Linkedin': result.get('linkedin'),
            'Telefon': ', '.join(result.get('phones', [])) if result.get('phones') else None,
            'Adres': result.get('address'),
            'Hakkımızda': result.get('about')
        }
        
        return final_data
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {}

def main():
    try:
        # Read the Excel file
        file_path = r'c:\Users\alito\OneDrive\Masaüstü\firmalar\firmalar.xlsx'
        df = pd.read_excel(file_path)
        
        # Check if required columns exist
        required_columns = ['FirmaAdı', 'WebSitesi']
        if not all(col in df.columns for col in required_columns):
            logging.error("Excel dosyasında gerekli sütunlar bulunamadı!")
            return
        
        # Initialize empty columns if they don't exist
        for col in ['Mail', 'Instagram', 'Linkedin', 'Telefon', 'Adres', 'Hakkımızda']:
            if col not in df.columns:
                df[col] = None
        
        # Process each company
        for idx, row in df.iterrows():
            company_name = row['FirmaAdı']
            website = row['WebSitesi']
            
            logging.info(f"Processing company: {company_name}")
            
            # Skip empty company names
            if pd.isna(company_name) or not company_name.strip():
                continue
                
            # If website is missing, search Google
            if pd.isna(website) or not website.strip():
                website = find_website_via_google(company_name)
                df.at[idx, 'WebSitesi'] = website
                time.sleep(2)  # Pause to avoid hitting Google's rate limits
            
            # Scrape website for information
            if website:
                company_data = scrape_company_website(website)
                
                # Update DataFrame with scraped data
                for col, value in company_data.items():
                    if value:  # Only update if we found data
                        df.at[idx, col] = value
                        
                # Save progress periodically
                if idx % 5 == 0:
                    df.to_excel('firmalar_updated.xlsx', index=False)
                    
                # Random delay between requests to avoid being blocked
                time.sleep(random.uniform(1.5, 3.5))
        
        # Save final results
        df.to_excel('firmalar_updated.xlsx', index=False)
        logging.info("Scraping completed successfully!")
        print("İşlem tamamlandı! Sonuçlar 'firmalar_updated.xlsx' dosyasına kaydedildi.")
        
    except Exception as e:
        logging.error(f"Main process error: {e}")
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()