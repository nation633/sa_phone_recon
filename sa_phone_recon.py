#!/usr/bin/env python3
import requests
import re
import json
from concurrent.futures import ThreadPoolExecutor
import sys
from bs4 import BeautifulSoup
import random

# Configuration
SA_COUNTRY_CODE = "+27"
USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

def display_banner():
    print("""\033[1;31m
    ____                 __        ______          __      _______          __ 
   / __ )____  ____     / /_____  / ____/___  ____/ /__   / ____(_)__  ____/ /_
  / __  / __ \/ __ \   / __/ __ \/ /   / __ \/ __  / _ \ / /_  / / _ \/ __  __/
 / /_/ / /_/ / /_/ /  / /_/ /_/ / /___/ /_/ / /_/ /  __/ /_/ / /  __/ /_/ /   
/_____/\____/\____/   \__/\____/\____/\____/\__,_/\___/\____/_/\___/\__,_/    
                                                                               
    \033[0m""")
    print("""\033[1;31m
                              ____  
                             |    | 
                             |____| 
                             /####/ 
                            /####/  
          /\                /####/   
         /  \              /####/    
        /    \            |====|     
       /      \           |    |     
      /        \          |    |     
     /          \         |    |     
    /            \        |    |     
   /              \       |    |     
  /                \      |    |     
 /                  \     |    |     
/                    \    |____|     
\033[0m""")

def is_south_african_number(phone):
    """Validate South African phone number format"""
    pattern = r'^(\+27|0)[6-8][0-9]{8}$'
    return re.match(pattern, phone) is not None

def clean_number(phone):
    """Normalize SA phone number format"""
    if phone.startswith('0'):
        return SA_COUNTRY_CODE + phone[1:]
    return phone

def search_truecaller(phone):
    """Search Truecaller for SA numbers with improved scraping"""
    try:
        url = f"https://www.truecaller.com/search/za/{phone}"
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors for robustness
        name_selectors = [
            'h1.profile-name',
            'h1[itemprop="name"]',
            'div.profile-detail h1'
        ]
        
        email_selectors = [
            'a[href^="mailto:"]',
            'div.profile-detail a[href*="@"]'
        ]
        
        result = {}
        
        # Extract name
        for selector in name_selectors:
            name_tag = soup.select_one(selector)
            if name_tag:
                result['name'] = name_tag.get_text(strip=True)
                break
        
        # Extract email
        for selector in email_selectors:
            email_tag = soup.select_one(selector)
            if email_tag:
                result['email'] = email_tag.get('href').replace('mailto:', '')
                break
        
        # Extract additional info if available
        info_tags = soup.select('div.profile-detail div.detail')
        if info_tags:
            result['additional_info'] = [tag.get_text(strip=True) for tag in info_tags]
        
        return result if result else None
        
    except Exception as e:
        print(f"\033[1;33m[!] Truecaller search failed: {str(e)}\033[0m")
        return None

def search_facebook(phone):
    """Improved Facebook search with session simulation"""
    try:
        session = requests.Session()
        session.headers.update(get_headers())
        
        # First get the Facebook homepage to simulate a real session
        session.get("https://www.facebook.com", timeout=10)
        
        # Then search for the phone number
        url = f"https://www.facebook.com/search/top/?q={phone}"
        response = session.get(url, timeout=15)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for profile links
        profile_links = soup.select('a[href*="/profile.php"]') or soup.select('a[href*="/groups/"]')
        
        result = {}
        if profile_links:
            result['profiles'] = [link.get('href') for link in profile_links[:3]]
        
        # Extract emails from page
        emails = set(re.findall(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            response.text
        ))
        
        if emails:
            result['emails'] = list(emails)
        
        return result if result else None
        
    except Exception as e:
        print(f"\033[1;33m[!] Facebook search failed: {str(e)}\033[0m")
        return None

def search_whatsapp(phone):
    """Enhanced WhatsApp check with more reliable detection"""
    try:
        url = f"https://web.whatsapp.com/send?phone={phone}"
        response = requests.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
        
        result = {}
        
        # Check for WhatsApp Web interface indicators
        if "use WhatsApp on your phone" in response.text:
            result['status'] = "WhatsApp account exists"
            result['url'] = url
        elif "phone number shared" in response.text.lower():
            result['status'] = "Number shared on WhatsApp"
        else:
            result['status'] = "No WhatsApp account found"
        
        return result
        
    except Exception as e:
        print(f"\033[1;33m[!] WhatsApp check failed: {str(e)}\033[0m")
        return None

def search_google(phone):
    """Search Google for phone number references"""
    try:
        url = f"https://www.google.com/search?q=%22{phone}%22"
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all result links
        results = []
        for g in soup.select('div.g'):
            link = g.select_one('a[href^="http"]')
            if link:
                results.append({
                    'title': link.get_text(),
                    'url': link.get('href')
                })
        
        # Extract emails from results
        emails = set(re.findall(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            response.text
        ))
        
        return {
            'search_results': results[:5],  # Limit to top 5 results
            'emails': list(emails) if emails else None
        }
        
    except Exception as e:
        print(f"\033[1;33m[!] Google search failed: {str(e)}\033[0m")
        return None

def search_all_platforms(phone):
    """Concurrent search across platforms with better error handling"""
    results = {}
    platforms = {
        'truecaller': search_truecaller,
        'facebook': search_facebook,
        'whatsapp': search_whatsapp,
        'google': search_google
    }
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_platform = {
            executor.submit(func, phone): name 
            for name, func in platforms.items()
        }
        
        for future in future_to_platform:
            platform = future_to_platform[future]
            try:
                result = future.result(timeout=30)
                if result:
                    results[platform] = result
            except Exception as e:
                print(f"\033[1;33m[!] {platform} search timed out: {str(e)}\033[0m")
    
    return results

def save_results(phone, data):
    """Save results to JSON file with pretty formatting"""
    filename = f"za_phone_{phone.replace('+', '')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

def main():
    display_banner()
    
    phone = input("\n\033[1;31m[+] Enter South African phone number (e.g., 0821234567): \033[0m").strip()
    
    if not is_south_african_number(phone):
        print("\n\033[1;31m[-] Invalid South African phone number format\033[0m")
        print("Valid formats: 0821234567 or +27821234567")
        return
    
    clean_phone = clean_number(phone)
    print(f"\n\033[1;31m[+] Investigating SA number: {clean_phone}\033[0m")
    
    print("\n\033[1;31m[+] Searching platforms... This may take a moment...\033[0m")
    results = search_all_platforms(clean_phone)
    
    if not results:
        print("\n\033[1;31m[-] No information found for this number\033[0m")
        print("\033[1;33m[!] Try these troubleshooting steps:")
        print("1. Verify the number is active and in use")
        print("2. Check if the number is listed publicly")
        print("3. Try different search methods manually\033[0m")
        return
    
    print("\n\033[1;31m[+] Found associated accounts:\033[0m")
    for platform, data in results.items():
        print(f"\n\033[1;33m{platform.upper()} RESULTS:\033[0m")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"  \033[1;32m{key}:\033[0m")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  \033[1;32m{key}:\033[0m {value}")
        else:
            print(f"  {data}")
    
    filename = save_results(clean_phone, results)
    print(f"\n\033[1;31m[+] Results saved to {filename}\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Operation cancelled by user\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\n\033[1;31m[!] Critical error: {str(e)}\033[0m")
        sys.exit(1)