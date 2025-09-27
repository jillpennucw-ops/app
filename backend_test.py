#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Salary Inflation Calculator
Tests the /api/calculate-inflation endpoint thoroughly
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

class SalaryInflationAPITester:
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
    
    def test_pre_1991_employment(self):
        """Test pre-1991 employment scenarios"""
        print("\n=== Testing Pre-1991 Employment ===")
        
        test_cases = [
            {"start_date": "1985-06-15", "original_salary": 35000, "description": "Mid-1980s employment"},
            {"start_date": "1975-01-01", "original_salary": 15000, "description": "Mid-1970s employment"},
            {"start_date": "1990-12-31", "original_salary": 45000, "description": "Last day before 1991"}
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['success']:
                response = result['response']
                print(f"✅ Status: {result['status_code']}")
                print(f"   Category: {response.get('category')}")
                print(f"   Original Salary: ${response.get('original_salary'):,.0f}")
                print(f"   Inflation Adjusted: ${response.get('inflation_adjusted_salary'):,.0f}")
                print(f"   Inflation Rate: {response.get('inflation_rate', 0)*100:.2f}%")
                print(f"   Years Elapsed: {response.get('years_elapsed')}")
                
                # Verify pre-1991 logic
                if response.get('category') == "Pre-1991 Employment":
                    if response.get('cola_adjusted_salary') is None and response.get('defacto_paycut') is None:
                        print("✅ Correct: No COLA calculations for pre-1991")
                    else:
                        print("❌ Error: COLA calculations should not exist for pre-1991")
                        self.test_results.append(f"FAIL: Pre-1991 test - unexpected COLA data for {case['start_date']}")
                else:
                    print(f"❌ Error: Expected 'Pre-1991 Employment', got '{response.get('category')}'")
                    self.test_results.append(f"FAIL: Pre-1991 test - wrong category for {case['start_date']}")
            else:
                print(f"❌ Request failed: {result['response']}")
                self.test_results.append(f"FAIL: Pre-1991 test - request failed for {case['start_date']}")
    
    def test_cola_period_employment(self):
        """Test 1991-2021 COLA period employment scenarios"""
        print("\n=== Testing 1991-2021 COLA Period Employment ===")
        
        test_cases = [
            # Test cases that should result in >= $75K after adding $8K (gets +$3K)
            {"start_date": "1995-03-15", "original_salary": 70000, "description": "High salary - should get +$3K COLA", "expected_threshold": "high"},
            {"start_date": "2010-07-01", "original_salary": 67000, "description": "Exactly $75K after +$8K - should get +$3K", "expected_threshold": "high"},
            
            # Test cases that should result in < $75K after adding $8K (gets 4% increase)
            {"start_date": "2000-01-15", "original_salary": 50000, "description": "Medium salary - should get 4% increase", "expected_threshold": "low"},
            {"start_date": "1991-01-01", "original_salary": 30000, "description": "First day of COLA period - low salary", "expected_threshold": "low"},
            {"start_date": "2021-12-31", "original_salary": 66999, "description": "Last day of COLA period - just under threshold", "expected_threshold": "low"},
            
            # Edge case - exactly at boundary
            {"start_date": "2015-06-01", "original_salary": 67000, "description": "Boundary case - exactly $75K after +$8K", "expected_threshold": "high"}
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['success']:
                response = result['response']
                print(f"✅ Status: {result['status_code']}")
                print(f"   Category: {response.get('category')}")
                print(f"   Original Salary: ${response.get('original_salary'):,.0f}")
                print(f"   Inflation Adjusted: ${response.get('inflation_adjusted_salary'):,.0f}")
                print(f"   COLA Adjusted: ${response.get('cola_adjusted_salary'):,.0f}")
                print(f"   De Facto Paycut: ${response.get('defacto_paycut'):,.0f}")
                
                # Verify COLA calculations
                original = response.get('original_salary')
                cola_adjusted = response.get('cola_adjusted_salary')
                
                if response.get('category') == "1991-2021 Employment (COLA Period)":
                    # Verify COLA logic
                    cola_base = original + 8000  # Step 1: Add $8K
                    
                    if case['expected_threshold'] == "high":
                        # Should be >= $75K after +$8K, so gets +$3K
                        expected_cola = cola_base + 3000
                        if abs(cola_adjusted - expected_cola) < 0.01:
                            print("✅ Correct: High threshold COLA calculation (+$3K)")
                        else:
                            print(f"❌ Error: Expected ${expected_cola:,.0f}, got ${cola_adjusted:,.0f}")
                            self.test_results.append(f"FAIL: COLA high threshold calculation wrong for {case['start_date']}")
                    else:
                        # Should be < $75K after +$8K, so gets 4% increase
                        expected_cola = cola_base * 1.04
                        if abs(cola_adjusted - expected_cola) < 0.01:
                            print("✅ Correct: Low threshold COLA calculation (4% increase)")
                        else:
                            print(f"❌ Error: Expected ${expected_cola:,.0f}, got ${cola_adjusted:,.0f}")
                            self.test_results.append(f"FAIL: COLA low threshold calculation wrong for {case['start_date']}")
                    
                    # Verify de facto paycut calculation
                    inflation_adjusted = response.get('inflation_adjusted_salary')
                    expected_paycut = inflation_adjusted - cola_adjusted
                    actual_paycut = response.get('defacto_paycut')
                    
                    if abs(actual_paycut - expected_paycut) < 0.01:
                        print("✅ Correct: De facto paycut calculation")
                    else:
                        print(f"❌ Error: Paycut calculation - expected ${expected_paycut:.2f}, got ${actual_paycut:.2f}")
                        self.test_results.append(f"FAIL: De facto paycut calculation wrong for {case['start_date']}")
                        
                else:
                    print(f"❌ Error: Expected COLA period category, got '{response.get('category')}'")
                    self.test_results.append(f"FAIL: COLA period test - wrong category for {case['start_date']}")
            else:
                print(f"❌ Request failed: {result['response']}")
                self.test_results.append(f"FAIL: COLA period test - request failed for {case['start_date']}")
    
    def test_post_2021_employment(self):
        """Test post-2021 employment scenarios"""
        print("\n=== Testing Post-2021 Employment ===")
        
        test_cases = [
            {"start_date": "2022-01-01", "original_salary": 80000, "description": "First day after COLA period"},
            {"start_date": "2023-06-15", "original_salary": 95000, "description": "Recent employment"},
            {"start_date": "2024-01-01", "original_salary": 120000, "description": "Very recent employment"}
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['success']:
                response = result['response']
                print(f"✅ Status: {result['status_code']}")
                print(f"   Category: {response.get('category')}")
                print(f"   Original Salary: ${response.get('original_salary'):,.0f}")
                print(f"   Inflation Adjusted: ${response.get('inflation_adjusted_salary'):,.0f}")
                
                # Verify post-2021 logic
                if response.get('category') == "Post-2021 Employment":
                    if response.get('cola_adjusted_salary') is None and response.get('defacto_paycut') is None:
                        print("✅ Correct: No COLA calculations for post-2021")
                    else:
                        print("❌ Error: COLA calculations should not exist for post-2021")
                        self.test_results.append(f"FAIL: Post-2021 test - unexpected COLA data for {case['start_date']}")
                else:
                    print(f"❌ Error: Expected 'Post-2021 Employment', got '{response.get('category')}'")
                    self.test_results.append(f"FAIL: Post-2021 test - wrong category for {case['start_date']}")
            else:
                print(f"❌ Request failed: {result['response']}")
                self.test_results.append(f"FAIL: Post-2021 test - request failed for {case['start_date']}")
    
    def test_edge_cases(self):
        """Test exact boundary dates and edge cases"""
        print("\n=== Testing Edge Cases ===")
        
        edge_cases = [
            {"start_date": "1991-01-01", "original_salary": 40000, "description": "Exactly Jan 1, 1991 - first COLA day"},
            {"start_date": "2021-12-31", "original_salary": 60000, "description": "Exactly Dec 31, 2021 - last COLA day"},
            {"start_date": "1990-12-31", "original_salary": 35000, "description": "Day before COLA period"},
            {"start_date": "2022-01-01", "original_salary": 75000, "description": "Day after COLA period"}
        ]
        
        for case in edge_cases:
            print(f"\nTesting: {case['description']}")
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['success']:
                response = result['response']
                print(f"✅ Status: {result['status_code']}")
                print(f"   Category: {response.get('category')}")
                print(f"   Date: {case['start_date']} -> Category: {response.get('category')}")
                
                # Verify correct categorization
                start_date = case['start_date']
                category = response.get('category')
                
                if start_date == "1991-01-01" or start_date == "2021-12-31":
                    if "COLA Period" in category:
                        print("✅ Correct: Boundary date correctly in COLA period")
                    else:
                        print(f"❌ Error: Boundary date {start_date} should be in COLA period")
                        self.test_results.append(f"FAIL: Edge case - wrong category for boundary date {start_date}")
                elif start_date == "1990-12-31":
                    if "Pre-1991" in category:
                        print("✅ Correct: Pre-1991 boundary correctly categorized")
                    else:
                        print(f"❌ Error: {start_date} should be Pre-1991")
                        self.test_results.append(f"FAIL: Edge case - wrong category for pre-1991 boundary")
                elif start_date == "2022-01-01":
                    if "Post-2021" in category:
                        print("✅ Correct: Post-2021 boundary correctly categorized")
                    else:
                        print(f"❌ Error: {start_date} should be Post-2021")
                        self.test_results.append(f"FAIL: Edge case - wrong category for post-2021 boundary")
            else:
                print(f"❌ Request failed: {result['response']}")
                self.test_results.append(f"FAIL: Edge case test - request failed for {case['start_date']}")
    
    def test_invalid_inputs(self):
        """Test invalid input handling"""
        print("\n=== Testing Invalid Inputs ===")
        
        # Future date
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        invalid_cases = [
            {"start_date": future_date, "original_salary": 50000, "description": "Future date", "expected_status": 400},
            {"start_date": "1900-01-01", "original_salary": 25000, "description": "Date before 1913", "expected_status": 400},
            {"start_date": "2023-13-45", "original_salary": 60000, "description": "Invalid date format", "expected_status": 400},
            {"start_date": "not-a-date", "original_salary": 70000, "description": "Non-date string", "expected_status": 400},
            {"start_date": "2020-01-01", "original_salary": -5000, "description": "Negative salary", "expected_status": 422},
            {"start_date": "2020-01-01", "original_salary": 0, "description": "Zero salary", "expected_status": 422}
        ]
        
        for case in invalid_cases:
            print(f"\nTesting: {case['description']}")
            result = self.make_request({
                "start_date": case["start_date"],
                "original_salary": case["original_salary"]
            })
            
            if result['status_code'] == case['expected_status']:
                print(f"✅ Correct error handling: Status {result['status_code']}")
                if isinstance(result['response'], dict) and 'detail' in result['response']:
                    print(f"   Error message: {result['response']['detail']}")
            else:
                print(f"❌ Wrong status code: Expected {case['expected_status']}, got {result['status_code']}")
                print(f"   Response: {result['response']}")
                self.test_results.append(f"FAIL: Invalid input test - wrong status for {case['description']}")
    
    def test_response_format(self):
        """Test response format and required fields"""
        print("\n=== Testing Response Format ===")
        
        result = self.make_request({
            "start_date": "2010-06-15",
            "original_salary": 55000
        })
        
        if result['success']:
            response = result['response']
            required_fields = [
                'original_salary', 'start_date', 'inflation_adjusted_salary',
                'category', 'summary', 'inflation_rate', 'years_elapsed'
            ]
            
            print("Checking required fields:")
            for field in required_fields:
                if field in response:
                    print(f"✅ {field}: {response[field]}")
                else:
                    print(f"❌ Missing field: {field}")
                    self.test_results.append(f"FAIL: Response format - missing field {field}")
            
            # Check COLA-specific fields for COLA period
            if "COLA Period" in response.get('category', ''):
                cola_fields = ['cola_adjusted_salary', 'defacto_paycut']
                print("\nChecking COLA-specific fields:")
                for field in cola_fields:
                    if field in response and response[field] is not None:
                        print(f"✅ {field}: {response[field]}")
                    else:
                        print(f"❌ Missing or null COLA field: {field}")
                        self.test_results.append(f"FAIL: Response format - missing COLA field {field}")
        else:
            print(f"❌ Request failed: {result['response']}")
            self.test_results.append("FAIL: Response format test - request failed")
    
    def test_api_availability(self):
        """Test basic API availability"""
        print("\n=== Testing API Availability ===")
        
        # Test root endpoint
        try:
            root_response = requests.get(f"{self.base_url}/api/", timeout=10)
            if root_response.status_code == 200:
                print("✅ Root API endpoint accessible")
            else:
                print(f"❌ Root API endpoint returned {root_response.status_code}")
                self.test_results.append("FAIL: Root API endpoint not accessible")
        except Exception as e:
            print(f"❌ Root API endpoint failed: {e}")
            self.test_results.append("FAIL: Root API endpoint connection failed")
        
        # Test inflation endpoint with OPTIONS (CORS preflight)
        try:
            options_response = requests.options(self.endpoint, timeout=10)
            print(f"✅ OPTIONS request successful: {options_response.status_code}")
        except Exception as e:
            print(f"❌ OPTIONS request failed: {e}")
            self.test_results.append("FAIL: CORS preflight (OPTIONS) failed")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Salary Inflation Calculator API Tests")
        print(f"Testing endpoint: {self.endpoint}")
        
        self.test_api_availability()
        self.test_response_format()
        self.test_pre_1991_employment()
        self.test_cola_period_employment()
        self.test_post_2021_employment()
        self.test_edge_cases()
        self.test_invalid_inputs()
        
        # Summary
        print("\n" + "="*60)
        print("🏁 TEST SUMMARY")
        print("="*60)
        
        if not self.test_results:
            print("✅ ALL TESTS PASSED! The salary inflation calculator API is working correctly.")
            print("\nKey features verified:")
            print("• Pre-1991 employment: Simple inflation adjustment")
            print("• 1991-2021 COLA period: Complex COLA calculations with threshold logic")
            print("• Post-2021 employment: Simple inflation adjustment")
            print("• Edge case handling: Boundary dates processed correctly")
            print("• Input validation: Proper error handling for invalid inputs")
            print("• Response format: All required fields present")
        else:
            print(f"❌ {len(self.test_results)} TESTS FAILED:")
            for i, failure in enumerate(self.test_results, 1):
                print(f"{i}. {failure}")
        
        return len(self.test_results) == 0

if __name__ == "__main__":
    tester = SalaryInflationAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)