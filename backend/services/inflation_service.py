import requests
import json
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

class InflationService:
    def __init__(self):
        # BLS CPI-U Series ID for All Urban Consumers (1982-84=100)
        self.cpi_series_id = "CUUR0000SA0"
        self.bls_api_url = "https://api.bls.gov/publicAPI/v2/timeseries/data"
        self.cache_file = Path(__file__).parent.parent / "data" / "cpi_cache.json"
        self.ensure_cache_dir()
        
    def ensure_cache_dir(self):
        """Ensure the data directory exists for caching"""
        self.cache_file.parent.mkdir(exist_ok=True)
        
    def get_cpi_data(self, start_year: int, end_year: int) -> Dict:
        """Get CPI data from BLS API with caching"""
        cache_key = f"{start_year}_{end_year}"
        cached_data = self.load_from_cache()
        
        # Check if we have cached data for this range
        if cache_key in cached_data:
            return cached_data[cache_key]
            
        try:
            # BLS API request
            headers = {'Content-type': 'application/json'}
            data = json.dumps({
                "seriesid": [self.cpi_series_id],
                "startyear": str(start_year),
                "endyear": str(end_year)
            })
            
            response = requests.post(self.bls_api_url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result['status'] == 'REQUEST_SUCCEEDED':
                # Cache the successful response
                cached_data[cache_key] = result
                self.save_to_cache(cached_data)
                return result
            else:
                raise Exception(f"BLS API error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error fetching CPI data: {e}")
            # Return fallback historical averages if API fails
            return self.get_fallback_cpi_data(start_year, end_year)
    
    def load_from_cache(self) -> Dict:
        """Load cached CPI data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
        return {}
    
    def save_to_cache(self, data: Dict):
        """Save CPI data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_fallback_cpi_data(self, start_year: int, end_year: int) -> Dict:
        """Fallback CPI data when API is unavailable - using historical averages"""
        # These are approximate historical CPI values for fallback
        fallback_cpi = {
            1913: 9.9, 1920: 20.0, 1930: 16.7, 1940: 14.0, 1950: 24.1,
            1960: 29.6, 1970: 38.8, 1980: 82.4, 1990: 130.7, 1991: 136.2,
            1995: 152.4, 2000: 172.2, 2005: 195.3, 2010: 218.1, 2015: 237.0,
            2020: 258.8, 2021: 271.0, 2022: 292.7, 2023: 307.0, 2024: 310.3
        }
        
        # Generate mock BLS API response format
        series_data = []
        for year in range(start_year, end_year + 1):
            # Interpolate or extrapolate CPI values
            cpi_value = self.interpolate_cpi(year, fallback_cpi)
            series_data.append({
                "year": str(year),
                "period": "M13",  # Annual average
                "value": str(cpi_value)
            })
        
        return {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [{
                    "seriesID": self.cpi_series_id,
                    "data": series_data
                }]
            }
        }
    
    def interpolate_cpi(self, year: int, fallback_cpi: Dict[int, float]) -> float:
        """Interpolate CPI value for a given year"""
        if year in fallback_cpi:
            return fallback_cpi[year]
        
        # Find surrounding years for interpolation
        years = sorted(fallback_cpi.keys())
        
        if year < min(years):
            # Extrapolate backwards (assume 3% inflation)
            base_year = min(years)
            base_cpi = fallback_cpi[base_year]
            years_diff = base_year - year
            return base_cpi / (1.03 ** years_diff)
        
        if year > max(years):
            # Extrapolate forwards (assume 2.5% inflation)
            base_year = max(years)
            base_cpi = fallback_cpi[base_year]
            years_diff = year - base_year
            return base_cpi * (1.025 ** years_diff)
        
        # Interpolate between two known years
        for i in range(len(years) - 1):
            if years[i] <= year <= years[i + 1]:
                y1, y2 = years[i], years[i + 1]
                cpi1, cpi2 = fallback_cpi[y1], fallback_cpi[y2]
                
                # Linear interpolation
                ratio = (year - y1) / (y2 - y1)
                return cpi1 + ratio * (cpi2 - cpi1)
        
        # Default fallback
        return 250.0  # Rough current CPI
    
    def calculate_inflation_rate(self, start_date: str) -> tuple[float, int]:
        """Calculate total inflation rate from start date to now"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        current_year = datetime.now().year
        start_year = start_dt.year
        years_elapsed = current_year - start_year
        
        # Get CPI data for the range
        cpi_data = self.get_cpi_data(start_year, current_year)
        
        # Extract CPI values
        start_cpi = self.extract_cpi_for_year(cpi_data, start_year)
        current_cpi = self.extract_cpi_for_year(cpi_data, current_year)
        
        # Calculate inflation rate
        if start_cpi and current_cpi:
            inflation_rate = (current_cpi - start_cpi) / start_cpi
        else:
            # Fallback to estimated rate
            inflation_rate = 0.025 * years_elapsed  # 2.5% annual average
            
        return inflation_rate, years_elapsed
    
    def extract_cpi_for_year(self, cpi_data: Dict, year: int) -> Optional[float]:
        """Extract CPI value for a specific year from BLS API response"""
        try:
            series = cpi_data['Results']['series'][0]
            for data_point in series['data']:
                if data_point['year'] == str(year) and data_point['period'] == 'M13':
                    return float(data_point['value'])
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error extracting CPI for year {year}: {e}")
        return None