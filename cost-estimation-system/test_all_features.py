#!/usr/bin/env python3
"""
Comprehensive test suite for Cost Estimation System
Tests all major functionalities via API endpoints
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_PREFIX = f"{BASE_URL}/api"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_header(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{title.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def test_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def test_fail(message):
    print(f"{RED}✗ {message}{RESET}")

def test_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def format_response(response):
    try:
        return json.dumps(response.json(), indent=2)
    except:
        return response.text

# ============================================================================
# TEST 1: Health Check
# ============================================================================
def test_health_check():
    test_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            test_success(f"Backend health check passed: {response.json()}")
            return True
        else:
            test_fail(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Health check error: {str(e)}")
        return False

# ============================================================================
# TEST 2: Get All Estimations (History)
# ============================================================================
def test_get_estimations():
    test_header("TEST 2: Get All Estimations (History)")
    try:
        response = requests.get(f"{API_PREFIX}/estimation/history")
        if response.status_code == 200:
            data = response.json()
            test_success(f"Retrieved {data['total']} estimations")
            print(f"\nResponse:")
            for est in data['estimations'][:3]:  # Show first 3
                print(f"  - ID: {est['id']}, File: {est['filename']}, Total Cost: ${est.get('total_cost', 'N/A')}")
            if len(data['estimations']) > 3:
                print(f"  ... and {len(data['estimations']) - 3} more")
            return True
        else:
            test_fail(f"Get estimations failed: {response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Get estimations error: {str(e)}")
        return False

# ============================================================================
# TEST 3: Get Specific Estimation Detail
# ============================================================================
def test_get_estimation_detail():
    test_header("TEST 3: Get Specific Estimation Detail")
    try:
        # First get all to find valid IDs
        response = requests.get(f"{API_PREFIX}/estimation/history")
        estimations = response.json()['estimations']
        
        if not estimations:
            test_info("No estimations available to test detail view")
            return True
        
        estimation_id = estimations[0]['id']
        detail_response = requests.get(f"{API_PREFIX}/estimation/{estimation_id}")
        
        if detail_response.status_code == 200:
            est = detail_response.json()['estimation']
            test_success(f"Retrieved estimation detail for ID {estimation_id}")
            print(f"\n  Filename: {est.get('filename', 'N/A')}")
            print(f"  Total Cost: ${est.get('total_cost', 'N/A')}")
            print(f"  Material Type: {est.get('extracted_parameters', {}).get('material_type', 'N/A')}")
            print(f"  Cycle Time: {est.get('estimated_cycle_time', 'N/A')} hours")
            return True
        else:
            test_fail(f"Get estimation detail failed: {detail_response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Get estimation detail error: {str(e)}")
        return False

# ============================================================================
# TEST 4: Get Cost Parameters
# ============================================================================
def test_get_parameters():
    test_header("TEST 4: Get Cost Parameters")
    try:
        response = requests.get(f"{API_PREFIX}/parameters")
        if response.status_code == 200:
            data = response.json()
            test_success(f"Retrieved {data['total']} cost parameters")
            print(f"\nParameters:")
            for param in data['parameters']:
                print(f"  - {param.get('parameter_name', 'N/A')}: {param.get('parameter_value', 'N/A')}")
            return True
        else:
            test_fail(f"Get parameters failed: {response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Get parameters error: {str(e)}")
        return False

# ============================================================================
# TEST 5: Create/Update Cost Parameter
# ============================================================================
def test_create_parameter():
    test_header("TEST 5: Create/Update Cost Parameter")
    try:
        param_data = {
            "parameter_name": "Test Parameter",
            "parameter_value": 99.99,
            "is_editable": True
        }
        response = requests.post(f"{API_PREFIX}/parameters", json=param_data)
        if response.status_code in [200, 201]:
            test_success(f"Created/Updated parameter: {param_data['parameter_name']}")
            print(f"\nResponse: {response.json()}")
            return True
        else:
            test_fail(f"Create parameter failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        test_fail(f"Create parameter error: {str(e)}")
        return False

# ============================================================================
# TEST 6: PDF Upload & Feature Extraction
# ============================================================================
def test_pdf_upload():
    test_header("TEST 6: PDF Upload & Feature Extraction")
    try:
        pdf_path = Path("/Users/ashutoshkumarsingh/Desktop/ML & Automation/cost-estimation-system/Costing/Phase 2 RFQ package PC4100/ay30018_10152024103531/AY30018.A.pdf")
        
        if not pdf_path.exists():
            test_info("Sample PDF not found, skipping upload test")
            return True
        
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_PREFIX}/estimation/upload", files=files)
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_success(f"PDF uploaded successfully")
            print(f"\n  Estimation ID: {data.get('estimation_id', data.get('id', 'N/A'))}")
            print(f"  Extracted Data:")
            if data.get('extracted_data'):
                for key, value in list(data['extracted_data'].items())[:5]:
                    print(f"    - {key}: {str(value)[:50]}")
            return True
        else:
            test_fail(f"PDF upload failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        test_fail(f"PDF upload error: {str(e)}")
        return False

# ============================================================================
# TEST 7: Calculate Cost
# ============================================================================
def test_calculate_cost():
    test_header("TEST 7: Calculate Cost")
    try:
        cost_data = {
            "material_cost": 50.00,
            "labor_hours": 5,
            "overhead_percent": 20
        }
        response = requests.post(f"{API_PREFIX}/estimation/calculate", json=cost_data)
        
        if response.status_code in [200, 201]:
            test_success("Cost calculation successful")
            result = response.json()
            print(f"\nResult:")
            print(f"  Input Material Cost: ${cost_data['material_cost']}")
            print(f"  Labor Hours: {cost_data['labor_hours']}")
            print(f"  Overhead: {cost_data['overhead_percent']}%")
            if 'result' in result:
                print(f"  Total Cost: ${result['result'].get('total_cost', 'N/A')}")
            return True
        else:
            test_fail(f"Cost calculation failed: {response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Cost calculation error: {str(e)}")
        return False

# ============================================================================
# TEST 8: Frontend Connectivity
# ============================================================================
def test_frontend_connectivity():
    test_header("TEST 8: Frontend Connectivity")
    try:
        response = requests.get("http://localhost:3001")
        if response.status_code == 200:
            test_success("Frontend is running and accessible")
            return True
        else:
            test_fail(f"Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        test_fail(f"Frontend connectivity error: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def main():
    print(f"\n{BLUE}{'*'*70}{RESET}")
    print(f"{BLUE}{'COST ESTIMATION SYSTEM - COMPREHENSIVE FUNCTIONALITY TEST'.center(70)}{RESET}")
    print(f"{BLUE}{'*'*70}{RESET}")
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health_check()))
    results.append(("Frontend Connectivity", test_frontend_connectivity()))
    results.append(("Get All Estimations", test_get_estimations()))
    results.append(("Get Estimation Detail", test_get_estimation_detail()))
    results.append(("Get Cost Parameters", test_get_parameters()))
    results.append(("Create Cost Parameter", test_create_parameter()))
    results.append(("PDF Upload", test_pdf_upload()))
    results.append(("Calculate Cost", test_calculate_cost()))
    
    # Summary
    test_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}{'ALL TESTS PASSED! ✓'.center(70)}{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
    else:
        print(f"{YELLOW}{'='*70}{RESET}")
        print(f"{YELLOW}{f'{total - passed} test(s) need attention'.center(70)}{RESET}")
        print(f"{YELLOW}{'='*70}{RESET}")

if __name__ == "__main__":
    main()
