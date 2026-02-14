import requests
import time

# Try to login and access visits page
print("Attempting to login and access visits page...")

session = requests.Session()

# First, get the login page to see the form
try:
    login_page = session.get("http://localhost:8000/auth/login")
    print(f"Login page status: {login_page.status_code}")
    
    # Try to login with doctor credentials
    login_data = {
        'username': 'momo',  # صابر المهذبي - is_doc=1
        'password': 'momo'  # Try the username as password
    }
    
    login_response = session.post("http://localhost:8000/auth/login", data=login_data)
    print(f"Login POST status: {login_response.status_code}")
    
    # Check if login was successful (should redirect or show success)
    if login_response.status_code == 200:
        print("Login attempt completed, now accessing visits page...")
        
        # Now try to access the visits page
        visits_response = session.get("http://localhost:8000/clinic/visits")
        print(f"Visits page status: {visits_response.status_code}")
        print(f"Visits page length: {len(visits_response.text)}")
        
        # Look for debug output
        if "CHRONIC DISEASE DEBUG" in visits_response.text:
            print("FOUND DEBUG OUTPUT!")
            lines = visits_response.text.split('\n')
            for i, line in enumerate(lines):
                if 'CHRONIC DISEASE DEBUG' in line:
                    print(f"Debug found at line {i}:")
                    # Print the debug section
                    for j in range(i, min(len(lines), i+15)):
                        print(f"  {lines[j].strip()}")
                        if '===========================' in lines[j]:
                            break
                    break
        else:
            print("No debug output found in response")
            
        # Check if it's still showing login page
        if "login" in visits_response.text.lower() and len(visits_response.text) < 6000:
            print("Still showing login page - authentication failed")
        else:
            print("Not login page - authentication might be successful")
            
            # Look for chronic disease data
            if "chronic-diseases" in visits_response.text:
                print("Found chronic-diseases class in HTML")
                
                # Extract a few rows to see what's happening
                lines = visits_response.text.split('\n')
                for i, line in enumerate(lines):
                    if 'chronic-diseases' in line:
                        print(f"Chronic disease cell found at line {i}:")
                        # Print context around it
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            print(f"  {j}: {lines[j].strip()}")
                        break
                        
    else:
        print(f"Login failed with status {login_response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()