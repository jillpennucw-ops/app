#!/usr/bin/env python3
"""
BLS Accuracy Test for Salary Inflation Calculator
Tests specific scenarios against known BLS calculator results
"""

import requests
import json
from typing import Dict, Any

class BLSAccuracyTester:
    def __init__(self):
        # Get backend URL from frontend .env file
        self.base_url = self.get_backend_url()
        self.endpoint = f"{self.base_url}/api/calculate-inflation"
        self.test_results = []
        
    def get_backend_url(self) -> str:
        """Get backend URL from frontend .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            print(f"Error reading frontend .env: {e}")
        return "http://localhost:8001"  # fallback
    
    def make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to the inflation endpoint"""
        try:
            response = requests.post(
                self.endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            return {
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': response.status_code == 200
            }
        except requests.exceptions.RequestException as e:
            return {
                'status_code': None,
                'response': f"Request failed: {str(e)}",
                'success': False
            }
    
    def test_bls_accuracy_scenarios(self):
        """Test specific scenarios against known BLS calculator results"""
        print("\n=== Testing BLS Calculator Accuracy ===")
        
        # Test scenarios with expected BLS results
        test_cases = [
            {
                "start_date": "2014-08-01",
                "original_salary": 57500,
                "expected_result": 76277,
                "description": "August 2014 to December 2024 - Primary test case",
                "tolerance": 500  # Allow $500 tolerance
            },
            {
                "start_date": "2020-01-01", 
                "original_salary": 50000,
                "expected_result": None,  # Will calculate expected based on CPI
                "description": "January 2020 to December 2024",
                "tolerance": 300
            },
            {
                "start_date": "2010-06-01",
                "original_salary": 40000, 
                "expected_result": None,  # Will calculate expected based on CPI
                "description": "June 2010 to December 2024",
                "tolerance": 500
            },
            {
                "start_date": "1995-03-01",
                "original_salary": 35000,
                "expected_result": None,  # Will calculate expected based on CPI  
                "description": "March 1995 to December 2024",
                "tolerance": 800
            }
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            print(f"Input: ${case['original_salary']:,} starting {case['start_date']}")
            
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['success']:
                response = result['response']
                calculated_result = response.get('inflation_adjusted_salary')
                inflation_rate = response.get('inflation_rate', 0)
                
                print(f"✅ API Response received")
                print(f"   Calculated Result: ${calculated_result:,.2f}")
                print(f"   Inflation Rate: {inflation_rate*100:.2f}%")
                print(f"   Years Elapsed: {response.get('years_elapsed')}")
                
                # For the primary test case, compare against known BLS result
                if case['expected_result']:
                    difference = abs(calculated_result - case['expected_result'])
                    percentage_diff = (difference / case['expected_result']) * 100
                    
                    print(f"   Expected (BLS): ${case['expected_result']:,.2f}")
                    print(f"   Difference: ${difference:,.2f} ({percentage_diff:.2f}%)")
                    
                    if difference <= case['tolerance']:
                        print(f"✅ ACCURACY TEST PASSED - Within ${case['tolerance']} tolerance")
                    else:
                        print(f"❌ ACCURACY TEST FAILED - Exceeds ${case['tolerance']} tolerance")
                        self.test_results.append(f"FAIL: BLS accuracy test - {case['description']} - difference ${difference:,.2f}")
                else:
                    # For other cases, verify the calculation makes sense
                    expected_rough = self.estimate_inflation_result(case['start_date'], case['original_salary'])
                    rough_difference = abs(calculated_result - expected_rough)
                    rough_percentage = (rough_difference / expected_rough) * 100
                    
                    print(f"   Rough Expected: ${expected_rough:,.2f}")
                    print(f"   Difference: ${rough_difference:,.2f} ({rough_percentage:.2f}%)")
                    
                    if rough_percentage <= 10:  # Allow 10% variance for rough estimates
                        print("✅ REASONABLENESS TEST PASSED")
                    else:
                        print("❌ REASONABLENESS TEST FAILED - Result seems unreasonable")
                        self.test_results.append(f"FAIL: Reasonableness test - {case['description']} - {rough_percentage:.1f}% variance")
                
                # Verify response structure
                required_fields = ['inflation_adjusted_salary', 'inflation_rate', 'original_salary', 'start_date']
                for field in required_fields:
                    if field not in response:
                        print(f"❌ Missing required field: {field}")
                        self.test_results.append(f"FAIL: Missing field {field} in response")
                        
            else:
                print(f"❌ Request failed: {result['response']}")
                self.test_results.append(f"FAIL: BLS accuracy test - request failed for {case['description']}")
    
    def estimate_inflation_result(self, start_date: str, original_salary: float) -> float:
        """Rough estimation for comparison purposes"""
        from datetime import datetime
        
        start_year = datetime.strptime(start_date, '%Y-%m-%d').year
        current_year = 2024
        years_elapsed = current_year - start_year
        
        # Rough historical inflation rates
        if start_year >= 2020:
            avg_inflation = 0.04  # ~4% recent years
        elif start_year >= 2010:
            avg_inflation = 0.025  # ~2.5% 2010s
        elif start_year >= 2000:
            avg_inflation = 0.025  # ~2.5% 2000s
        elif start_year >= 1990:
            avg_inflation = 0.03   # ~3% 1990s
        else:
            avg_inflation = 0.035  # ~3.5% earlier periods
            
        # Compound inflation calculation
        total_inflation = (1 + avg_inflation) ** years_elapsed - 1
        return original_salary * (1 + total_inflation)
    
    def test_api_connectivity(self):
        """Test basic API connectivity"""
        print("\n=== Testing API Connectivity ===")
        
        try:
            # Test root endpoint
            root_response = requests.get(f"{self.base_url}/api/", timeout=10)
            if root_response.status_code == 200:
                print("✅ API endpoint accessible")
                return True
            else:
                print(f"❌ API endpoint returned {root_response.status_code}")
                self.test_results.append("FAIL: API endpoint not accessible")
                return False
        except Exception as e:
            print(f"❌ API connectivity failed: {e}")
            self.test_results.append("FAIL: API connectivity failed")
            return False
    
    def run_bls_accuracy_tests(self):
        """Run BLS accuracy verification tests"""
        print("🎯 Starting BLS Calculator Accuracy Verification")
        print(f"Testing endpoint: {self.endpoint}")
        print("="*60)
        
        # Test connectivity first
        if not self.test_api_connectivity():
            print("❌ Cannot proceed - API not accessible")
            return False
        
        # Run accuracy tests
        self.test_bls_accuracy_scenarios()
        
        # Summary
        print("\n" + "="*60)
        print("🏁 BLS ACCURACY TEST SUMMARY")
        print("="*60)
        
        if not self.test_results:
            print("✅ ALL BLS ACCURACY TESTS PASSED!")
            print("\nKey verification points:")
            print("• August 2014 calculation matches BLS calculator (~$76,277)")
            print("• All test scenarios produce reasonable inflation adjustments")
            print("• API response format includes all required fields")
            print("• Inflation rates and calculations appear accurate")
            return True
        else:
            print(f"❌ {len(self.test_results)} BLS ACCURACY TESTS FAILED:")
            for i, failure in enumerate(self.test_results, 1):
                print(f"{i}. {failure}")
            return False

if __name__ == "__main__":
    tester = BLSAccuracyTester()
    success = tester.run_bls_accuracy_tests()
    exit(0 if success else 1)