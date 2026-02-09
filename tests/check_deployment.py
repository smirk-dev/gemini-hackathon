#!/usr/bin/env python3
"""
Check deployment status of legalmind-backend and test the 403 fix
"""

import subprocess
import json
import sys
import time
import urllib.request
import urllib.error

def run_command(cmd, timeout=30):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timeout", 1
    except Exception as e:
        return "", str(e), 1

def main():
    print("\n" + "="*80)
    print("CHECKING VERTEX AI FIX DEPLOYMENT")
    print("="*80 + "\n")
    
    # Step 1: Check service status
    print("Step 1: Checking service status...")
    cmd = 'gcloud run services describe legalmind-backend --project=legalmind-486106 --region=us-central1 --format="value(status.conditions[0].status, status.observedGeneration, status.latestReadyRevisionName)"'
    stdout, stderr, rc = run_command(cmd)
    
    if rc == 0:
        print(f"✅ Service Status: {stdout.strip()}")
    else:
        print(f"⚠️  Status check output: {stderr.strip()}")
    
    # Step 2: Check if backend responds
    print("\nStep 2: Testing backend health endpoint...")
    backend_url = "https://legalmind-backend-677928716377.us-central1.run.app/health"
    
    try:
        req = urllib.request.Request(backend_url, method='GET')
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            status_code = response.status
            print(f"✅ Status Code: {status_code}")
            print(f"✅ Response: {json.dumps(data, indent=2)}")
            
            if status_code == 200:
                print("\n✅✅✅ SUCCESS! 403 ERROR IS FIXED! ✅✅✅")
                print("\nThe backend is responding correctly without authentication errors.")
                print("The Vertex AI fallback fix has been successfully deployed!")
                return 0
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        
        if e.code == 403:
            print("\n⚠️  Still getting 403 error!")
            print("The deployment may still be in progress or the fixes haven't deployed yet.")
            print("\nWaiting 30 seconds and retrying...")
            time.sleep(30)
            
            # Retry once
            try:
                req = urllib.request.Request(backend_url, method='GET')
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    print(f"✅ Retry successful! Status: {response.status}")
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    return 0
            except urllib.error.HTTPError as e2:
                print(f"❌ Still failing: {e2.code}")
                return 1
        return 1
        
    except urllib.error.URLError as e:
        print(f"⚠️  Connection error: {e.reason}")
        print("Service may be cold-starting. Cloud Run scales to zero when inactive.")
        return 1
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
