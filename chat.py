#!/usr/bin/env python3
"""
Interactive chat with GPT-OSS-120B model
"""
import requests
import json

API_BASE = "http://localhost:8000/v1"
MODEL_NAME = "gpt-oss-120b"

def chat(messages, temperature=0.7, max_tokens=2048):
    """Send chat request to the model"""
    response = requests.post(
        f"{API_BASE}/chat/completions",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        },
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
    print("=" * 60)
    print(f"Interactive Chat with {MODEL_NAME}")
    print("=" * 60)
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("Type 'clear' to start a new conversation")
    print("Type 'system <message>' to set a system prompt")
    print("=" * 60)
    print()

    messages = []

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if user_input.lower() == 'clear':
                messages = []
                print("\nConversation cleared!\n")
                continue

            if user_input.lower().startswith('system '):
                system_msg = user_input[7:].strip()
                messages.insert(0, {"role": "system", "content": system_msg})
                print(f"\nSystem prompt set!\n")
                continue

            messages.append({"role": "user", "content": user_input})

            print("\nAssistant: ", end="", flush=True)
            response = chat(messages)
            print(response)
            print()

            messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
