from ollama import Client

client = Client(host='http://localhost:11434')

response = client.chat(
    model='qwen2.5:7b',
    messages=[
        {
            "role": "user",
            "content": "Say hello in one sentence."
        }
    ]
)

print(response["message"]["content"])