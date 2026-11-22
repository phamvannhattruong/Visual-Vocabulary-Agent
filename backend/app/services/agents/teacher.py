from typing import Any, Dict, List, Optional
from backend.app.services.agents.base import Agent


class TeacherAgent(Agent):
    def __init__(self):
        super().__init__()

    def generate_learning_content(
        self,
        object_detected: List[str] | None,
        scene_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not object_detected:
            return (
                "Oh, I haven't identified any objects in this photo yet. Tip: Try shooting closer, well-lit, and realistic!"
            )

        # Build context description block
        scene_info = ""
        spatial_info = ""
        if scene_context and isinstance(scene_context, dict):
            scene_name = scene_context.get("scene", "General Environment")
            scene_vn = scene_context.get("scene_vietnamese", "")
            scene_desc = scene_context.get("description", "")
            scene_info = f"- Detected Scene: {scene_name} ({scene_vn}) - {scene_desc}"

            relations = scene_context.get("spatial_relationships", [])
            if relations:
                formatted_relations = "\n".join(f"  * {rel}" for rel in relations)
                spatial_info = f"- Spatial Relationships:\n{formatted_relations}"

        context_block = ""
        if scene_info or spatial_info:
            context_block = f"""
Additional Scene & Spatial Context:
{scene_info}
{spatial_info}
"""

        prompts = f"""
You are an intelligent and friendly 'Visual Vocabulary Agent'. 
Your mission is to help users learn English through the objects they capture in their photos.

Input list of detected objects: {object_detected}
{context_block}

Please follow these steps:
1. Greet the user with high energy and enthusiasm. If a scene context is provided, warmly acknowledge it (e.g. "Welcome to your study corner!", "Looks like you're in the kitchen!").
2. Select up to 3 most interesting or practical objects from the provided list.
3. For each selected object, provide:
   - Vocabulary (English)
   - Estimated CEFR Level (e.g. [A1], [A2], [B1])
   - IPA Phonetic Transcription
   - Vietnamese Meaning
   - A brief, practical bilingual (English-Vietnamese) example sentence.
4. **Spatial Prepositions Section:**
   - Teach 1 or 2 prepositions of place (such as: *on, in, next to, under, beside, between*) by explaining where the objects are situated relative to each other based on the scene context.
5. Conclude with a fun, short Multiple Choice Quiz related to one of the objects or spatial prepositions.

The quiz MUST be formatted in JSON at the very end of your response, wrapped between [QUIZ_START] and [QUIZ_END] tags.
Example of the JSON structure:
[QUIZ_START]
{{
  "question": "Which preposition describes an object positioned right beside another?",
  "options": ["Next to", "Inside", "Under"],
  "answer": "Next to"
}}
[QUIZ_END]

Style Guidelines:
- Use a friendly, encouraging, and educational tone.
- Format the output beautifully using Markdown (bold text, emojis, bullet points).
- Ensure the content is easy to read for an English learner.
"""
        return self.generate_response(prompts)
