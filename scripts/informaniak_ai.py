import requests

import requests

URL = "https://api.infomaniak.com/1/ai"
headers = {
  'Authorization': 'Bearer INFOMANIAK_TOKEN',
  'Content-Type': 'application/json',
}
req = requests.request("GET", url = URL , headers = headers)
res = req.json()
print(res)

def process_text_with_infomaniak_ai(text_input):
    url = "https://api.infomaniak.com/1/ai/566/openai/chat/completions"
    headers = {
        "Authorization": "Bearer INFOMANIAK_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3",
        "messages": [{"role": "user", "content": text_input}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

# Example usage
text_input = "Please generate a structured JSON output and no other text with format: entry{name: , surname: } for the following text: Name: Khoa, surname: Khoa"
response = process_text_with_infomaniak_ai(text_input)
print(response)