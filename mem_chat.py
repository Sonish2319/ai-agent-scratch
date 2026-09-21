import ollama

print("Simple Qwen Chatbot")
print("Type 'exit' to quit.\n")

messages = []

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Goodbye!")
        break

    # Add the user's message to the conversation
    messages.append({
        "role": "user",
        "content": user_message
    })

    response = ollama.chat(
        model="qwen3:4b",
        messages=messages
    )

    assistant_message = response["message"]["content"]

    # Qwen's response to the conversation
    messages.append({
        "role": "assistant",
        "content": assistant_message
    })

    print(f"Qwen: {assistant_message}\n")