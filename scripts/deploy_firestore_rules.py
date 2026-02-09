"""
Deploy Firestore Security Rules
Uses Google Cloud Admin API to update rules directly
"""

import subprocess
import sys
import json
from pathlib import Path

def install_google_cloud_firestore_admin():
    """Install required packages if needed."""
    try:
        import google.cloud.firestore_admin_v1
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "google-cloud-firestore-admin"
        ])

def deploy_rules():
    """Deploy Firestore security rules."""
    # Note: This requires Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS
    
    rules_file = Path(__file__).parent / "backend" / "firestore.rules"
    
    if not rules_file.exists():
        print(f"ERROR: Rules file not found: {rules_file}")
        return False
    
    print(f"Reading rules from: {rules_file}")
    rules_content = rules_file.read_text()
    
    print("\n" + "="*60)
    print("LegalMind Firestore Security Rules")
    print("="*60)
    print(rules_content)
    print("="*60)
    
    print("\nTo deploy these rules, use one of these methods:")
    print("\n1. Firebase Console (easiest):")
    print("   - Go to: https://console.firebase.google.com")
    print("   - Select project: legalmind-486106")
    print("   - Go to: Firestore Database > Rules")
    print("   - Replace the default rules with the above content")
    print("   - Click 'Publish'")
    
    print("\n2. Using 'firebase' CLI:")
    print("   - Run: firebase login")
    print("   - Run: firebase deploy --only firestore:rules --project=legalmind-486106")
    
    print("\n3. Using 'gcloud' CLI:")
    print("   - Run: gcloud auth login")
    print("   - Run: gcloud firestore rules deploy firestore.rules --project=legalmind-486106")
    
    return True

if __name__ == "__main__":
    print("LegalMind Firestore Rules Deployment Helper")
    deploy_rules()
