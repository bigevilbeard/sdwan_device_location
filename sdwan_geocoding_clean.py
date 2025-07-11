#!/usr/bin/env python3
"""
Cisco SD-WAN Site Hierarchy with Reverse Geocoding - Clean Version
"""

import requests
import json
import urllib3
from collections import defaultdict
import sys
import time

# Disable SSL warnings for sandbox environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GeocodeService:
    """Service for reverse geocoding GPS coordinates to addresses"""
    
    def __init__(self):
        self.cache = {}  # Cache to avoid repeated API calls
        
    def reverse_geocode_nominatim(self, lat, lon):
        """Use OpenStreetMap Nominatim service (free, no API key required)"""
        if f"{lat},{lon}" in self.cache:
            return self.cache[f"{lat},{lon}"]
        
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'SD-WAN-Location-Mapper/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            time.sleep(1)  # Be respectful to free service
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                location_info = {
                    'display_name': data.get('display_name', 'Unknown Location'),
                    'city': (address.get('city') or 
                            address.get('town') or 
                            address.get('village') or 
                            address.get('hamlet', 'Unknown City')),
                    'state': (address.get('state') or 
                             address.get('province', 'Unknown State')),
                    'country': address.get('country', 'Unknown Country'),
                    'country_code': address.get('country_code', '').upper(),
                    'postcode': address.get('postcode', ''),
                    'formatted_address': self._format_address(address)
                }
                
                self.cache[f"{lat},{lon}"] = location_info
                return location_info
                
        except Exception as e:
            print(f"WARNING: Geocoding failed for {lat},{lon}: {str(e)}")
        
        return {
            'display_name': f'Location at {lat}, {lon}',
            'city': 'Unknown City',
            'state': 'Unknown State', 
            'country': 'Unknown Country',
            'country_code': '',
            'postcode': '',
            'formatted_address': f'{lat}, {lon}'
        }
    
    def _format_address(self, address):
        """Format address components into readable string"""
        components = []
        
        # Add city/town
        city = (address.get('city') or 
                address.get('town') or 
                address.get('village') or 
                address.get('hamlet'))
        if city:
            components.append(city)
        
        # Add state/province
        state = address.get('state') or address.get('province')
        if state:
            components.append(state)
        
        # Add country
        if address.get('country'):
            components.append(address.get('country'))
        
        return ', '.join(components) if components else 'Unknown Location'

class SDWANSiteExtractorWithGeo:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.token = None
        self.geocoder = GeocodeService()
        
    def authenticate(self):
        """Authenticate and get session token"""
        auth_url = f"{self.base_url}/j_security_check"
        auth_data = {
            'j_username': self.username,
            'j_password': self.password
        }
        
        response = self.session.post(auth_url, data=auth_data)
        
        if response.status_code == 200:
            token_url = f"{self.base_url}/dataservice/client/token"
            token_response = self.session.get(token_url)
            if token_response.status_code == 200:
                self.token = token_response.text
                self.session.headers.update({'X-XSRF-TOKEN': self.token})
                return True
        return False
    
    def get_devices(self):
        """Get all devices"""
        url = f"{self.base_url}/dataservice/device"
        response = self.session.get(url)
        return response.json() if response.status_code == 200 else None
    
    def get_tloc_data(self):
        """Get TLOC data for additional network topology info"""
        url = f"{self.base_url}/dataservice/device/tloc"
        response = self.session.get(url)
        return response.json() if response.status_code == 200 else None
    
    def extract_sites_with_geocoding(self):
        """Extract sites and add geocoded location information"""
        
        print("Getting device data...")
        devices_data = self.get_devices()
        if not devices_data or 'data' not in devices_data:
            print("ERROR: Failed to get device data")
            return None
        
        print("Getting TLOC data...")
        tloc_data = self.get_tloc_data()
        
        print("Processing devices and geocoding locations...")
        
        sites = defaultdict(lambda: {
            'devices': [],
            'location': None,
            'geocoded_location': None,
            'site_type': 'unknown'
        })
        
        # Process each device
        for i, device in enumerate(devices_data['data']):
            site_id = device.get('site-id', 'unknown')
            
            print(f"Processing device {i+1}/{len(devices_data['data'])}: {device.get('host-name', 'Unknown')}")
            
            device_info = {
                'hostname': device.get('host-name', 'N/A'),
                'system_ip': device.get('system-ip', 'N/A'),
                'device_type': device.get('device-type', 'N/A'),
                'device_model': device.get('device-model', 'N/A'),
                'reachability': device.get('reachability', 'N/A'),
                'version': device.get('version', 'N/A'),
                'platform': device.get('platform', 'N/A')
            }
            
            # Process location data
            if device.get('latitude') and device.get('longitude'):
                lat = float(device.get('latitude'))
                lon = float(device.get('longitude'))
                
                location_info = {
                    'latitude': lat,
                    'longitude': lon,
                    'is_device_gps': device.get('isDeviceGeoData', False)
                }
                
                # Perform reverse geocoding
                print(f"   Geocoding {lat}, {lon}...")
                geocoded = self.geocoder.reverse_geocode_nominatim(lat, lon)
                location_info['geocoded'] = geocoded
                
                # Use first device's location as site location
                if not sites[site_id]['location']:
                    sites[site_id]['location'] = location_info
                    sites[site_id]['geocoded_location'] = geocoded
                
                device_info['location'] = location_info
            
            # Determine site type
            if device.get('device-type') in ['vmanage', 'vsmart', 'vbond']:
                sites[site_id]['site_type'] = 'control_plane'
            elif sites[site_id]['site_type'] == 'unknown':
                sites[site_id]['site_type'] = 'branch'
            
            sites[site_id]['devices'].append(device_info)
        
        # Add TLOC information if available
        tloc_by_system_ip = {}
        if tloc_data and 'data' in tloc_data:
            for tloc in tloc_data['data']:
                system_ip = tloc.get('system-ip')
                if system_ip:
                    if system_ip not in tloc_by_system_ip:
                        tloc_by_system_ip[system_ip] = []
                    tloc_by_system_ip[system_ip].append({
                        'color': tloc.get('color', 'N/A'),
                        'control_connections_up': tloc.get('controlConnectionsUp', 0),
                        'bfd_sessions_up': tloc.get('bfdSessionsUp', 0)
                    })
        
        # Add TLOC info to devices
        for site_id, site_info in sites.items():
            for device in site_info['devices']:
                system_ip = device['system_ip']
                if system_ip in tloc_by_system_ip:
                    device['tloc_info'] = tloc_by_system_ip[system_ip]
        
        return dict(sites)

def print_geocoded_site_report(sites):
    """Print site report with geocoded location information"""
    
    print("\n" + "="*80)
    print("CISCO SD-WAN SITES WITH GEOCODED LOCATIONS")
    print("="*80)
    
    print(f"\nSummary: {len(sites)} sites discovered")
    
    # Categorize sites
    control_sites = {k: v for k, v in sites.items() if v['site_type'] == 'control_plane'}
    branch_sites = {k: v for k, v in sites.items() if v['site_type'] == 'branch'}
    
    print(f"   Control Plane Sites: {len(control_sites)}")
    print(f"   Branch Sites: {len(branch_sites)}")
    
    # Control Plane Sites
    if control_sites:
        print(f"\nCONTROL PLANE SITES")
        print("-" * 40)
        for site_id, site_info in control_sites.items():
            print(f"\nSite {site_id} ({len(site_info['devices'])} devices)")
            
            if site_info['geocoded_location']:
                geo = site_info['geocoded_location']
                print(f"   Location: {geo['formatted_address']}")
                print(f"   City: {geo['city']}, {geo['state']}, {geo['country']} {geo['country_code']}")
                if geo['postcode']:
                    print(f"   Postal Code: {geo['postcode']}")
                print(f"   Coordinates: {site_info['location']['latitude']}, {site_info['location']['longitude']}")
            
            for device in site_info['devices']:
                status = "ONLINE" if device['reachability'] == 'reachable' else "OFFLINE"
                print(f"   [{status}] {device['hostname']} ({device['device_type']})")
                print(f"      System IP: {device['system_ip']}, Model: {device['device_model']}")
                print(f"      Version: {device['version']}, Platform: {device['platform']}")
    
    # Branch Sites
    if branch_sites:
        print(f"\nBRANCH SITES")
        print("-" * 40)
        for site_id, site_info in branch_sites.items():
            print(f"\nSite {site_id} ({len(site_info['devices'])} devices)")
            
            if site_info['geocoded_location']:
                geo = site_info['geocoded_location']
                loc = site_info['location']
                gps_type = "Device GPS" if loc['is_device_gps'] else "Site Location"
                
                print(f"   {gps_type}: {geo['formatted_address']}")
                print(f"   City: {geo['city']}, {geo['state']}, {geo['country']} {geo['country_code']}")
                if geo['postcode']:
                    print(f"   Postal Code: {geo['postcode']}")
                print(f"   Coordinates: {loc['latitude']}, {loc['longitude']}")
            
            for device in site_info['devices']:
                status = "ONLINE" if device['reachability'] == 'reachable' else "OFFLINE"
                print(f"   [{status}] {device['hostname']} ({device['device_type']})")
                print(f"      System IP: {device['system_ip']}, Model: {device['device_model']}")
                print(f"      Version: {device['version']}, Platform: {device['platform']}")
                
                # Show TLOC info if available
                if 'tloc_info' in device:
                    print(f"      Network Connections:")
                    for tloc in device['tloc_info']:
                        print(f"        {tloc['color']}: {tloc['control_connections_up']} control, {tloc['bfd_sessions_up']} BFD")

def generate_location_summary(sites):
    """Generate a summary of all locations"""
    
    print(f"\nLOCATION SUMMARY")
    print("-" * 40)
    
    countries = defaultdict(list)
    cities = defaultdict(list)
    
    for site_id, site_info in sites.items():
        if site_info['geocoded_location']:
            geo = site_info['geocoded_location']
            country = geo['country']
            city = geo['city']
            
            countries[country].append(f"Site {site_id}")
            cities[f"{city}, {geo['state']}, {country}"].append(f"Site {site_id}")
    
    print(f"\nCountries ({len(countries)}):")
    for country, sites_list in sorted(countries.items()):
        print(f"   {country}: {', '.join(sites_list)}")
    
    print(f"\nCities ({len(cities)}):")
    for city, sites_list in sorted(cities.items()):
        print(f"   {city}: {', '.join(sites_list)}")

def print_api_usage_guide():
    """Print API usage guide"""
    
    print("\n" + "="*80)
    print("API USAGE GUIDE - EXTRACTING SITE HIERARCHY WITH GEOCODING")
    print("="*80)
    
    guide = """
PROBLEM: No single API endpoint provides Network Hierarchy site list

SOLUTION: Multi-step API approach with geocoding enhancement

REQUIRED API CALLS:

1. PRIMARY: GET /dataservice/device
   - Returns all devices with site-id, location, and device details
   - This is your main data source for site hierarchy
   - Group devices by site-id to create site structure

2. SUPPLEMENTARY: GET /dataservice/device/tloc  
   - Provides network topology and connection information
   - Useful for understanding site connectivity
   - Links to devices via system-ip

3. GEOCODING: Reverse geocode GPS coordinates to addresses
   - OpenStreetMap Nominatim (free, no API key)
   - Google Maps, HERE, MapBox (premium options)

IMPLEMENTATION STEPS:

Step 1: Authenticate and get device list
Step 2: Parse device data and group by site-id
Step 3: Extract location data (latitude/longitude)
Step 4: Reverse geocode coordinates to city/address
Step 5: Categorize sites (control plane vs branch)
Step 6: Supplement with TLOC data for network topology
Step 7: Build hierarchical site structure with location info

KEY INSIGHTS:

- Site hierarchy is implicit in the data, not explicit
- site-id is the primary grouping mechanism
- Location data comes from device GPS or site coordinates
- Geocoding converts coordinates to human-readable addresses
- Device types help categorize site purposes
- Multiple API calls are required - no single endpoint solution

LIMITATIONS:

- No dedicated "Network Hierarchy" API endpoint
- Site names must be inferred or manually mapped
- Hierarchical relationships beyond site-id not available via API
- Some site metadata may only be available in the UI
- Geocoding adds external dependency and potential rate limits
"""
    
    print(guide)

def main():
    # Configuration
    BASE_URL = "https://sandbox-sdwan-2.cisco.com"
    USERNAME = "devnetuser"
    PASSWORD = "RG!_Yw919_83"
    
    print("Cisco SD-WAN Site Hierarchy Extraction with Geocoding")
    print(f"Target: {BASE_URL}")
    
    # Initialize extractor
    extractor = SDWANSiteExtractorWithGeo(BASE_URL, USERNAME, PASSWORD)
    
    # Authenticate
    print("\nAuthenticating...")
    if not extractor.authenticate():
        print("ERROR: Authentication failed")
        sys.exit(1)
    print("SUCCESS: Authentication successful")
    
    # Extract sites with geocoding
    print("\nExtracting sites with location mapping...")
    sites = extractor.extract_sites_with_geocoding()
    
    if sites:
        # Generate geocoded report
        print_geocoded_site_report(sites)
        
        # Generate location summary
        generate_location_summary(sites)
        
        # Save results
        output_file = '/Users/stuartclark/Downloads/sdwan_sites_geocoded_clean.json'
        with open(output_file, 'w') as f:
            json.dump(sites, f, indent=2)
        print(f"\nSites with geocoded locations saved to: {output_file}")
        
        # Print usage guide
        print_api_usage_guide()
        
        print("\nCONCLUSION: Site locations successfully mapped to cities and addresses!")
    else:
        print("ERROR: Failed to extract site hierarchy")

if __name__ == "__main__":
    main()
