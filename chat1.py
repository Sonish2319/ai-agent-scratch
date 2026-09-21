import ollama

print("Simple Qwen ChatBot Example\n")

print("Type 'exit' to quit the chat.\n")

while True:

    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("GoodByE!")
        break


    response  = ollama.chat(
        model="qwen3:4b",
        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    assistant_message = response["message"]["content"]

    print(f"Qwen: {assistant_message}\n")
    