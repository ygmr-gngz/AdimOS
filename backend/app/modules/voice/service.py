from app.modules.voice.stt import transcribe
from app.modules.voice.tts import synthesize
from app.modules.voice.intent_router import route_intent
from app.modules.agents.knowledge_agent import KnowledgeAgent
from app.modules.agents.crm_agent import CRMAgent
from app.modules.agents.ceo_agent import CEOAgent
from app.modules.agents.learning_agent import LearningAgent

_agents = {
    "knowledge": KnowledgeAgent(),
    "crm": CRMAgent(),
    "ceo": CEOAgent(),
    "learning": LearningAgent(),
}


def process_voice(audio_bytes: bytes) -> dict:
    transcript = transcribe(audio_bytes)
    agent_type = route_intent(transcript)
    agent = _agents.get(agent_type, _agents["knowledge"])

    if agent_type in ("knowledge", "learning"):
        result = agent.ask(transcript) if hasattr(agent, "ask") else {"answer": agent.chat(transcript), "sources": []}
        answer_text = result["answer"]
        sources = result.get("sources", [])
    elif agent_type == "ceo":
        answer_text = agent.ask(transcript)
        sources = []
    else:
        answer_text = agent.chat(transcript)
        sources = []

    return {
        "transcript": transcript,
        "answer_text": answer_text,
        "answer_audio_base64": synthesize(answer_text),
        "agent_used": agent_type,
        "sources": sources,
    }
