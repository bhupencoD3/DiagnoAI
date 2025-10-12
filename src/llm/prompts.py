from typing import List, Dict, Any
import logging

class MedicalPromptTemplate:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def build_mistral_prompt(self, query: str, context: str) -> str:
        system_message = """You are a medical assistant. You MUST answer using ONLY the provided context.

ABSOLUTE RULES:
1. ONLY use information from the provided context - DO NOT use general medical knowledge
2. If context says "LIMITED RELEVANT CONTEXT", respond that information is not available
3. Structure answer clearly but be concise
4. Be transparent about information limitations
5. Always include medical disclaimer

PROFESSIONAL CONDUCT:
- Use professional, clinical language
- NO conversational tone, motivational phrases, or informal language
- Present information factually and objectively

FORMATTING:
- Use **bold headers** for sections
- Use bullet points for lists
- Keep responses under 1500 characters"""

        user_message = f"""MEDICAL CONTEXT FROM DATABASE:
{context}

USER QUESTION: {query}

Based ONLY on the context above, provide a structured, professional medical response.

If the context doesn't contain complete information, explicitly state what's missing.

IMPORTANT: 
- DO NOT use any medical knowledge outside of the provided context
- Maintain professional clinical tone throughout
- No conversational elements or friendly language"""

        return f"""<s>[INST] {system_message}

{user_message} [/INST]"""