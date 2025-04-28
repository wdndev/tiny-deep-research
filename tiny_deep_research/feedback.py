from typing import List
import json

from .prompt import get_system_prompt
from .llm.llm_services import LLMService

async def generate_feedback(
    query: str,
    llm_client: LLMService,
    system_prompt: str = get_system_prompt(),
) -> List[str]:
    """
    Generate feedback using the LLM service.

    :param feedback: The feedback to be processed.
    :param llm: The LLM service instance.
    :param system_prompt: The system prompt for the LLM.
    :return: A list of generated feedback responses.
    """
    feedback_content = f"Given this research topic: {query}, generate 3-5 follow-up questions to better understand the user's research needs. Return the response as a JSON object with a 'questions' array field."
    # feedback_content = 
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": feedback_content},
    ]

    llm_response = await llm_client.get_response(
        messages, 
        response_format = {"type": "json_object"},
        stream=False
    )

    # 解析json
    try:
        response_json = json.loads(llm_response)
        return response_json.get("questions", [])
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {llm_response}")
        return []