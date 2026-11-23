from typing import Any, Dict, List, Optional
from backend.app.services.agents.base import Agent


class TeacherAgent(Agent):
    def __init__(self):
        super().__init__()

    def generate_learning_content(
        self,
        object_detected: List[str] | None,
        scene_context: Optional[Dict[str, Any]] = None,
        user_memory: Optional[Dict[str, Any]] = None,
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

        # Build personalized long-term memory block
        memory_block = ""
        if user_memory and isinstance(user_memory, dict) and user_memory.get("total_lessons", 0) > 0:
            known = user_memory.get("known_vocabulary", [])[:15]
            weak = user_memory.get("weak_pronunciation_words", [])[:8]
            mastered = user_memory.get("mastered_words", [])[:8]
            level = user_memory.get("learner_level", "A1")
            total_l = user_memory.get("total_lessons", 0)

            memory_block = f"""
Learner Long-Term Memory Profile (Personalized Learning History):
- Estimated CEFR Level: {level}
- Previous Visual Lessons Completed: {total_l}
- Already Known Vocabulary (Encountered in past lessons): {', '.join(known) if known else 'None'}
- Words Needing Reinforcement (Past low pronunciation scores < 75): {', '.join(weak) if weak else 'None'}
- Mastered Vocabulary: {', '.join(mastered) if mastered else 'None'}

Pedagogical Memory Directives:
1. NOVELTY PREFERENCE: If the detected objects contain words not yet in 'Already Known Vocabulary', prioritize selecting those new words to expand the learner's vocabulary!
2. REINFORCE WEAK WORDS: If any detected object matches a word in 'Words Needing Reinforcement', prioritize selecting it and give an encouraging pronunciation tip!
3. ADAPTIVE CHALLENGE: Adapt example sentences and quiz difficulty to the learner's estimated level ({level}).
"""

        prompts = f"""
You are an intelligent, personalized, and friendly 'Visual Vocabulary Agent'. 
Your mission is to help users learn English through the objects they capture in their photos, taking into account their individual learning journey and memory history.

Input list of detected objects: {object_detected}
{context_block}
{memory_block}

Please follow these steps:
1. Greet the user with high energy and enthusiasm. If a scene context is provided, warmly acknowledge it. If the learner has past memory, warmly welcome them back (e.g. "Welcome back to your visual learning journey!").
2. Select up to 3 most educational objects from the provided list, adhering to the Pedagogical Memory Directives (prioritizing new words or reinforcing weak words).
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
