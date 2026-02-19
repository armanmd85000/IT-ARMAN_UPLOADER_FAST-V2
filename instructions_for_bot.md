Here are the instructions to update the other repository with the new Koyeb API integration.

### **Task: Migrate Classplus/DRM Logic to New Koyeb API**

You need to update the API credentials, helper functions, and main processing logic to use the new signed URL endpoint.

---

### **Step 1: Update Variables**
**File:** `vars.py` (or `modules/vars.py`)

Add or update these specific variables. **Ensure you do NOT have these hardcoded in your main file.**

```python
# Koyeb API Configuration
api_url = "https://head-micheline-botupdatevip-f1804c58.koyeb.app"
api_token = "162zCU8mXkpXQX6G4ky"
API_USER_ID = "1621539522"
```

---

### **Step 2: Update Helper Functions**
**File:** `itsgolu.py` (or `modules/saini.py` / `helper.py`)

Add these two functions to handle the response from the new API.

```python
def get_mps_and_keys2(api_url):
    """
    For DRM links (expecting 'mpd_url' and 'keys').
    """
    response = requests.get(api_url)
    response_json = response.json()
    mpd = response_json.get('mpd_url')
    keys = response_json.get('keys')
    return mpd, keys

def get_mps_and_keys3(api_url):
    """
    For Non-DRM links (expecting direct 'url').
    """
    response = requests.get(api_url)
    response_json = response.json()
    mpd = response_json.get('url')
    return mpd
```

---

### **Step 3: Update Main Processing Logic**
**File:** `main.py` (or `modules/drm_handler.py`)

Locate the block that handles `cpvod`, `classplusapp`, or `media-cdn` links. Replace the old API call logic with this:

```python
# 1. Construct the API URL with the correct suffix (@botupdatevip4u) and credentials
api_req_url = f"{api_url}/get_keys?url={url}@botupdatevip4u&user_id={API_USER_ID}&token={api_token}"
print(f"API Call: {api_req_url}")

keys_string = ""
mpd = None

try:
    if "drm/" in url or "cpvod" in url:
        # --- DRM Logic ---
        mpd, keys = helper.get_mps_and_keys2(api_req_url)
        url = mpd
        if keys:
            keys_string = " ".join([f"--key {k}" for k in keys])
        else:
            keys_string = ""
    else:
        # --- Non-DRM Logic (media-cdn, etc.) ---
        mpd = helper.get_mps_and_keys3(api_req_url)
        url = mpd
        keys_string = ""

    print(f"Resolved URL: {url}")

except Exception as e:
    print(f"API request failed: {e}")
    # Optional: Add fallback logic or pass
    pass
```

---

### **Step 4: Critical Checks (Don't skip!)**

1.  **Remove Hardcoding:** Check `main.py` (or the main script) to ensure `api_url` or `api_token` are **NOT** defined there. They must be imported from `vars.py`. If they are defined in `main.py`, they will override your new values and cause the bot to fail.
2.  **Imports:** Ensure you have the necessary imports in your main file:
    ```python
    from vars import *  # To get api_url, api_token, API_USER_ID
    import itsgolu as helper # Or whatever your helper module is named
    ```
