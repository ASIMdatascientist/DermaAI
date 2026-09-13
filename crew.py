import os

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
import litellm


# =========================================
# LOAD ENVIRONMENT VARIABLES
# =========================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================================
# GEMINI LLM
# =========================================

gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=GEMINI_API_KEY
)


# =========================================
# SKIN DISEASE INFORMATION AGENT
# =========================================

skin_agent = Agent(
    role="Skin Disease Information Specialist",

    goal=(
        "Provide clear, simple and educational information "
        "about Acne, Eczema and Vitiligo."
    ),

    backstory=(
        "You are an AI health information assistant specialized "
        "in explaining common skin conditions. "
        "You provide general educational information and do not "
        "replace a qualified medical professional."
    ),

    llm=gemini_llm,

    verbose=True
)


# =========================================
# FUNCTION (now async — safe to call from
# FastAPI's running event loop)
# =========================================

async def get_skin_explanation(disease, confidence):

    task = Task(
        description=f"""
        A skin disease classification model has predicted:

        Disease: {disease}
        Confidence: {confidence:.2f}%

        The available classes are:
        - Acne
        - Eczema
        - Vitiligo

        Provide a simple and easy-to-understand explanation.

        Include:

        1. What is {disease}?
        2. Common symptoms
        3. General skin-care information
        4. When a person should consider consulting a doctor

        Important rules:

        - This is educational information only.
        - Do not claim that the AI prediction is a confirmed diagnosis.
        - Do not prescribe medicines.
        - Do not recommend specific drug doses.
        - Keep the response clear and concise.
        """,

        expected_output="""
        A clear response containing:

        - Disease explanation
        - Common symptoms
        - General care information
        - When to consult a healthcare professional
        - A short medical disclaimer
        """,

        agent=skin_agent
    )


    # =========================================
    # CREATE CREW
    # =========================================

    crew = Crew(
        agents=[skin_agent],
        tasks=[task],
        verbose=True
    )


    # =========================================
    # RUN CREW ASYNCHRONOUSLY
    # (safe inside FastAPI's running event loop)
    # =========================================

    result = await crew.kickoff_async()

    return str(result)


# =========================================
# CHATBOT FOLLOW-UP FUNCTION
# (used by /chat — talks directly to Gemini
# via litellm, keeping conversation history,
# instead of spinning up a full Crew/Task
# for every single message)
# =========================================

async def chat_with_gemini(disease, confidence, history, user_message):

    system_prompt = f"""
    You are a friendly AI health information assistant helping a
    patient understand their AI-predicted skin condition.

    The classification model predicted:
    Disease: {disease}
    Confidence: {confidence:.2f}%

    The available classes the model can predict are:
    - Acne
    - Eczema
    - Vitiligo

    Rules you must always follow:
    - This is educational information only, never a confirmed diagnosis.
    - Never prescribe medicines or give specific drug doses.
    - If the user describes worsening, severe, or unusual symptoms,
      recommend they see a qualified healthcare professional promptly.
    - Keep answers clear, simple and reasonably concise.
    - If the question is unrelated to skin health, gently steer the
      conversation back to the topic.
    """

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # -----------------------------
    # Add prior conversation turns
    # (history items look like:
    #  {"role": "user"|"assistant", "content": "..."})
    # -----------------------------

    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    response = await litellm.acompletion(
        model="gemini/gemini-3.6-flash",
        api_key=GEMINI_API_KEY,
        messages=messages
    )

    return response.choices[0].message.content