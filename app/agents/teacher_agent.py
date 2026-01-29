import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from app.agents.base_agent import Agent

load_dotenv()

class TeacherAgent(Agent):
    def __init__(self):
        super().__init__()

    def generate_learning_content(self, object_detected):
        if object_detected is None:
            return (
                "Oh, I haven't identified any objects in this photo yet. Tip: Try shooting closer, well-lit, and realistic!"
            )

        prompts = """
        You are an intelligent and friendly 'Visual Vocabulary Agent'. 
    
        Your mission is to help users learn English through the objects they capture in their photos.
        
        Input list of detected objects: {objects}
            
        Please follow these steps:
            1. Greet the user with high energy and enthusiasm.
            2. Select up to 3 most interesting objects from the provided list.
            3. For each selected object, provide:
               -  Vocabulary (English)
               -  IPA Phonetic Transcription
               -  Vietnamese Meaning
               -  A brief, practical bilingual (English-Vietnamese) example sentence.
            4. Conclude with a fun, short Quiz related to one of the objects mentioned.
            
        Finally, create a short Multiple Choice Quiz related to one of the objects above.
        The quiz MUST be formatted in JSON at the very end of your response, wrapped between [QUIZ_START] and [QUIZ_END] tags.
        Example of the JSON structure:
        [QUIZ_START]
        {{
          "question": "Which object is used for cutting paper?",
          "options": ["Scissors", "Pen", "Book"],
          "answer": "Scissors"
        }}
        [QUIZ_END]
        
        Style Guidelines:
            - Use a friendly, encouraging, and educational tone.
            - Format the output beautifully using Markdown (bold text, emojis, lists).
            - Ensure the content is easy to read for an English learner.
            """

        prompts = PromptTemplate(
            input_variables=["object"],
            template=prompts,
        )

        chain = prompts | self.gemini

        object_str = ", ".join(object_detected)
        response = chain.invoke({"objects": object_str})

        return response.content


if __name__ == "__main__":
    # Giả lập kết quả từ vision_agent.py
    sample_objects = ['scissors', 'pen', 'book']

    try:
        brain = Agent()
        result = brain.generate_learning_content(sample_objects)
        print(result)
    except Exception as e:
        print(f"Lỗi: {e}")