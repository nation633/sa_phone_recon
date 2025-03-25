#!/usr/bin/env python3
import requests
import re
import json
import sys
from phonenumbers import parse, is_valid_number, format_number
from phonenumbers.phonenumberutil import NumberParseException
from phonenumbers import PhoneNumberFormat

class PhoneRecon:
    def __init__(self, number):
        self.number = number
        self.valid = False
        self.country = None
        self.carrier = None
        self.results = {}

    def validate_number(self):
        """Validate phone number using phonenumbers library"""
        try:
            parsed = parse(self.number, None)
            self.valid = is_valid_number(parsed)
            self.country = self.get_country_name(parsed)
            self.carrier = self.get_carrier_name(parsed)
            self.number = format_number(parsed, PhoneNumberFormat.E164)
            return True
        except NumberParseException:
            return False

    def get_country_name(self, parsed_number):
        """Get country name from country code"""
        from phonenumbers import geocoder
        return geocoder.description_for_number(parsed_number, "en")

    def get_carrier_name(self, parsed_number):
        """Get carrier name using phonenumbers carrier data"""
        from phonenumbers import carrier
        return carrier.name_for_number(parsed_number, "en")

    def google_search(self):
        """Search Google for phone number references"""
        try:
            url = f"https://www.google.com/search?q=%22{self.number}%22"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            emails = re.findall(r'[\w\.-]+@[\w\.-]+', response.text)
            self.results['google'] = {
                'emails': list(set(emails)),
                'sites': self.extract_links(response.text)
            }
        except Exception as e:
            print(f"Google search error: {str(e)}")

    def extract_links(self, text):
        """Extract links from search results"""
        return re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)

    def numverify_lookup(self, api_key):
        """Use Numverify API for validation (requires API key)"""
        try:
            url = f"http://apilayer.net/api/validate?access_key={api_key}&number={self.number}"
            response = requests.get(url)
            data = response.json()
            
            if data.get('valid'):
                self.results['numverify'] = {
                    'carrier': data.get('carrier'),
                    'line_type': data.get('line_type'),
                    'location': data.get('location')
                }
        except Exception as e:
            print(f"Numverify error: {str(e)}")

    def generate_report(self):
        """Generate final report"""
        return {
            'number': self.number,
            'valid': self.valid,
            'country': self.country,
            'carrier': self.carrier,
            'results': self.results
        }

def main():
    print("""
    ___  _ __  ___  ___  ___  ___  _____ 
   / _ \| '_ \/ __|/ _ \/ _ \/ _ \/ _  |
  | (_) | | | \__ \  __/  __/  __/ (_| |
   \___/|_| |_|___/\___|\___|\___|\__  |
                                  |___/ 
    Educational Phone Number Reconnaissance Tool
    """)
    
    if len(sys.argv) != 2:
        print("Usage: python3 phone_recon.py +1234567890")
        sys.exit(1)

    scanner = PhoneRecon(sys.argv[1])
    
    if not scanner.validate_number():
        print("Invalid phone number")
        sys.exit(1)
        
    print(f"\n[+] Valid {scanner.country} number")
    print(f"[+] Carrier: {scanner.carrier}")
    
    print("\n[+] Conducting Google search...")
    scanner.google_search()
    
    print("\n[+] Saving results...")
    report = scanner.generate_report()
    
    with open('phone_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print("\n[+] Report saved to phone_report.json")

if __name__ == "__main__":
    main()