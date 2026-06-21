#!/usr/bin/env python3
"""
Quick test to verify PDF readings from sample files
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pathlib import Path
import requests

BASE_URL = "http://localhost:8000/api"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_sample_pdfs():
    """Test uploading and reading all sample PDFs"""
    
    pdf_files = [
        "data/sample_aluminum_bracket.pdf",
        "data/sample_steel_shaft.pdf",
        "data/sample_plastic_housing.pdf",
        "data/sample_copper_plate.pdf",
    ]
    
    print_header("🔍 TESTING SAMPLE PDF UPLOADS")
    
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            print(f"❌ {pdf_path} - NOT FOUND")
            continue
        
        filename = Path(pdf_path).name
        print(f"📄 Testing: {filename}")
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = requests.post(f"{BASE_URL}/estimation/upload", files=files)
            
            if response.status_code == 200:
                result = response.json()
                est_id = result.get('estimation_id')
                print(f"   ✅ Upload Success - ID: {est_id}")
                
                # Try to get estimation if ID exists
                if est_id:
                    try:
                        est_response = requests.get(f"{BASE_URL}/estimation/{est_id}")
                        if est_response.status_code == 200:
                            est_data = est_response.json()
                            print(f"   ✅ Read Success - Filename: {est_data.get('filename', 'N/A')}")
                        else:
                            print(f"   ⚠️  Could not read estimation details")
                    except:
                        pass
            else:
                print(f"   ❌ Upload Failed - {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:60]}")
    
    # Get history
    print_header("📊 ESTIMATION HISTORY")
    try:
        response = requests.get(f"{BASE_URL}/estimation/history")
        if response.status_code == 200:
            estimations = response.json()
            print(f"✅ Total estimations in database: {len(estimations)}\n")
            for est in estimations if isinstance(estimations, list) else []:
                if isinstance(est, dict):
                    print(f"   • {est.get('filename', 'N/A'):40} (ID: {est.get('id', 'N/A')})")
        else:
            print(f"❌ Could not retrieve history")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Get parameters
    print_header("💰 COST PARAMETERS")
    try:
        response = requests.get(f"{BASE_URL}/parameters/")
        if response.status_code == 200:
            params = response.json()
            print(f"✅ Total parameters in database: {len(params)}\n")
            for param in params:
                print(f"   • {param.get('name', 'N/A'):30} = {param.get('value', 'N/A')}")
        else:
            print(f"❌ Could not retrieve parameters")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print_header("✅ TEST COMPLETE")

if __name__ == "__main__":
    try:
        # First check if backend is running
        response = requests.get(f"{BASE_URL}/health/status", timeout=2)
        if response.status_code == 200:
            test_sample_pdfs()
        else:
            print("❌ Backend is not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend at http://localhost:8000")
        print("\nPlease start the backend server first:")
        print("   cd backend")
        print("   source venv/bin/activate")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
