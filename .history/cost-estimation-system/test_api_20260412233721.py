#!/usr/bin/env python3
"""
Test script to verify PDF reading and cost estimation functionality
"""

import sys
import os
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

BASE_URL = "http://localhost:8000/api"

def test_health_check():
    """Test if the API is running"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health/status")
        if response.status_code == 200:
            print(f"✓ Health Check Passed: {response.json()}")
            return True
        else:
            print(f"✗ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_get_parameters():
    """Test getting cost parameters"""
    print("\n🔍 Testing Get Parameters...")
    try:
        response = requests.get(f"{BASE_URL}/parameters/")
        if response.status_code == 200:
            params = response.json()
            print(f"✓ Retrieved {len(params)} parameters")
            for param in params[:3]:
                print(f"  - {param.get('name', 'N/A')}: {param.get('value', 'N/A')}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_upload_pdf():
    """Test uploading a PDF file"""
    print("\n🔍 Testing PDF Upload...")
    pdf_path = Path("data/sample_aluminum_bracket.pdf")
    
    if not pdf_path.exists():
        print(f"✗ Sample PDF not found: {pdf_path}")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('sample_aluminum_bracket.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/estimation/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ PDF Upload Successful")
            print(f"  - Estimation ID: {result.get('id', 'N/A')}")
            print(f"  - Filename: {result.get('filename', 'N/A')}")
            return result.get('id')
        else:
            print(f"✗ Upload Failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_estimate_cost(estimation_id):
    """Test generating cost estimation"""
    print(f"\n🔍 Testing Cost Estimation (ID: {estimation_id})...")
    try:
        response = requests.post(f"{BASE_URL}/estimation/estimate/{estimation_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Cost Estimation Generated")
            if 'cost_breakdown' in result:
                breakdown = result['cost_breakdown']
                print(f"  - Raw Material Cost: ${breakdown.get('raw_material_cost', 0):.2f}")
                print(f"  - Machining Cost: ${breakdown.get('machining_cost', 0):.2f}")
                print(f"  - Labor Cost: ${breakdown.get('labor_cost', 0):.2f}")
                print(f"  - Total Cost: ${breakdown.get('total_cost', 0):.2f}")
            return True
        else:
            print(f"✗ Estimation Failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_get_history():
    """Test getting estimation history"""
    print("\n🔍 Testing Estimation History...")
    try:
        response = requests.get(f"{BASE_URL}/estimation/history")
        if response.status_code == 200:
            estimations = response.json()
            print(f"✓ Retrieved {len(estimations)} estimations")
            for est in estimations[:3]:
                print(f"  - {est.get('filename', 'N/A')} (ID: {est.get('id', 'N/A')})")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("AI-DRIVEN COST ESTIMATION SYSTEM - TEST SUITE")
    print("=" * 60)
    
    # Test health
    if not test_health_check():
        print("\n⚠️  Backend is not running. Please start the backend server first:")
        print("   cd backend && source venv/bin/activate && uvicorn main:app --reload")
        return
    
    # Test parameters
    test_get_parameters()
    
    # Test PDF upload
    est_id = test_upload_pdf()
    
    # Test cost estimation if upload was successful
    if est_id:
        test_estimate_cost(est_id)
    
    # Test history
    test_get_history()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
