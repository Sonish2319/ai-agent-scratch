import ollama

response = ollama.chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": "Hello Qwen, can you tell me a joke?"
        }
    ]
)

print(response["message"]["content"])