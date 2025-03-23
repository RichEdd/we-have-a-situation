from enum import Enum, auto

class Faction(Enum):
    # Law Enforcement Factions
    FBI = "FBI - Tactical Response Unit"  # More tactical abilities, jurisdiction, special agents
    CIA = "CIA - Intelligence Division"   # High-tech capabilities, intelligence gathering
    LOCAL_PD = "Local Police Department"  # Better terrain knowledge, local resources
    
    # Hostage Taker Factions
    CHILDREN_OF_THE_VEIL = "Children of the Veil"  # Religious cult with local influence
    ZERO_SIGNAL = "Zero Signal"  # Dark web hacker collective
    ECLIPSE_ORDER = "Eclipse Order"  # Well-funded terrorist organization

class ActionCategory(Enum):
    NEGOTIATE = "Negotiate"
    TACTICAL = "Tactical"
    FORCE = "Force"
    SPECIAL = "Special"

class UIState(Enum):
    SIDE_SELECT = auto()
    FACTION_SELECT = auto()
    MAIN_GAME = auto()
    ACTION_MENU = auto()
    EXIT_CONFIRM = auto()

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
    TRUST_INCREASE = "trust_increase"
    TRUST_DECREASE = "trust_decrease"
    TENSION_INCREASE = "tension_increase"
    TENSION_DECREASE = "tension_decrease"
    HOSTAGE_RELEASE = "hostage_release"
    TACTICAL_ADVANTAGE = "tactical_advantage"
    INTEL_GAINED = "intel_gained"
    RESOURCE_GAIN = "resource_gain"
    RESOURCE_LOSS = "resource_loss"
    MORALE_INCREASE = "morale_increase"
    MORALE_DECREASE = "morale_decrease"
    PHYSICAL_DAMAGE = "physical_damage"
    FIRE_DAMAGE = "fire_damage"
    FLOOD_DAMAGE = "flood_damage"
    POWER_OUTAGE = "power_outage"
    GAS_LEAK = "gas_leak"
    ROOF_DAMAGE = "roof_damage"
    FINANCIAL_LOSS = "financial_loss"
    PUBLIC_PANIC = "public_panic"
    CASUALTIES = "casualties" 