#!/usr/bin/env python3
import requests
import re
import json
from concurrent.futures import ThreadPoolExecutor
import time
import os
import sys
from bs4 import BeautifulSoup

# Configuration
SA_COUNTRY_CODE = "+27"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
}

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
    """Search Truecaller for SA numbers"""
    try:
        url = f"https://www.truecaller.com/search/za/{phone}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if "not found" in response.text.lower():
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        name_tag = soup.find('h1', class_='profile-name')
        email_tag = soup.find('a', href=re.compile(r'mailto:'))
        
        result = {}
        if name_tag:
            result['name'] = name_tag.get_text(strip=True)
        if email_tag:
            result['email'] = email_tag.get('href').replace('mailto:', '')
        
        return result if result else None
        
    except Exception as e:
        print(f"Truecaller error: {str(e)}")
        return None

def search_facebook(phone):
    """Search Facebook for SA numbers"""
    try:
        url = f"https://www.facebook.com/search/top/?q={phone}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        emails = set(re.findall(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            response.text
        ))
        
        return list(emails) if emails else None
        
    except Exception as e:
        print(f"Facebook error: {str(e)}")
        return None

def search_whatsapp(phone):
    """Check WhatsApp profile for SA numbers"""
    try:
        url = f"https://wa.me/{phone}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if "invite to chat" in response.text.lower():
            return {"status": "WhatsApp account exists"}
        return None
        
    except Exception as e:
        print(f"WhatsApp error: {str(e)}")
        return None

def search_all_platforms(phone):
    """Concurrent search across platforms"""
    results = {}
    platforms = {
        'truecaller': search_truecaller,
        'facebook': search_facebook,
        'whatsapp': search_whatsapp
    }
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_platform = {
            executor.submit(func, phone): name 
            for name, func in platforms.items()
        }
        
        for future in future_to_platform:
            platform = future_to_platform[future]
            try:
                result = future.result()
                if result:
                    results[platform] = result
            except Exception as e:
                print(f"{platform} error: {str(e)}")
    
    return results

def save_results(phone, data):
    """Save results to JSON file"""
    filename = f"za_phone_{phone.replace('+', '')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return filename

def main():
    print("""\033[1;32m
   _____ _                 _____       _           
  / ____| |               / ____|     | |          
 | (___ | |__   ___  ___ | |  __ _ __ | |__  _ __  
  \___ \| '_ \ / _ \/ _ \| | |_ | '_ \| '_ \| '_ \ 
  ____) | | | |  __/ (_) | |__| | |_) | | | | |_) |
 |_____/|_| |_|\___|\___/ \_____| .__/|_| |_| .__/ 
                                | |         | |    
                                |_|         |_|    
    \033[0m""")
    
    phone = input("\nEnter South African phone number (e.g., 0821234567): ").strip()
    
    if not is_south_african_number(phone):
        print("\033[1;31m[-] Invalid South African phone number format\033[0m")
        print("Valid formats: 0821234567 or +27821234567")
        return
    
    clean_phone = clean_number(phone)
    print(f"\n\033[1;34m[+] Investigating SA number: {clean_phone}\033[0m")
    
    print("\n\033[1;36m[+] Searching platforms...\033[0m")
    results = search_all_platforms(clean_phone)
    
    if not results:
        print("\033[1;31m[-] No information found for this number\033[0m")
        return
    
    print("\n\033[1;32m[+] Found associated accounts:\033[0m")
    for platform, data in results.items():
        print(f"\n\033[1;33m{platform.upper()}:\033[0m")
        for key, value in data.items():
            print(f"  {key}: {value}")
    
    filename = save_results(clean_phone, results)
    print(f"\n\033[1;32m[+] Results saved to {filename}\033[0m")

if __name__ == "__main__":
    # Check if running on Kali or Termux
    if not (os.path.exists('/etc/os-release') or 'kali' in open('/etc/os-release').read().lower()):
        if not os.path.exists('/data/data/com.termux/files/home'):
            print("\033[1;31m[-] This script is designed to run on Kali Linux or Termux only\033[0m")
            sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Operation cancelled by user\033[0m")
        sys.exit(0)
