"""
AI Agent — Live Tool Calling Engine
====================================
Supports both Groq (Free, ultra-fast Llama-3.3-70b) and Anthropic Claude.
The AI model autonomously chooses which database tool to invoke, executes it,
and synthesizes a natural, helpful travel plan response.

Run with:
    python agent.py
"""

import os
import json
from dotenv import load_dotenv

from tools import search_destinations, get_destination_details, estimate_cost, generate_itinerary

load_dotenv()

# --- Anthropic tool format ---
CLAUDE_TOOLS = [
    {
        "name": "search_destinations",
        "description": "Search Pakistan destinations by optional province, district/city, max budget per day (PKR), or category (e.g. mountains, historical, nature, beaches, cultural).",
        "input_schema": {
            "type": "object",
            "properties": {
                "province": {"type": "string", "description": "e.g. KPK, Punjab, Sindh, Balochistan, Gilgit-Baltistan, Azad Kashmir, Islamabad"},
                "district": {"type": "string", "description": "e.g. Swat, Lahore, Karachi, Hunza, Skardu, Quetta, Multan"},
                "max_budget_per_day": {"type": "integer", "description": "Maximum budget per person per day, in PKR"},
                "category": {"type": "string", "description": "e.g. mountains, historical, beaches, nature, cultural, museum"},
            },
        },
    },
    {
        "name": "get_destination_details",
        "description": "Get full details for one destination by its integer id.",
        "input_schema": {
            "type": "object",
            "properties": {"destination_id": {"type": "integer"}},
            "required": ["destination_id"],
        },
    },
    {
        "name": "estimate_cost",
        "description": "Estimate a formula-based trip cost breakdown for a destination id, number of days, and number of people.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_id": {"type": "integer"},
                "days": {"type": "integer"},
                "people": {"type": "integer"},
            },
            "required": ["destination_id", "days"],
        },
    },
    {
        "name": "generate_itinerary",
        "description": "Generate a structured day-by-day itinerary for a destination id and number of days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_id": {"type": "integer"},
                "days": {"type": "integer"},
            },
            "required": ["destination_id", "days"],
        },
    },
]

# --- Groq / OpenAI compatible tool format ---
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_destinations",
            "description": "Search Pakistan destinations by optional province, district/city, max budget per day (PKR), or category (e.g. mountains, historical, nature, beaches, cultural).",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string", "description": "e.g. KPK, Punjab, Sindh, Balochistan, Gilgit-Baltistan, Azad Kashmir, Islamabad"},
                    "district": {"type": "string", "description": "e.g. Swat, Lahore, Karachi, Hunza, Skardu, Quetta, Multan"},
                    "max_budget_per_day": {"type": "integer", "description": "Maximum budget per person per day, in PKR"},
                    "category": {"type": "string", "description": "e.g. mountains, historical, beaches, nature, cultural, museum"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_destination_details",
            "description": "Get full details for one destination by its integer id.",
            "parameters": {
                "type": "object",
                "properties": {"destination_id": {"type": "integer"}},
                "required": ["destination_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_cost",
            "description": "Estimate a formula-based trip cost breakdown for a destination id, number of days, and number of people.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "integer"},
                    "days": {"type": "integer"},
                    "people": {"type": "integer"},
                },
                "required": ["destination_id", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_itinerary",
            "description": "Generate a structured day-by-day itinerary for a destination id and number of days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "integer"},
                    "days": {"type": "integer"},
                },
                "required": ["destination_id", "days"],
            },
        },
    },
]

# Maps a tool name to the actual Python function
TOOL_FUNCTIONS = {
    "search_destinations": search_destinations,
    "get_destination_details": get_destination_details,
    "estimate_cost": estimate_cost,
    "generate_itinerary": generate_itinerary,
}


def run_groq_agent(user_message: str, max_turns: int = 8) -> str:
    """Runs the Groq AI agent with function calling."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise ValueError("GROQ_API_KEY is not configured in .env.")

    from groq import Groq
    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert, warm, and helpful Pakistan Travel AI Assistant. "
                "You have access to tools for querying a real database of 150+ verified destinations in Pakistan. "
                "Always use the available tools to search for destinations, calculate real budget estimates, "
                "fetch destination details, and generate day-by-day itineraries. "
                "Format costs cleanly in PKR with bullet points and emojis."
            )
        },
        {"role": "user", "content": user_message}
    ]

    turns = 0
    while turns < max_turns:
        turns += 1
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        choice = response.choices[0]
        response_msg = choice.message

        # If no tool call was made, return final text
        if not response_msg.tool_calls:
            return response_msg.content or "I have processed your travel inquiry."

        messages.append(response_msg)

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except Exception:
                func_args = {}

            print(f"  [Groq Tool Call] {func_name}({func_args})")
            func = TOOL_FUNCTIONS.get(func_name)
            if func:
                try:
                    result = func(**func_args)
                except Exception as err:
                    result = {"error": str(err)}
            else:
                result = {"error": f"Tool '{func_name}' not recognized."}

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(result),
            })

    return "Reached maximum agent reasoning turns without a final answer."


def run_claude_agent(user_message: str, max_turns: int = 5) -> str:
    """Runs the Claude AI Agent with tool-calling support."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise ValueError("ANTHROPIC_API_KEY is not configured in .env.")

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    messages = [{"role": "user", "content": user_message}]
    turns = 0

    while turns < max_turns:
        turns += 1
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=CLAUDE_TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
            return final_text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if getattr(block, "type", "") != "tool_use":
                continue

            print(f"  [Claude Tool Call] {block.name}({block.input})")
            func = TOOL_FUNCTIONS.get(block.name)
            if func:
                try:
                    result = func(**block.input)
                except Exception as err:
                    result = {"error": str(err)}
            else:
                result = {"error": f"Tool '{block.name}' not recognized."}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return "Reached maximum agent reasoning turns without final answer."


def run_agent(user_message: str, max_turns: int = 5) -> str:
    """
    Unified entry point:
    Uses Groq if GROQ_API_KEY is configured.
    Otherwise uses Anthropic if ANTHROPIC_API_KEY is configured.
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key and groq_key != "your_key_here":
        return run_groq_agent(user_message, max_turns=max_turns)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key and anthropic_key != "your_key_here":
        return run_claude_agent(user_message, max_turns=max_turns)

    raise ValueError("Neither GROQ_API_KEY nor ANTHROPIC_API_KEY is configured in .env.")


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if groq_key and groq_key != "your_key_here":
        print("🇵🇰 Pakistan Travel Agent — AI Mode (Groq Llama / GPT-OSS)")
    elif anthropic_key and anthropic_key != "your_key_here":
        print("🇵🇰 Pakistan Travel Agent — AI Mode (Anthropic Claude)")
    else:
        print("⚠️ No API key found. Add GROQ_API_KEY or ANTHROPIC_API_KEY in .env.")

    print("Type a trip request (or 'quit' to exit)\n")
    while True:
        try:
            user_input = input("You: ")
            if user_input.strip().lower() in ("quit", "exit"):
                break
            if not user_input.strip():
                continue
            answer = run_agent(user_input)
            print(f"\nAgent: {answer}\n")
        except Exception as e:
            print(f"\n[Agent Error]: {e}\n")
