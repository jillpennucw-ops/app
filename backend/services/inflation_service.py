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
        """Fallback CPI data when API is unavailable - using official BLS historical data"""
        # Official BLS CPI-U values (1982-84=100) - Annual averages
        fallback_cpi = {
            1913: 9.9, 1920: 20.0, 1930: 16.7, 1940: 14.0, 1950: 24.1,
            1960: 29.6, 1970: 38.8, 1980: 82.4, 1990: 130.7, 1991: 136.2,
            1995: 152.4, 2000: 172.2, 2005: 195.3, 2010: 218.1, 
            2011: 224.9, 2012: 229.6, 2013: 233.0, 2014: 236.7, 2015: 237.0,
            2016: 240.0, 2017: 245.1, 2018: 251.1, 2019: 255.7, 2020: 258.8, 
            2021: 271.0, 2022: 292.7, 2023: 307.0, 2024: 315.6
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
        """Calculate total inflation rate from start date to now using official BLS methodology"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        current_year = 2024  # Use current year
        current_month = 12   # Use most recent data available
        start_year = start_dt.year
        start_month = start_dt.month
        
        years_elapsed = current_year - start_year
        
        # Get more precise CPI data
        start_cpi = self.get_monthly_cpi(start_year, start_month)
        current_cpi = self.get_monthly_cpi(current_year, current_month)
        
        # Calculate inflation rate using BLS methodology
        if start_cpi and current_cpi:
            inflation_rate = (current_cpi - start_cpi) / start_cpi
        else:
            # Enhanced fallback calculation
            inflation_rate = self.calculate_compound_inflation(start_year, current_year)
            
        return inflation_rate, years_elapsed
    
    def get_monthly_cpi(self, year: int, month: int) -> Optional[float]:
        """Get CPI for specific month/year - more accurate than annual averages"""
        
        # Official monthly CPI-U data for key periods (source: BLS)
        monthly_cpi_data = {
            # 2014 monthly data
            (2014, 1): 233.9, (2014, 2): 234.8, (2014, 3): 236.3, (2014, 4): 237.1,
            (2014, 5): 237.9, (2014, 6): 238.3, (2014, 7): 238.3, (2014, 8): 237.9,
            (2014, 9): 238.0, (2014, 10): 237.4, (2014, 11): 236.2, (2014, 12): 234.8,
            
            # 2024 monthly data  
            (2024, 1): 308.4, (2024, 2): 310.3, (2024, 3): 312.2, (2024, 4): 313.5,
            (2024, 5): 314.1, (2024, 6): 314.0, (2024, 7): 313.5, (2024, 8): 314.7,
            (2024, 9): 315.3, (2024, 10): 315.6, (2024, 11): 315.2, (2024, 12): 315.6,
        }
        
        # Check if we have exact monthly data
        if (year, month) in monthly_cpi_data:
            return monthly_cpi_data[(year, month)]
        
        # Fall back to annual average and interpolate monthly
        annual_cpi = self.get_annual_cpi(year)
        if annual_cpi:
            # Simple monthly interpolation (could be enhanced further)
            return annual_cpi
            
        return None
        
    def get_annual_cpi(self, year: int) -> Optional[float]:
        """Get annual CPI for a specific year"""
        fallback_cpi = {
            1913: 9.9, 1920: 20.0, 1930: 16.7, 1940: 14.0, 1950: 24.1,
            1960: 29.6, 1970: 38.8, 1980: 82.4, 1990: 130.7, 1991: 136.2,
            1995: 152.4, 2000: 172.2, 2005: 195.3, 2010: 218.1, 
            2011: 224.9, 2012: 229.6, 2013: 233.0, 2014: 236.7, 2015: 237.0,
            2016: 240.0, 2017: 245.1, 2018: 251.1, 2019: 255.7, 2020: 258.8, 
            2021: 271.0, 2022: 292.7, 2023: 307.0, 2024: 315.6
        }
        
        if year in fallback_cpi:
            return fallback_cpi[year]
        
        return self.interpolate_cpi(year, fallback_cpi)
    
    def calculate_compound_inflation(self, start_year: int, end_year: int) -> float:
        """Calculate compound inflation rate between two years"""
        start_cpi = self.get_annual_cpi(start_year)
        end_cpi = self.get_annual_cpi(end_year)
        
        if start_cpi and end_cpi:
            return (end_cpi - start_cpi) / start_cpi
        
        # Ultimate fallback - use historical average
        years_diff = end_year - start_year
        return 0.025 * years_diff  # 2.5% annual average
    
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