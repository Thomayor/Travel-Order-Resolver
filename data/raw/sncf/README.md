# SNCF Open Data - Raw Files

## Overview

This directory contains raw data files downloaded from SNCF Open Data portal for building the French railway network graph.

## Files

### 1. gares-sncf.csv
**Description**: Liste des gares de voyageurs SNCF
**Source**: SNCF Open Data Portal (https://data.sncf.com/)
**Download date**: 2026-01-22
**Format**: CSV, UTF-8 encoding

**Columns**:
- Station name
- UIC station code (unique identifier)
- Latitude / Longitude (GPS coordinates)
- City name
- INSEE code (city code)
- Other metadata

**Usage**: Node data for the railway graph (stations)

---

### 2. horaires-des-gares.csv
**Description**: Horaires d'ouverture des gares (station opening hours)
**Source**: SNCF Open Data Portal
**Download date**: 2026-01-22
**Format**: CSV, UTF-8 encoding

**Note**: This file contains **station opening hours**, NOT train timetables/schedules.

**Columns**:
- Station code
- Opening hours (weekdays, weekends)
- Service availability

**Usage**: Optional metadata (not required for pathfinding)

---

### 3. formes-des-lignes-du-rfn.geojson
**Description**: Formes géométriques des lignes du Réseau Ferré National (RFN)
**Source**: SNCF Open Data Portal
**Download date**: 2026-01-22
**Format**: GeoJSON (LINESTRING geometries)

**Structure**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon1, lat1], [lon2, lat2], ...]
      },
      "properties": {
        "line_code": "...",
        "line_name": "..."
      }
    }
  ]
}
```

**Usage**:
- Extract real railway connections between stations
- Calculate distances between connected stations
- Edge data for the railway graph (connections)

---

## Data Sources

All data downloaded from:
- **Primary source**: https://data.sncf.com/
- **License**: Open Data (Licence Ouverte / Open License)

### Recommended datasets from data.sncf.com:
1. **Gares de voyageurs** (Passenger stations)
2. **Horaires des gares** (Station opening hours)
3. **Formes des lignes du RFN** (Railway line geometries)

**Alternative datasets** (if needed):
- Train schedules: `horaires-des-trains.csv` (not downloaded yet, optional)
- Station facilities: `equipements-des-gares.csv` (not downloaded yet, optional)

---

## Next Steps

### KAN-26: Clean and normalize station names
Process `gares-sncf.csv` to:
- Normalize accents (Gare de l'Est → Gare de l Est)
- Standardize hyphens and spaces
- Remove special characters
- Create station name variants (official name → normalized name)

Output: `data/processed/stations_clean.csv`

### KAN-27: Create station-to-city mapping
Extract mapping from `gares-sncf.csv`:
- Map each station to its city
- Handle cities with multiple stations (e.g., Paris)
- Create city-level gazetteer

Output: `data/processed/city_station_mapping.json`

### KAN-28: Build graph database
Use GeoJSON to extract real railway connections:
- Parse LINESTRING geometries
- Match stations to nearest line endpoints
- Create NetworkX graph with stations as nodes and connections as edges

### KAN-29: Calculate connection weights
From GeoJSON geometries:
- Calculate geographic distance (Haversine formula)
- Estimate travel time (if timetable data available)

---

## Data Quality Notes

### Coverage
- **Stations**: ~3,000 passenger stations in France (gares de voyageurs)
- **Railway lines**: Complete RFN (Réseau Ferré National)
- **Geographic scope**: Metropolitan France + DOM-TOM

### Limitations
- GeoJSON contains physical railway lines, not direct train routes
- No train timetable data included (would require separate dataset)
- Some small local stations may be missing

### Validation Needed (KAN-30)
- [ ] Verify all stations have coordinates
- [ ] Check for orphaned stations (not connected to any line)
- [ ] Validate geographic coordinates (within France bounds)
- [ ] Test sample queries (Paris → Lyon, Toulouse → Marseille)

---

## File Sizes

Approximate file sizes:
- `gares-sncf.csv`: ~500 KB
- `horaires-des-gares.csv`: ~200 KB
- `formes-des-lignes-du-rfn.geojson`: ~50 MB (large file with all line geometries)

**Total**: ~50 MB

---

## Usage Example

```python
import pandas as pd
import json

# Load stations
stations = pd.read_csv('data/raw/sncf/gares-sncf.csv', encoding='utf-8')
print(f"Total stations: {len(stations)}")

# Load railway lines
with open('data/raw/sncf/formes-des-lignes-du-rfn.geojson', 'r', encoding='utf-8') as f:
    railway_lines = json.load(f)
print(f"Total railway lines: {len(railway_lines['features'])}")

# Preview station data
print(stations.head())
```

---

## Changelog

### 2026-01-22 - Initial Download
- Downloaded gares-sncf.csv (station list)
- Downloaded horaires-des-gares.csv (opening hours)
- Downloaded formes-des-lignes-du-rfn.geojson (railway line geometries)
- Created documentation (this README)

---

**Ticket**: KAN-25 - Access and download SNCF open data files ✅ COMPLETED
