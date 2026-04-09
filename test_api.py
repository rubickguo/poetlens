
import requests
import base64
import io
from PIL import Image

def test():
    # Create a small red image
    img = Image.new('RGB', (100, 100), color = 'red')
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    url = "http://127.0.0.1:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "qwen", # Try generic name, usually ignored or use what we saw
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
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
        "max_tokens": 100
    }

    try:
        print(f"Sending request to {url}...")
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
