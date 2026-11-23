import json
import re
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
        known: List[str] = []
        weak: List[str] = []
        mastered: List[str] = []
        level = "A1"
        total_l = 0

        if user_memory and isinstance(user_memory, dict) and user_memory.get("total_lessons", 0) > 0:
            known = user_memory.get("known_vocabulary", [])
            weak = user_memory.get("weak_pronunciation_words", [])
            mastered = user_memory.get("mastered_words", [])
            level = user_memory.get("learner_level", "A1")
            total_l = user_memory.get("total_lessons", 0)

            memory_block = f"""
Learner Long-Term Memory Profile (Personalized Learning History):
- Estimated CEFR Level: {level}
- Previous Visual Lessons Completed: {total_l}
- Already Known Vocabulary (Encountered in past lessons): {', '.join(known[:15]) if known else 'None'}
- Words Needing Reinforcement (Past low pronunciation scores < 75): {', '.join(weak[:8]) if weak else 'None'}
- Mastered Vocabulary: {', '.join(mastered[:8]) if mastered else 'None'}

Pedagogical Memory Directives:
1. NOVELTY PREFERENCE: If the detected objects contain words not yet in 'Already Known Vocabulary', prioritize selecting those new words to expand the learner's vocabulary!
2. REINFORCE WEAK WORDS: If any detected object matches a word in 'Words Needing Reinforcement', prioritize selecting it and give an encouraging pronunciation tip!
3. ADAPTIVE CHALLENGE: Adapt example sentences and quiz difficulty to the learner's estimated level ({level}).
"""

        # Categorize detected objects into New vs Reviewed
        known_lower_set = {str(k).lower().strip() for k in known}
        detected_clean = [str(o).lower().strip() for o in object_detected] if object_detected else []
        new_objects = [o for o in detected_clean if o not in known_lower_set]
        reviewed_objects = [o for o in detected_clean if o in known_lower_set]

        target_review_word = None
        if reviewed_objects:
            weak_lower_set = {str(w).lower().strip() for w in weak}
            for obj in reviewed_objects:
                if obj in weak_lower_set:
                    target_review_word = obj
                    break
            if not target_review_word:
                target_review_word = reviewed_objects[0]

        breakdown_block = f"""
Detected Objects Breakdown by Learner Status:
- New / Unencountered Vocabulary: {', '.join(new_objects) if new_objects else 'None (All detected objects were previously encountered)'}
- Already Learned Vocabulary (To Review): {', '.join(reviewed_objects) if reviewed_objects else 'None (All detected objects are new)'}
"""

        prompts = f"""
You are an intelligent, personalized, and friendly 'Visual Vocabulary Agent'. 
Your mission is to help users learn English through the objects they capture in their photos, taking into account their individual learning journey and memory history.

Input list of detected objects: {object_detected}
{context_block}
{memory_block}
{breakdown_block}

PEDAGOGICAL TEACHING INSTRUCTIONS:
1. Greet the user warmly with high energy and enthusiasm. Acknowledge the physical scene context if provided. If the learner has past memory, warmly welcome them back to their visual learning studio.
2. Content Generation by Word Category:
   A. **FOR NEW / UNENCOUNTERED WORDS** (e.g. {', '.join(new_objects) if new_objects else 'None'}):
      - If there are new words, provide a clear, structured visual lesson for up to 2-3 new words:
        * Vocabulary word (English) + Estimated CEFR level (e.g. [A1], [A2], [B1])
        * IPA Phonetic Transcription (e.g. /ˈbɒt.əl/)
        * Vietnamese Meaning (Nghĩa tiếng Việt rõ ràng)
        * Natural bilingual example sentence (English - Vietnamese).
   B. **FOR ALREADY LEARNED WORDS** (e.g. {', '.join(reviewed_objects) if reviewed_objects else 'None'}):
      - If reviewed words are detected (or if all detected words are already learned):
        * Warmly acknowledge that the user has previously learned them.
        * Provide an inspiring refresher note and introduce a 3-Question Deep Review Challenge (Thử thách ôn tập 3 câu hỏi) for '{target_review_word or (reviewed_objects[0] if reviewed_objects else (detected_clean[0] if detected_clean else "the object"))}'.
3. **Spatial Prepositions Section:**
   - Teach 1 or 2 prepositions of place (such as: *on, in, next to, under, beside, between*) by explaining where objects are situated relative to each other based on scene context.
4. **QUIZ GENERATION (MANDATORY at the very end of your response, wrapped between [QUIZ_START] and [QUIZ_END]):**
   - **CASE 1: If there are Already Learned Words (or all detected words are already learned):**
     You MUST generate a 3-Question Multiple Choice Review Challenge for the target reviewed word ('{target_review_word or (reviewed_objects[0] if reviewed_objects else (detected_clean[0] if detected_clean else "object"))}'):
     * **Question 1 (type: "pronunciation"):** Test the correct IPA transcription, pronunciation, or syllable stress of the target word.
     * **Question 2 (type: "meaning"):** Test the exact Vietnamese definition or correct usage in context.
     * **Question 3 (type: "synonym"):** Test a synonym or closely related English word for this target word.
       **CRITICAL REQUIREMENT FOR QUESTION 3:**
       You MUST include a "synonym_lesson" object inside Question 3 providing:
       - "word": The synonym word in English
       - "ipa": IPA phonetic transcription of the synonym
       - "meaning_vn": Vietnamese translation of the synonym
       - "example": Natural bilingual example sentence (English and Vietnamese) using the synonym.

     Example format for Case 1:
     [QUIZ_START]
     {{
       "mode": "review_challenge",
       "target_word": "bottle",
       "questions": [
         {{
           "id": 1,
           "type": "pronunciation",
           "question": "Phiên âm IPA chuẩn của từ 'bottle' là gì?",
           "options": ["/ˈbɒtl/", "/ˈbʌtl/", "/ˈbɔːtl/"],
           "answer": "/ˈbɒtl/",
           "explanation": "Từ 'bottle' phát âm là /ˈbɒtl/."
         }},
         {{
           "id": 2,
           "type": "meaning",
           "question": "Trong tiếng Việt, từ 'bottle' có nghĩa chính xác nhất là gì?",
           "options": ["Cái chai, cái bình", "Cái thìa, cái dĩa", "Cái cốc thủy tinh"],
           "answer": "Cái chai, cái bình",
           "explanation": "'Bottle' chỉ cái chai, lọ đựng chất lỏng."
         }},
         {{
           "id": 3,
           "type": "synonym",
           "question": "Từ nào sau đây gần nghĩa hoặc đồng nghĩa với từ 'bottle'?",
           "options": ["flask", "towel", "fork"],
           "answer": "flask",
           "explanation": "'flask' (bình giữ nhiệt / bình nước nhỏ) là từ gần nghĩa với 'bottle'.",
           "synonym_lesson": {{
             "word": "flask",
             "ipa": "/flɑːsk/",
             "meaning_vn": "Bình giữ nhiệt, bình đựng nước du lịch nhỏ gọn",
             "example": "He filled his flask with cold water. (Anh ấy đã đổ đầy nước mát vào bình du lịch.)"
           }}
         }}
       ]
     }}
     [QUIZ_END]

   - **CASE 2: If ALL detected words are NEW (no words have been learned before):**
     Generate a fun review question about one of the newly taught words or prepositions:
     [QUIZ_START]
     {{
       "mode": "single",
       "questions": [
         {{
           "id": 1,
           "type": "comprehension",
           "question": "Which sentence correctly uses the word '{new_objects[0] if new_objects else "object"}'?",
           "options": ["Option A", "Option B", "Option C"],
           "answer": "Option A",
           "explanation": "Explanation here."
         }}
       ]
     }}
     [QUIZ_END]

Style Guidelines:
- Use a friendly, encouraging, and educational tone.
- Format the output beautifully using Markdown (bold text, bullet points).
- Ensure the content is easy to read for an English learner.
"""
        return self.generate_response(prompts)

    def generate_synonym_lesson(self, synonym_word: str) -> Dict[str, Any]:
        """Dynamically generate a mini-lesson for a synonym word as fallback."""
        prompt = f"""
Provide a mini-lesson in JSON format for the English vocabulary word '{synonym_word}'.
The response MUST be valid JSON with keys:
- "word": "{synonym_word}"
- "ipa": IPA phonetic transcription
- "meaning_vn": Vietnamese translation
- "example": Natural bilingual example sentence (English and Vietnamese)

Example:
{{
  "word": "flask",
  "ipa": "/flɑːsk/",
  "meaning_vn": "Bình giữ nhiệt, bình đựng nước du lịch",
  "example": "He carried a flask of hot tea. (Anh ấy mang theo một bình trà nóng.)"
}}
"""
        try:
            raw = self.generate_response(prompt)
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {
            "word": synonym_word,
            "ipa": "",
            "meaning_vn": "Từ đồng nghĩa tiếng Anh",
            "example": f"This is an example sentence using {synonym_word}.",
        }
