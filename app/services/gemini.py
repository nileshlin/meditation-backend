import json
from typing import List

from google import genai
from google.genai import types

from app.config.settings import settings
from app.config.logger import logger
from app.database.models import Message, MessageRole


class GeminiService:
    _client: genai.Client | None = None
    _model_name: str | None = None

    def __init__(self):
        if GeminiService._client is None:
            GeminiService._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            GeminiService._model_name = settings.GEMINI_MODEL

        self.client = GeminiService._client
        self.model = GeminiService._model_name

    # conversation
    async def generate_agent_response(self, messages: List[Message]) -> str:
        if not messages:
            return (
                "Welcome! I'm here to help you create a personalized meditation. "
                "What kind of meditation experience are you looking for today?"
            )

        history = []
        for msg in messages[:-1]:
            role = "user" if msg.role == MessageRole.USER else "model"

            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

        current_user_message = messages[-1].content

        system_instruction = (
            "You are a calm and attentive meditation preparation assistant. "
            "Your ONLY task is to gently gather information from the user to create a truly personalized guided meditation. "
            "Ask ONE natural, warm follow-up question at a time. "
            "Do NOT explain meditation types, do NOT give examples of styles, do NOT suggest anything, "
            "do NOT share information about meditation, do NOT teach or advise — just listen and ask the next clarifying question.\n\n"
            
            "Focus ONLY on these dimensions (one question at a time):\n"
            "• What kind of feeling or experience they are hoping to have\n"
            "• How experienced they are with guided meditation or stillness practices\n"
            "• Current emotional / mental / physical state\n"
            "• Main goal or intention right now\n"
            "• Any specific theme, image, or quality they want to feel\n" 
            "• Preferred length of the session (in minutes)\n\n"
            
            "Rules:\n"
            "1. Ask only ONE question per response.\n"
            "2. Keep your message very short (1–2 sentences maximum).\n"
            "3. Be warm, gentle, and present — never instructive or explanatory.\n"
            "4. After 2–3 meaningful exchanges (when you have collected enough core information), "
            "   your next response must be exactly:\n"
            "   \"Thank you. I now have a good sense of what would be most helpful for you right now.\n\n"
            
            "Never generate or preview any meditation text. "
            "Never list meditation styles or techniques. "
            "Stay in pure information-gathering mode until the user signals readiness."
        )

        async_chat = self.client.aio.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.65,
                top_p=0.95,
                top_k=40,
            ),
            history=history,
        )

        try:
            response = await async_chat.send_message(current_user_message)
            return (response.text or "").strip()

        except Exception as e:
            logger.error(f"Gemini chat response failed: {e}", exc_info=True)
            return (
                "I'm sorry, I encountered an issue while preparing your meditation "
                "guidance. Could you please try again?"
            )

    # Summarization
    async def summarize_conversation(self, messages: List[Message]) -> str:
        if not messages:
            return "No conversation history available."

        conversation_text = "\n".join(
            f"{msg.role.value.upper()}: {msg.content}"
            for msg in messages
        )

        prompt = (
            "You are an expert at summarizing meditation preparation conversations.\n"
            "Create a concise yet comprehensive summary that captures:\n"
            "- User's meditation goals and intentions\n"
            "- Preferred meditation type/style\n"
            "- Emotional/mental/physical state\n"
            "- Experience level\n"
            "- Any specific requests or themes\n"
            "- Key personal insights shared\n\n"
            "Conversation:\n"
            + conversation_text
            + "\n\nSummary:"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=1000,
                ),
            )

            return (response.text or "").strip()

        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}", exc_info=True)
            raise

    # Meditation script generation
    async def generate_meditation_script(self, summary: str) -> List[str]:
        prompt = (
            "You are an expert meditation script writer.\n\n"
            "Create a complete, flowing meditation script divided into EXACTLY 5 logical blocks.\n"
            "Approximate spoken durations:\n"
            "- Block 1: ~90 seconds\n"
            "- Block 2: ~150 seconds\n"
            "- Block 3: ~90 seconds\n"
            "- Block 4: ~120 seconds\n"
            "- Block 5: ~120 seconds\n\n"
            "Guidelines:\n"
            "- Use calm, soothing, slow-paced language suitable for guided meditation\n"
            "- Include breathing instructions, body awareness, and appropriate visualizations\n"
            "- Match the style and content to the user's preferences from the summary\n"
            "- End Block 5 with a gentle return to present awareness\n\n"
            "User summary:\n" + summary + "\n\n"
            "VERY IMPORTANT OUTPUT RULES:\n"
            "1. Respond with **ONLY** a valid JSON array — nothing else.\n"
            "2. No explanations, no markdown, no code fences (```), no introductory text.\n"
            "3. The array must contain EXACTLY 5 strings.\n"
            "4. Each string is one complete block of narration text.\n"
            "5. Do NOT include block numbers or labels inside the strings.\n"
            "6. Properly escape any double quotes or special characters inside the text.\n\n"
            "Correct output format (example):\n"
            '["First block text here...", "Second block text here...", "Third...", "Fourth...", "Fifth..."]\n\n'
            "Your response must start with [ and end with ] and be parseable by json.loads()"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=4000,
                    response_mime_type="application/json",
                ),
            )

            text = (response.text or "").strip()

            if text.startswith("```json"):
                text = text.split("```json", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end != -1 and end > start:
                text = text[start:end]

            scripts = json.loads(text)

            if not isinstance(scripts, list) or len(scripts) != 5:
                raise ValueError(f"Expected 5 script blocks, got {len(scripts)}")

            return [str(block).strip() for block in scripts]

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed. Raw response was:\n{text}\nError: {e}")
            raise RuntimeError(f"Gemini returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Gemini script generation failed: {e}", exc_info=True)
            raise RuntimeError("Failed to generate meditation script structure")