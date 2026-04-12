import requests

key = 'AIzaSyDGmy5Q0m9ldm9HtoBUZskckrmdZ-LPEN0'
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={key}'

try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    models = r.json().get('models', [])
    print("Available Generative Models:")
    for m in models:
        # Check if it supports generateContent
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(f"- {m.get('name')}")
            
    # Try testing gemini-1.5-flash
    print("\nTesting gemini-1.5-flash generation...")
    gen_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}'
    resp = requests.post(gen_url, json={'contents': [{'parts': [{'text': 'Hello, are you functional?!'}]}]})
    resp.raise_for_status()
    print("Success:", resp.json()["candidates"][0]["content"]["parts"][0]["text"])
except Exception as e:
    print("Error:", str(e))
    if hasattr(e, "response") and e.response is not None:
        print(e.response.text)
