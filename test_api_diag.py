
import requests
import base64
import io
import json
from PIL import Image

API_URL = "http://127.0.0.1:1234/v1/chat/completions"

def test_tiny_image():
    print("Creating tiny 64x64 test image...")
    # Create a tiny red square
    img = Image.new('RGB', (64, 64), color = 'red')
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    payload = {
        "model": "qwen",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in one word."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }

    print(f"Sending request to {API_URL}...")
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success! Response:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return True
        else:
            print("Failed! Error response:")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_tiny_image()
