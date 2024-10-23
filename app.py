from openai import OpenAI
from dotenv import load_dotenv
from ghostsnstuff_spiritbox_fw.agents import Writer

load_dotenv()

client = OpenAI()

writer = Writer(client, "gpt-4o-mini", 0.5)
response = writer.generate(
    "A group of ghost hunters is currently in an attic. The goal of the scenario is to restore the lost spirit's memories and allow it to escape before the evil spirit consumes it.",
    "Lost spirit and evil secondary spirit",
    None
)

print(f"Producer notes: {response.reasoning}")
scenario = response.scenario
print(scenario.model_dump_json(indent=2))