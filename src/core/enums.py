from enum import Enum, auto

class Faction(Enum):
    # Law Enforcement Factions
    FBI = "Federal Bureau of Investigation"
    CIA = "Central Intelligence Agency"
    LOCAL_PD = "Local Police Department"
    
    # Hostage Taker Factions
    SHADOW_SYNDICATE = "Shadow Syndicate"  # Tech-savvy international crime organization
    RED_DRAGON_TRIAD = "Red Dragon Triad"  # Traditional organized crime group
    LIBERATION_FRONT = "Liberation Front"   # Political extremist organization

class ActionCategory(Enum):
    DIALOGUE = "Dialogue"
    RESOURCES = "Resources"
    FORCE = "Force"
    TECH = "Tech"
    NEGOTIATION = "Negotiation"
    THREATS = "Threats"

class UIState(Enum):
    SIDE_SELECT = auto()
    FACTION_SELECT = auto()
    MAIN_GAME = auto()
    ACTION_MENU = auto()
    EXIT_CONFIRM = auto()
    AI_TURN = auto()  # New state for AI turn
    HISTORY_LOG = auto()  # New state for viewing game history

class DialogueType(Enum):
    DEMAND = "demand"
    THREAT = "threat"
    EMPATHY = "empathy"
    REASON = "reason"
    DECEPTION = "deception"
    INFORMATION = "information"
    NEGOTIATION = "negotiation"
    CONCESSION = "concession"

class ActionEffect(Enum):
    STRESS_INCREASE = "stress_increase"
    STRESS_DECREASE = "stress_decrease"
    TRUST_INCREASE = "trust_increase"
    TRUST_DECREASE = "trust_decrease"
    MORALE_INCREASE = "morale_increase"
    MORALE_DECREASE = "morale_decrease"
    TENSION_INCREASE = "tension_increase"
    TENSION_DECREASE = "tension_decrease"
    HOSTAGE_RELEASE = "hostage_release"
    DEMAND_ACCEPTED = "demand_accepted"
    INTEL_GAINED = "intel_gained"
    THREAT_ESCALATION = "threat_escalation"
    RESOURCE_GAIN = "resource_gain"
    RESOURCE_LOSS = "resource_loss"
    TACTICAL_ADVANTAGE = "tactical_advantage"
    TACTICAL_DISADVANTAGE = "tactical_disadvantage"
    EXTRA_ACTION_POINTS = "extra_action_points"
    DISABLE_COMMUNICATIONS = "disable_communications"
    MASS_PANIC = "mass_panic"
    INSIDER_INTEL = "insider_intel"
    MEDIA_MANIPULATION = "media_manipulation"
    CYBER_ADVANTAGE = "cyber_advantage" 