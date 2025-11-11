#!/usr/bin/env python
"""
Helper script to test and troubleshoot Anigold API connection.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

import requests
import json
from django.conf import settings

def test_anigold_api(api_key):
    """Test Anigold API with given key."""
    url = 'http://api.anigoldbot.ir/store/prices/'
    
    print("=" * 60)
    print("🔍 Testing Anigold API Connection")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"API Key: {api_key}")
    print()
    
    # Use apikey header (correct format for Anigold API)
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print("📡 Sending request...")
        response = requests.post(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's a success response
            if isinstance(data, dict):
                is_success = data.get('IsSuccess', True)
                message = data.get('Message', '')
                
                if not is_success:
                    print("❌ API Error:")
                    print(f"   {message}")
                    print()
                    print("💡 Solutions:")
                    print("   1. Check if your API key is correct")
                    print("   2. Contact Anigold support to verify your API key")
                    print("   3. Request a new API key if needed")
                    return False
                elif 'Prices' in data:
                    prices = data['Prices']
                    print(f"✅ SUCCESS! Got {len(prices)} price items")
                    print()
                    if prices:
                        print("Sample prices:")
                        for item in prices[:5]:
                            print(f"   - {item.get('fa_slug', 'N/A')}: {item.get('price', 'N/A')} Rials")
                    return True
            
            # Check if it's an array response
            elif isinstance(data, list):
                print(f"✅ SUCCESS! Got {len(data)} price items")
                print()
                if data:
                    print("Sample prices:")
                    for item in data[:5]:
                        print(f"   - {item.get('fa_slug', 'N/A')}: {item.get('price', 'N/A')} Rials")
                return True
            
            else:
                print("⚠️ Unexpected response format:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        print("   The API server may be down or unreachable")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        print("   Check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print()
    print("🚀 Anigold API Test Utility")
    print()
    
    # Get API key from settings
    api_key = getattr(settings, 'ANIGOLD_API_KEY', None)
    
    if not api_key:
        print("❌ No API key found in settings!")
        print()
        print("Please set ANIGOLD_API_KEY in:")
        print("  - .env file, OR")
        print("  - gold_shop/settings.py")
        return
    
    # Test the API
    success = test_anigold_api(api_key)
    
    print()
    print("=" * 60)
    
    if success:
        print("✅ API is working correctly!")
        print()
        print("Next steps:")
        print("  1. Run: python manage.py update_prices")
        print("  2. Check prices in admin panel")
    else:
        print("❌ API test failed")
        print()
        print("To fix:")
        print("  1. Get a valid API key from Anigold")
        print("  2. Update your .env file:")
        print("     ANIGOLD_API_KEY=your-new-api-key-here")
        print("  3. Or contact Anigold support:")
        print("     http://api.anigoldbot.ir/")
    
    print()


if __name__ == '__main__':
    main()

