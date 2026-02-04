# Firestore Setup Guide

## Deploy Security Rules

Your Firestore database is created but has restrictive security rules. To deploy the LegalMind security rules:

### Option 1: Using Firebase CLI (Recommended)

```bash
# Install Firebase CLI if not already installed
npm install -g firebase-tools

# Login to Firebase
firebase login

# From the backend directory, deploy rules
firebase deploy --only firestore:rules --project=legalmind-486106
```

### Option 2: Manual Update in Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: **legalmind-486106**
3. Navigate to **Firestore Database**
4. Click **Rules** tab
5. Replace the default rules with the content from `firestore.rules`
6. Click **Publish**

## Authentication Setup

The Google Firestore client library will automatically use **Application Default Credentials** if available:

### For Local Development

If you're using a local service account key:

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set in `.env.local`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

### For Google Cloud Environment

If running on Google Cloud (App Engine, Cloud Run, Compute Engine):
- Credentials are automatically provided by the environment
- No additional setup needed

## Verify Connection

After updating security rules, test the connection:

```bash
# Restart backend
cd backend
python main_new.py
```

The backend should now successfully connect to Firestore and the API should work.

## Database Collections

Once connected, the following collections will be automatically created:

- `sessions` - Chat session storage
- `messages` - Message history
- `contracts` - Uploaded contract documents
- `clauses` - Extracted contract clauses
- `thinking_logs` - Agent reasoning/thinking process
- `documents` - Generated legal documents

## Project Details

- **Project ID**: legalmind-486106
- **Project Number**: 677928716377
- **Database**: (default)
- **Edition**: Standard Edition
- **Mode**: Firestore Native
- **Location**: Multi-region (nam5 - United States)
- **SLA**: 99.999%
