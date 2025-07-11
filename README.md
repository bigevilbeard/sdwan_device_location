# Cisco SD-WAN Site Hierarchy Extractor with Geocoding

A Python tool that extracts site hierarchy information from Cisco SD-WAN Manager API and maps GPS coordinates to human-readable addresses using reverse geocoding.

## Problem Statement

Cisco SD-WAN Manager does not provide a single API endpoint to retrieve the complete site hierarchy from the Network Hierarchy section. This tool solves that limitation by orchestrating multiple API calls to reconstruct the site structure with enhanced location information.

## Features

- **Multi-API Site Extraction**: Combines multiple SD-WAN API endpoints to build complete site hierarchy
- **Reverse Geocoding**: Converts GPS coordinates to city/state/country addresses
- **Site Categorization**: Automatically categorizes sites as Control Plane or Branch sites
- **Network Topology**: Includes TLOC connection information for each device
- **Professional Output**: Clean, enterprise-ready reporting format
- **Data Export**: Saves results in structured JSON format

## Requirements

```bash
pip install requests urllib3
```

## Configuration

Update the configuration section in the script:

```python
# Configuration
BASE_URL = "https://your-sdwan-manager.com"
USERNAME = "your-username"
PASSWORD = "your-password"
```

## Usage

```bash
python3 sdwan_geocoding_clean.py
```

## API Endpoints Used

The tool orchestrates the following Cisco SD-WAN Manager API endpoints:

1. **Primary Data Source**: `GET /dataservice/device`
   - Returns all devices with site-id, location coordinates, and device details
   - Main source for building site hierarchy structure

2. **Network Topology**: `GET /dataservice/device/tloc`
   - Provides network connection information
   - Links to devices via system-ip for connectivity details

3. **Geocoding Service**: OpenStreetMap Nominatim API
   - Converts GPS coordinates to human-readable addresses
   - Free service with 1 request/second rate limiting

## Sample Output

```
Cisco SD-WAN Site Hierarchy Extraction with Geocoding
Target: https://sandbox-sdwan-2.cisco.com

Authenticating...
SUCCESS: Authentication successful

Extracting sites with location mapping...
Getting device data...
Getting TLOC data...
Processing devices and geocoding locations...
Processing device 1/7: vmanage
   Geocoding 37.666684, -122.777023...
Processing device 2/7: vsmart
   Geocoding 37.666684, -122.777023...
Processing device 3/7: vbond
   Geocoding 37.666684, -122.777023...
Processing device 4/7: dc-cedge01
   Geocoding 37.411, -121.932...
Processing device 5/7: site1-cedge01
   Geocoding 35.852, -78.869...
Processing device 6/7: site2-cedge01
   Geocoding 53.277, -8.932...
Processing device 7/7: site3-vedge01
   Geocoding 53.408, -2.228...

================================================================================
CISCO SD-WAN SITES WITH GEOCODED LOCATIONS
================================================================================

Summary: 5 sites discovered
   Control Plane Sites: 1
   Branch Sites: 4

CONTROL PLANE SITES
----------------------------------------

Site 101 (3 devices)
   Location: United States
   City: Unknown City, Unknown State, United States US
   Coordinates: 37.666684, -122.777023
   [ONLINE] vmanage (vmanage)
      System IP: 10.10.1.1, Model: vmanage
      Version: 20.10.1, Platform: x86_64
   [ONLINE] vsmart (vsmart)
      System IP: 10.10.1.5, Model: vsmart
      Version: 20.10.1, Platform: x86_64
   [ONLINE] vbond (vbond)
      System IP: 10.10.1.3, Model: vedge-cloud
      Version: 20.10.1, Platform: x86_64

BRANCH SITES
----------------------------------------

Site 100 (1 devices)
   Device GPS: San Jose, California, United States
   City: San Jose, California, United States US
   Postal Code: 95134
   Coordinates: 37.411, -121.932
   [OFFLINE] dc-cedge01 (vedge)
      System IP: 10.10.1.11, Model: vedge-C8000V
      Version: 17.10.01.0.1479, Platform: x86_64
      Network Connections:
        public-internet: 0 control, 0 BFD
        mpls: 0 control, 0 BFD

Site 1001 (1 devices)
   Device GPS: Morrisville, North Carolina, United States
   City: Morrisville, North Carolina, United States US
   Postal Code: 27560
   Coordinates: 35.852, -78.869
   [ONLINE] site1-cedge01 (vedge)
      System IP: 10.10.1.13, Model: vedge-C8000V
      Version: 17.10.01.0.1479, Platform: x86_64
      Network Connections:
        public-internet: 2 control, 0 BFD
        mpls: 1 control, 0 BFD

Site 1002 (1 devices)
   Device GPS: Éire / Ireland
   City: Unknown City, Unknown State, Éire / Ireland IE
   Postal Code: H91 NN76
   Coordinates: 53.277, -8.932
   [ONLINE] site2-cedge01 (vedge)
      System IP: 10.10.1.15, Model: vedge-C8000V
      Version: 17.10.01.0.1479, Platform: x86_64
      Network Connections:
        public-internet: 1 control, 6 BFD
        mpls: 2 control, 6 BFD

Site 1003 (1 devices)
   Device GPS: Manchester, England, United Kingdom
   City: Manchester, England, United Kingdom GB
   Postal Code: M20 2SP
   Coordinates: 53.408, -2.228
   [ONLINE] site3-vedge01 (vedge)
      System IP: 10.10.1.17, Model: vedge-cloud
      Version: 20.10.1, Platform: x86_64
      Network Connections:
        public-internet: 1 control, 6 BFD
        mpls: 2 control, 6 BFD

LOCATION SUMMARY
----------------------------------------

Countries (3):
   United Kingdom: Site 1003
   United States: Site 101, Site 100, Site 1001
   Éire / Ireland: Site 1002

Cities (5):
   Manchester, England, United Kingdom: Site 1003
   Morrisville, North Carolina, United States: Site 1001
   San Jose, California, United States: Site 100
   Unknown City, Unknown State, United States: Site 101
   Unknown City, Unknown State, Éire / Ireland: Site 1002

Sites with geocoded locations saved to: /Users/stuartclark/Downloads/sdwan_sites_geocoded_clean.json
```

## Output Data Structure

The tool generates a JSON file with the following structure:

```json
{
  "101": {
    "devices": [
      {
        "hostname": "vmanage",
        "system_ip": "10.10.1.1",
        "device_type": "vmanage",
        "device_model": "vmanage",
        "reachability": "reachable",
        "version": "20.10.1",
        "platform": "x86_64",
        "location": {
          "latitude": 37.666684,
          "longitude": -122.777023,
          "is_device_gps": false,
          "geocoded": {
            "display_name": "United States",
            "city": "Unknown City",
            "state": "Unknown State",
            "country": "United States",
            "country_code": "US",
            "postcode": "",
            "formatted_address": "United States"
          }
        }
      }
    ],
    "location": {
      "latitude": 37.666684,
      "longitude": -122.777023,
      "is_device_gps": false,
      "geocoded": {
        "display_name": "United States",
        "city": "Unknown City",
        "state": "Unknown State",
        "country": "United States",
        "country_code": "US",
        "postcode": "",
        "formatted_address": "United States"
      }
    },
    "geocoded_location": {
      "display_name": "United States",
      "city": "Unknown City",
      "state": "Unknown State",
      "country": "United States",
      "country_code": "US",
      "postcode": "",
      "formatted_address": "United States"
    },
    "site_type": "control_plane"
  }
}
```

## Implementation Details

### Multi-Step Process

1. **Authentication**: Authenticate with SD-WAN Manager using form-based login
2. **Device Data Extraction**: Retrieve all devices with location coordinates
3. **Site Grouping**: Group devices by site-id to create site structure
4. **Geocoding**: Convert GPS coordinates to human-readable addresses
5. **Site Categorization**: Classify sites based on device types
6. **Network Topology**: Add TLOC connection information
7. **Report Generation**: Create formatted output and JSON export

### Geocoding Options

The tool uses OpenStreetMap Nominatim (free) by default, but can be extended to support:

- **Google Maps Geocoding API** ($5 per 1000 requests)
- **HERE Geocoding API** (250k/month free tier)
- **MapBox Geocoding API** ($0.50 per 1000 requests)
- **Azure Maps** (Various pricing tiers)

### Rate Limiting

- Implements 1-second delays between geocoding requests
- Caches geocoding results to avoid duplicate API calls
- Includes error handling for failed geocoding requests

## Key Insights

- **No Single API**: SD-WAN Manager lacks a dedicated Network Hierarchy API endpoint
- **Site-ID Grouping**: Sites are reconstructed by grouping devices with the same site-id
- **Implicit Hierarchy**: Site structure is implicit in device data, not explicitly defined
- **Location Enhancement**: Geocoding significantly improves location readability
- **Multi-API Requirement**: Complete site picture requires orchestrating multiple API calls


## Security Considerations

- Store credentials securely (environment variables recommended)
- Use HTTPS for all API communications
- Implement proper error handling for authentication failures
- Consider API rate limiting and throttling
- Validate and sanitize all input data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided as-is for educational and operational purposes. Always test in a non-production environment first. Ensure compliance with your organization's security policies and Cisco's API usage guidelines.

