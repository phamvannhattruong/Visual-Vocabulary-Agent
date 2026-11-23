import json
import re
from typing import Any, Dict, List, Optional
from backend.app.services.agents.base import Agent


class TeacherAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def build_offline_lesson(
        self,
        object_detected: List[str] | None,
        scene_context: Optional[Dict[str, Any]] = None,
        user_memory: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Graceful local lesson generator when network or external AI quotas are unavailable.
        Guarantees that learners always receive high quality educational content.
        """
        if not object_detected:
            return "Chào mừng bạn! Hãy tải lên một bức ảnh rõ nét để khám phá từ vựng tiếng Anh nhé."

        offline_db: Dict[str, Dict[str, str]] = {
            "person": {
                "ipa": "/ˈpɜː.sən/",
                "meaning": "Người, một cá nhân",
                "cefr": "A1",
                "example": "A person is traveling along the road. (Một người đang di chuyển dọc theo con đường.)",
                "synonym": "individual",
                "synonym_ipa": "/ˌɪn.dɪˈvɪdʒ.u.əl/",
                "synonym_meaning": "Cá nhân, người riêng biệt",
                "synonym_example": "Every individual has unique strengths. (Mỗi cá nhân đều có thế mạnh riêng.)",
            },
            "motorcycle": {
                "ipa": "/ˈməʊ.təˌsaɪ.kəl/",
                "meaning": "Xe máy, xe mô tô",
                "cefr": "A2",
                "example": "He rides his motorcycle to work every day. (Anh ấy đi xe máy đi làm mỗi ngày.)",
                "synonym": "motorbike",
                "synonym_ipa": "/ˈməʊ.tə.baɪk/",
                "synonym_meaning": "Xe gắn máy",
                "synonym_example": "She parked her motorbike by the curb. (Cô ấy đỗ xe gắn máy ở lề đường.)",
            },
            "car": {
                "ipa": "/kɑːr/",
                "meaning": "Xe ô tô, xe hơi",
                "cefr": "A1",
                "example": "The family travels by car. (Gia đình đi du lịch bằng ô tô.)",
                "synonym": "automobile",
                "synonym_ipa": "/ˈɔː.tə.mə.biːl/",
                "synonym_meaning": "Xe hơi, xe cơ giới",
                "synonym_example": "The automobile industry is advancing. (Ngành công nghiệp ô tô đang phát triển.)",
            },
            "bottle": {
                "ipa": "/ˈbɒt.əl/",
                "meaning": "Cái chai, cái bình đựng nước",
                "cefr": "A1",
                "example": "Please fill the bottle with fresh water. (Làm ơn hãy đổ đầy chai nước sạch.)",
                "synonym": "flask",
                "synonym_ipa": "/flɑːsk/",
                "synonym_meaning": "Bình giữ nhiệt, bình đựng nước nhỏ gọn",
                "synonym_example": "He kept warm tea in his flask. (Anh ấy giữ trà ấm trong bình giữ nhiệt.)",
            },
            "cup": {
                "ipa": "/kʌp/",
                "meaning": "Cái cốc, cái tách",
                "cefr": "A1",
                "example": "She is drinking warm tea from a cup. (Cô ấy đang uống trà ấm từ chiếc cốc.)",
                "synonym": "mug",
                "synonym_ipa": "/mʌɡ/",
                "synonym_meaning": "Cốc vại lớn có quai",
                "synonym_example": "He poured coffee into a large mug. (Anh ấy rót cà phê vào một chiếc cốc vại lớn.)",
            },
            "laptop": {
                "ipa": "/ˈlæp.tɒp/",
                "meaning": "Máy tính xách tay",
                "cefr": "A1",
                "example": "He opened his laptop to start working. (Anh ấy mở máy tính xách tay để làm việc.)",
                "synonym": "notebook",
                "synonym_ipa": "/ˈnəʊt.bʊk/",
                "synonym_meaning": "Máy tính xách tay siêu mỏng",
                "synonym_example": "She carried her notebook to the conference. (Cô ấy mang máy tính xách tay đến hội nghị.)",
            },
        }

        known = [str(k).lower().strip() for k in user_memory.get("known_vocabulary", [])] if user_memory else []
        known_set = set(known)
        clean_objs = [str(o).lower().strip() for o in object_detected]
        new_objs = [o for o in clean_objs if o not in known_set]
        reviewed_objs = [o for o in clean_objs if o in known_set]

        # Build vocabulary sections
        lesson_md = "Chào mừng bạn đến với **Visual Vocabulary Studio**! 🌟\n\n"
        if scene_context and isinstance(scene_context, dict) and scene_context.get("scene"):
            lesson_md += f"Bối cảnh nhận diện: **{scene_context.get('scene')}** ({scene_context.get('scene_vietnamese', '')})\n\n"

        lesson_md += "### 📚 Bài học Từ vựng Thực tế:\n\n"
        target_obj = clean_objs[0]

        for obj in clean_objs[:3]:
            info = offline_db.get(obj, {
                "ipa": f"/{obj}/",
                "meaning": f"Đồ vật: {obj}",
                "cefr": "A1",
                "example": f"This is an everyday {obj}. (Đây là một vật dụng quen thuộc.)",
                "synonym": f"{obj}-related",
                "synonym_ipa": f"/{obj}/",
                "synonym_meaning": f"Từ liên quan đến {obj}",
                "synonym_example": f"This relates to {obj}.",
            })
            lesson_md += f"#### **{obj.capitalize()}** `[{info['cefr']}]`\n"
            lesson_md += f"- **Phiên âm IPA:** `{info['ipa']}`\n"
            lesson_md += f"- **Nghĩa tiếng Việt:** {info['meaning']}\n"
            lesson_md += f"- **Ví dụ câu:** {info['example']}\n\n"

        # Prepositions section
        if len(clean_objs) >= 2:
            lesson_md += f"### 📍 Giới từ Chỉ Vị trí (Spatial Prepositions):\n"
            lesson_md += f"- Trong bức ảnh, **{clean_objs[0]}** đang nằm **near / next to** (gần / bên cạnh) **{clean_objs[1]}**.\n\n"

        # Quiz generation
        target_info = offline_db.get(target_obj, {
            "ipa": f"/{target_obj}/",
            "meaning": f"Đồ vật {target_obj}",
            "synonym": "item",
            "synonym_ipa": "/ˈaɪ.təm/",
            "synonym_meaning": "Món đồ, vật phẩm",
            "synonym_example": "This is an important item. (Đây là một món đồ quan trọng.)",
        })

        if reviewed_objs:
            rev_target = reviewed_objs[0]
            rev_info = offline_db.get(rev_target, target_info)
            quiz_json = {
                "mode": "review_challenge",
                "target_word": rev_target,
                "questions": [
                    {
                        "id": 1,
                        "type": "pronunciation",
                        "question": f"Phiên âm IPA chuẩn của từ '{rev_target}' là gì?",
                        "options": [rev_info["ipa"], f"/{rev_target}ing/", f"/un{rev_target}/"],
                        "answer": rev_info["ipa"],
                        "explanation": f"Từ '{rev_target}' có phiên âm chuẩn là {rev_info['ipa']}."
                    },
                    {
                        "id": 2,
                        "type": "meaning",
                        "question": f"Trong tiếng Việt, từ '{rev_target}' có nghĩa chính xác nhất là gì?",
                        "options": [rev_info["meaning"], "Cái bàn gỗ", "Quyển sách học"],
                        "answer": rev_info["meaning"],
                        "explanation": f"'{rev_target}' có nghĩa tiếng Việt là: {rev_info['meaning']}."
                    },
                    {
                        "id": 3,
                        "type": "synonym",
                        "question": f"Từ nào sau đây gần nghĩa hoặc đồng nghĩa với từ '{rev_target}'?",
                        "options": [rev_info["synonym"], "blanket", "window"],
                        "answer": rev_info["synonym"],
                        "explanation": f"'{rev_info['synonym']}' là từ gần nghĩa phù hợp nhất.",
                        "synonym_lesson": {
                            "word": rev_info["synonym"],
                            "ipa": rev_info["synonym_ipa"],
                            "meaning_vn": rev_info["synonym_meaning"],
                            "example": rev_info["synonym_example"]
                        }
                    }
                ]
            }
        else:
            quiz_json = {
                "mode": "single",
                "target_word": target_obj,
                "questions": [
                    {
                        "id": 1,
                        "type": "comprehension",
                        "question": f"Which sentence correctly describes the word '{target_obj}' in this scene?",
                        "options": [
                            target_info["example"],
                            f"The {target_obj} is flying in the outer space.",
                            f"I eat a {target_obj} for breakfast."
                        ],
                        "answer": target_info["example"],
                        "explanation": f"Câu ví dụ chính xác là: {target_info['example']}"
                    }
                ]
            }

        lesson_md += f"\n[QUIZ_START]\n{json.dumps(quiz_json, ensure_ascii=False, indent=2)}\n[QUIZ_END]"
        return lesson_md
