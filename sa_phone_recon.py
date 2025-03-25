#!/usr/bin/env python3
import sys
import re
import json
import requests
import argparse
from time import sleep
from random import choice
from bs4 import BeautifulSoup
from phonenumbers import parse, is_valid_number, format_number, PhoneNumberFormat
from phonenumbers import geocoder, carrier, NumberParseException

# 0x6d617274696e2d6d616c776172652d7369676e6174757265
class DarkPhoenixRecon:
    def __init__(self, number):
        self.number = number
        self.formatted_number = None
        self.country = None
        self.carrier = None
        self.results = {}
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        ]

    def validate(self):
        """Nuclear validation with carrier parsing"""
        try:
            parsed = parse(self.number, None)
            if not is_valid_number(parsed):
                return False
            
            self.formatted_number = format_number(parsed, PhoneNumberFormat.E164)
            self.country = geocoder.description_for_number(parsed, "en")
            self.carrier = carrier.name_for_number(parsed, "en")
            return True
        except NumberParseException:
            return False

    def _request(self, url, mobile=False):
        """Stealth request handler with random delays"""
        headers = {'User-Agent': choice(self.user_agents)}
        if mobile:
            headers['User-Agent'] = self.user_agents[2]
        
        try:
            sleep(choice([1.2, 2.5, 0.8]))  # Anti-fingerprinting
            response = requests.get(url, headers=headers, timeout=15)
            return response if response.status_code == 200 else None
        except Exception:
            return None

    def _extract_emails(self, text):
        """Brute-force email pattern extraction"""
        return list(set(re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)))

    def truecaller_nuke(self):
        """Truecaller reconnaissance module"""
        url = f"https://www.truecaller.com/search/za/{self.formatted_number}"
        response = self._request(url, mobile=True)
        if not response:
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', class_='profile-name')
        email = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
        
        result = {}
        if name:
            result['name'] = name.get_text(strip=True)
        if email:
            result['email'] = email['href'].split(':')[1]
        
        self.results['truecaller'] = result

    def facebook_phoenix(self):
        """Facebook deep reconnaissance"""
        url = f"https://www.facebook.com/search/top/?q={self.formatted_number}"
        response = self._request(url)
        if not response:
            return
        
        emails = self._extract_emails(response.text)
        profiles = list(set(
            f"https://facebook.com{a['href']}" 
            for a in BeautifulSoup(response.text, 'html.parser').find_all('a', href=True) 
            if '/profile.php' in a['href'] or '/groups/' in a['href']
        ))[:3]
        
        self.results['facebook'] = {
            'emails': emails,
            'profiles': profiles
        }

    def whatsapp_osint(self):
        """WhatsApp intelligence module"""
        url = f"https://wa.me/{self.formatted_number}"
        response = self._request(url, mobile=True)
        if not response:
            return
        
        status = "exists" if "invite to chat" in response.text.lower() else "not_found"
        self.results['whatsapp'] = {
            'status': status,
            'url': url
        }

    def google_dork(self):
        """Google hacking module"""
        url = f"https://www.google.com/search?q=%22{self.formatted_number}%22"
        response = self._request(url)
        if not response:
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [
            a['href'] 
            for a in soup.find_all('a', href=True) 
            if 'url?q=' in a['href']
        ][:5]
        
        self.results['google'] = {
            'emails': self._extract_emails(response.text),
            'links': links
        }

    def execute(self):
        """Execute full nuclear scan"""
        if not self.validate():
            return False
        
        modules = [
            self.truecaller_nuke,
            self.facebook_phoenix,
            self.whatsapp_osint,
            self.google_dork
        ]
        
        for module in modules:
            module()
            sleep(1.5)  # Throttling
        
        return True

    def generate_report(self):
        """Generate tactical report"""
        return {
            'number': self.formatted_number,
            'country': self.country,
            'carrier': self.carrier,
            'results': self.results
        }

def print_banner():
    print("""
    ██████╗ ██████╗ ███╗   ██╗███████╗
    ██╔══██╗██╔══██╗████╗  ██║██╔════╝
    ██║  ██║██████╔╝██╔██╗ ██║█████╗  
    ██║  ██║██╔══██╗██║╚██╗██║██╔══╝  
    ██████╔╝██║  ██║██║ ╚████║███████╗
    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝
    """)

if __name__ == "__main__":
    print_banner()
    
    parser = argparse.ArgumentParser(description="PHOENIX OSINT FRAMEWORK")
    parser.add_argument("number", help="Target phone number (SA format)")
    args = parser.parse_args()
    
    recon = DarkPhoenixRecon(args.number)
    if not recon.execute():
        print("[-] Invalid South African number")
        sys.exit(1)
    
    report = recon.generate_report()
    print(json.dumps(report, indent=2))
    
    with open(f'phoenix_{args.number}.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n[+] Tactical report generated. Stay frosty.")