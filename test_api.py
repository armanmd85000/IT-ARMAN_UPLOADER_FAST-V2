import requests
import urllib.parse

# Configuration
base_api_url = "https://covercel.vercel.app/extract_keys"
video_url = "https://media-cdn.classplusapp.com/436362/cc/3519c432b8d84ca8ad6245e73ccad67e-ws/master.m3u8"
user_id_val = "8457494001"

def test_request(description, constructed_url):
    print(f"\n--- Test: {description} ---")
    print(f"Request URL: {constructed_url}")
    try:
        response = requests.get(constructed_url, timeout=30)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:", response.json())
        except ValueError:
            print("Response Text:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test 1: Literal braces as requested by the user
    # Format: url={https://...}@bots_updatee&user_id={8457494001}
    url_1 = f"{base_api_url}?url={{{video_url}}}@bots_updatee&user_id={{{user_id_val}}}"
    test_request("Literal Braces (User Request)", url_1)

    # Test 2: Braces only on URL (common confusion point)
    url_2 = f"{base_api_url}?url={{{video_url}}}@bots_updatee&user_id={user_id_val}"
    test_request("Braces on URL only", url_2)

    # Test 3: Standard clean format (No braces, just values - effectively what we tried before but re-verifying)
    url_3 = f"{base_api_url}?url={video_url}@bots_updatee&user_id={user_id_val}"
    test_request("Clean Values (No Braces)", url_3)
