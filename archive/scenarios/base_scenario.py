from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class LocationType(Enum):
    BANK = "bank"
    AIRPORT = "airport"
    HOSPITAL = "hospital"
    SUBURBAN_HOME = "suburban_home"
    TRAIN_STATION = "train_station"
    FARM = "farm"

class EnvironmentFeature(Enum):
    SECURITY_CAMERAS = "security_cameras"
    MULTIPLE_EXITS = "multiple_exits"
    CIVILIANS_NEARBY = "civilians_nearby"
    COVER_SPOTS = "cover_spots"
    VANTAGE_POINTS = "vantage_points"
    COMMUNICATION_SYSTEMS = "communication_systems"

@dataclass
class LocationProperties:
    type: LocationType
    size: str  # small, medium, large
    features: List[EnvironmentFeature]
    civilian_density: int  # 1-10 scale
    security_level: int   # 1-10 scale
    response_time: int    # minutes for backup to arrive

class Scenario:
    def __init__(self, name: str, location: LocationProperties):
        self.name = name
        self.location = location
        self.objectives: Dict[str, List[dict]] = {
            "negotiator": [],
            "hostage_taker": []
        }
        self.available_resources: Dict[str, List[str]] = {
            "negotiator": [],
            "hostage_taker": []
        }
        self.special_conditions: List[dict] = []
    
    def add_objective(self, role: str, objective: dict):
        """Add an objective for a specific role."""
        self.objectives[role].append(objective)
    
    def add_resource(self, role: str, resource: str):
        """Add an available resource for a specific role."""
        self.available_resources[role].append(resource)
    
    def add_special_condition(self, condition: dict):
        """Add a special condition that affects the scenario."""
        self.special_conditions.append(condition)
    
    def get_initial_state(self) -> dict:
        """Get the initial state configuration for this scenario."""
        return {
            "location": {
                "type": self.location.type.value,
                "size": self.location.size,
                "features": [f.value for f in self.location.features],
                "civilian_density": self.location.civilian_density,
                "security_level": self.location.security_level,
                "response_time": self.location.response_time
            },
            "objectives": self.objectives,
            "available_resources": self.available_resources,
            "special_conditions": self.special_conditions,
            "players": {
                "negotiator": {
                    "affiliation": "fbi",
                    "initial_resources": {
                        "swat_team": 1,
                        "surveillance": 2,
                        "negotiation_time": 60
                    }
                },
                "hostage_taker": {
                    "affiliation": "organization_alpha",
                    "initial_resources": {
                        "hostages": 5,
                        "weapons": 3,
                        "escape_routes": 2
                    }
                }
            },
            "hostages": [
                {
                    "id": 1,
                    "type": "civilian",
                    "status": "captured",
                    "health": 100,
                    "stress": 50
                },
                {
                    "id": 2,
                    "type": "bank_employee",
                    "status": "captured",
                    "health": 100,
                    "stress": 70
                },
                {
                    "id": 3,
                    "type": "security_guard",
                    "status": "captured",
                    "health": 90,
                    "stress": 40
                },
                {
                    "id": 4,
                    "type": "civilian",
                    "status": "captured",
                    "health": 100,
                    "stress": 60
                },
                {
                    "id": 5,
                    "type": "bank_manager",
                    "status": "captured",
                    "health": 100,
                    "stress": 80
                }
            ],
            "environment": {
                "time_of_day": "morning",
                "weather": "clear",
                "police_presence": 5,
                "media_attention": 7,
                "civilian_crowd": 8
            }
        }

def create_bank_scenario() -> Scenario:
    """Create a sample bank scenario."""
    location = LocationProperties(
        type=LocationType.BANK,
        size="medium",
        features=[
            EnvironmentFeature.SECURITY_CAMERAS,
            EnvironmentFeature.MULTIPLE_EXITS,
            EnvironmentFeature.CIVILIANS_NEARBY,
            EnvironmentFeature.COVER_SPOTS
        ],
        civilian_density=7,
        security_level=8,
        response_time=5
    )
    
    scenario = Scenario("The Last Withdrawal", location)
    
    # Add negotiator objectives
    scenario.add_objective("negotiator", {
        "type": "primary",
        "description": "Ensure all hostages are released safely",
        "success_conditions": ["all_hostages_safe"],
        "reward": 100
    })
    
    # Add hostage taker objectives
    scenario.add_objective("hostage_taker", {
        "type": "primary",
        "description": "Secure escape with minimum $500,000",
        "success_conditions": ["money_secured", "successful_escape"],
        "reward": 100
    })
    
    # Add available resources
    scenario.add_resource("negotiator", "SWAT team")
    scenario.add_resource("negotiator", "Surveillance equipment")
    scenario.add_resource("hostage_taker", "Weapons")
    scenario.add_resource("hostage_taker", "Inside knowledge of vault")
    
    return scenario 