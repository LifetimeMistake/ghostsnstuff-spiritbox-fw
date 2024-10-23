from agents import BaseAgent
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = BaseAgent(
    client,
    "gpt-4o-mini",
    0.5,
    CalendarEvent,
    "Extract the event information"
)

print(agent.ask("Alice and Bob are going to a movie on Thursday"))