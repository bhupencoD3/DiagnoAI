from typing import List, Dict, Any
import logging

class MedicalPromptTemplate:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def build_mistral_prompt(self, query: str, context: str) -> str:
        system_message = """You are a medical information specialist. Extract and synthesize ALL relevant information from the provided context.

CORE INSTRUCTIONS:
1. Extract ALL medical facts about symptoms, causes, treatments, risk factors
2. Organize with **bold headers** and bullet points
3. Be precise with medical terminology
4. Include ONLY this one-sentence disclaimer at the end: "**Medical Disclaimer:** Consult healthcare professionals for medical advice."
5. STOP immediately after the disclaimer

IMPORTANT: IGNORE source citations like [Source X: ...] - only extract medical content."""

        user_message = f"""MEDICAL CONTEXT:
    {context}

    QUESTION: {query}

    Extract and synthesize the medical information. Use **bold headers** and bullet points. End with the exact disclaimer sentence.

    ANSWER:"""

        return f"""<s>[INST] {system_message}

    {user_message} [/INST]"""