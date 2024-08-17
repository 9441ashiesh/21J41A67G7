import requests
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Global configuration
WINDOW_SIZE = 10
stored_numbers = []
auth_token = None
token_expires_at = 0

# API endpoints for different number types
API_ENDPOINTS = {
    'p': "http://20.244.56.144/test/primes",
    'f': "http://20.244.56.144/test/fibo",
    'e': "http://20.244.56.144/test/even",
    'r': "http://20.244.56.144/test/rand"
}

# Authentication details
auth_url = "http://20.244.56.144/test/auth"
auth_payload = {
    "companyName": "goMart",
    "clientID": "fca9595d-42c3-462e-ba1b-71d4640faab6",
    "clientSecret": "towUjxWQQGsuDLws",
    "ownerName": "Rahul",
    "ownerEmail": "ashieshmittapalli@gmail.com",
    "rollNo": "21J41A67G7"
}

def get_auth_token():
    """Fetch a new authorization token."""
    global auth_token, token_expires_at
    try:
        response = requests.post(auth_url, json=auth_payload)
        auth_data = response.json()
        auth_token = auth_data.get("access_token")
        expires_in = auth_data.get("expires_in")
        token_expires_at = time.time() + expires_in
        print("New token acquired:", auth_token)
    except requests.exceptions.RequestException as e:
        print(f"Failed to get auth token: {e}")


##################################### TASK 1 #####################################
def fetch_numbers(number_id):
    """Fetch numbers from the test server based on the number ID."""
    global auth_token
    try:
        start_time = time.time()
        print(f"Fetching numbers for ID: {number_id}...")

        if not auth_token or time.time() >= token_expires_at:
            get_auth_token()

        headers = {
            "Authorization": f"Bearer {auth_token}"
        }

        response = requests.get(API_ENDPOINTS[number_id], headers=headers, timeout=0.5)
        elapsed_time = time.time() - start_time
        print(f"Request completed in {elapsed_time} seconds with status code {response.status_code}.")

        if response.status_code == 200 and elapsed_time < 0.5:
            numbers = response.json().get("numbers", [])
            print(f"Numbers received: {numbers}")
            return numbers
        else:
            print("Request failed or took too long. Attempting to refresh token and retry...")
            # Refresh token and retry
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"

            # Retry the request with the new token
            response = requests.get(API_ENDPOINTS[number_id], headers=headers, timeout=0.5)
            elapsed_time = time.time() - start_time
            print(f"Retry request completed in {elapsed_time} seconds with status code {response.status_code}.")

            if response.status_code == 200 and elapsed_time < 0.5:
                print(response.json())
                numbers = response.json().get("numbers", [])
                print(f"Numbers received on retry: {numbers}")
                return numbers
            else:
                print("Retry failed or took too long.")
    except requests.exceptions.Timeout:
        print("Request timed out.")
        # Refresh token and retry in case of timeout
        get_auth_token()
        headers["Authorization"] = f"Bearer {auth_token}"

        # Retry the request with the new token
        try:
            response = requests.get(API_ENDPOINTS[number_id], headers=headers, timeout=0.5)
            if response.status_code == 200:
                numbers = response.json().get("numbers", [])
                print(f"Numbers received on retry after timeout: {numbers}")
                return numbers
        except requests.exceptions.RequestException as e:
            print(f"Retry failed with exception: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed with exception: {e}")

    return []


@app.route('/numbers/<number_id>', methods=['GET'])
def get_numbers(number_id):
    global stored_numbers

    if number_id not in API_ENDPOINTS:
        return jsonify({"error": "Invalid number ID"}), 400

    # Fetch new numbers from the test server
    new_numbers = fetch_numbers(number_id)
    
    if not new_numbers:
        print("No new numbers were fetched.")
    
    # Store previous state
    window_prev_state = stored_numbers.copy()

    # Add unique numbers to the stored list
    for number in new_numbers:
        if number not in stored_numbers:
            stored_numbers.append(number)
        if len(stored_numbers) > WINDOW_SIZE:
            stored_numbers.pop(0)  # Maintain the window size by removing the oldest number

    # Calculate the average of the current window
    avg = round(sum(stored_numbers) / len(stored_numbers), 2) if stored_numbers else 0.00

    # Prepare the response
    response = {
        "numbers": new_numbers,
        "windowPrevState": window_prev_state,
        "windowCurrState": stored_numbers,
        "avg": avg
    }

    print(f"Response: {response}")
    
    return jsonify(response), 200

######################################### TASK 2 ########################################


if __name__ == '__main__':
    # Initially get the auth token
    get_auth_token()
    app.run(port=9876, debug=True)
