import requests

# Configuration
base_api_url = "https://covercel.vercel.app/extract_keys"
user_id = "8457494001"  # New user_id provided by user

# Test URLs (from previous message)
test_urls = [
    "https://media-cdn.classplusapp.com/436362/cc/52207a2ffeee4b2f86ff156a8e88593f-sg/master.m3u8",
    "https://media-cdn.classplusapp.com/436362/cc/3f8a8929ca184aa6bac5ca2db66cf9ad-do/master.m3u8"
]

def test_single_url(url):
    # Construct the API request URL as per instructions:
    # https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id={user_id}
    api_req_url = f"{base_api_url}?url={url}@bots_updatee&user_id={user_id}"

    print(f"\n--- Testing URL: {url} ---")
    print(f"API Request: {api_req_url}")

    try:
        response = requests.get(api_req_url, timeout=30)
        print(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print("Response JSON:")
            print(data)
        except ValueError:
            print("Response Text (Not JSON):")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for url in test_urls:
        test_single_url(url)
