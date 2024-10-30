from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from threading import Thread
from ..server import Server
from ..scenario import ScenarioDefinition, load_scenario
import uvicorn

class GenerateScenarioRequest(BaseModel):
    base_scenario: str
    prompt: str

class SystemCallRequest(BaseModel):
    command: str

class SystemCallResponse(BaseModel):
    curator_response: str

class StartScenarioRequest(BaseModel):
    base_scenario_name: Optional[str] = None
    custom_scenario: Optional[ScenarioDefinition] = None

class DebugAPI:
    def __init__(self, server: 'Server', host="127.0.0.1", port=8000):
        self.server = server
        self.host = host
        self.port = port
        self.app = FastAPI()

        # Route Definitions
        self.app.get("/scenario/current")(self.get_current_scenario)
        self.app.get("/scenario/base_scenarios")(self.get_base_scenarios)
        self.app.post("/scenario/generate")(self.generate_scenario)
        self.app.post("/scenario/start")(self.start_scenario)
        self.app.post("/scenario/stop")(self.stop_scenario)
        self.app.post("/system/call")(self.execute_system_call)
        self.app.get("/events")(self.get_events)

    def run(self):
        """Runs FastAPI in a background thread."""
        thread = Thread(target=self._run_server)
        thread.daemon = True
        thread.start()

    def _run_server(self):
        """Launch the Uvicorn server to serve the FastAPI app."""
        uvicorn.run(self.app, host=self.host, port=self.port)

    # Endpoints
    def get_current_scenario(self) -> Dict[str, Any]:
        scenario = self.server.get_current_scenario()
        if scenario:
            return scenario.model_dump()
        else:
            raise HTTPException(status_code=404, detail="No current scenario found")

    def get_base_scenarios(self) -> List[str]:
        base_scenarios = self.server.get_base_scenarios()
        return [str(path.stem) for path in base_scenarios]

    def generate_scenario(self, request: GenerateScenarioRequest) -> Dict[str, Any]:
        base_scenario_paths = {path.stem: path for path in self.server.get_base_scenarios()}
        base_scenario_path = base_scenario_paths.get(request.base_scenario)

        if not base_scenario_path:
            raise HTTPException(status_code=400, detail="Invalid base scenario name")

        new_scenario = self.server.write_scenario(base_scenario_path, request.prompt)
        if new_scenario:
            return new_scenario.model_dump()
        else:
            raise HTTPException(status_code=500, detail="Failed to generate scenario")
        
    def start_scenario(self, request: StartScenarioRequest):
        if request.base_scenario_name:
            base_scenario_paths = {path.stem: path for path in self.server.get_base_scenarios()}
            base_scenario_path = base_scenario_paths.get(request.base_scenario_name)

            if not base_scenario_path:
                raise HTTPException(status_code=400, detail="Invalid base scenario name")
            
            scenario = load_scenario(str(base_scenario_path.resolve()))
            if scenario and self.server.start_scenario(scenario):
                return {"status": "started"}
            else:
                raise HTTPException(status_code=500, detail="Failed to start scenario from base")

        elif request.custom_scenario:
            scenario = request.custom_scenario
            if self.server.start_scenario(scenario):
                return {"status": "started"}
            else:
                raise HTTPException(status_code=500, detail="Failed to start custom scenario")

        else:
            raise HTTPException(status_code=400, detail="Either base_scenario_name or custom_scenario must be provided")

    def stop_scenario(self):
        self.server.stop_scenario()
        return {"status": "stopped"}

    def execute_system_call(self, request: SystemCallRequest) -> SystemCallResponse:
        result = self.server.execute_command(request.command)
        if result:
            return SystemCallResponse(curator_response=result.curator_response)
        else:
            raise HTTPException(status_code=500, detail="Command execution failed")

    def get_events(self) -> List[Dict[str, Any]]:
        timeline = self.server.get_timeline()
        if timeline:
            return [event.to_dict() for event in timeline.list()]
        else:
            raise HTTPException(status_code=404, detail="No events found")
