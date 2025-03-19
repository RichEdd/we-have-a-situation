from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

class DialogueType(Enum):
    DEMAND = "demand"
    THREAT = "threat"
    EMPATHY = "empathy"
    REASON = "reason"
    DECEPTION = "deception"
    INFORMATION = "information"
    NEGOTIATION = "negotiation"
    CONCESSION = "concession"

class DialogueEffect(Enum):
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

@dataclass
class DialogueOption:
    text: str
    type: DialogueType
    effects: List[DialogueEffect]
    requirements: Dict[str, any]
    success_chance: float

class DialogueSystem:
    def __init__(self):
        self.dialogue_history: List[dict] = []
        self.trust_level: float = 0.5  # 0.0 to 1.0
        self.tension_level: float = 0.5  # 0.0 to 1.0
        self.intel_level: float = 0.0  # 0.0 to 1.0
        self.hostages_released: int = 0
        self.demands_met: int = 0
    
    def get_available_options(self, player_state: dict) -> List[DialogueOption]:
        """Get available dialogue options based on current game state."""
        if "scenario" in player_state:
            if player_state["role"] == "negotiator":
                return player_state["scenario"].get_negotiator_options(player_state)
            else:
                return player_state["scenario"].get_hostage_taker_options(player_state)
        
        # Fallback to basic options if no scenario is provided
        return self._get_basic_options(player_state)
    
    def _get_basic_options(self, player_state: dict) -> List[DialogueOption]:
        """Get basic dialogue options when no scenario is provided."""
        options = []
        
        if player_state["role"] == "negotiator":
            options.extend([
                DialogueOption(
                    text="Let's talk about this. No one needs to get hurt.",
                    type=DialogueType.EMPATHY,
                    effects=[DialogueEffect.STRESS_DECREASE, DialogueEffect.TRUST_INCREASE],
                    requirements={},
                    success_chance=0.8
                ),
                DialogueOption(
                    text="The building is surrounded. There's no way out.",
                    type=DialogueType.THREAT,
                    effects=[DialogueEffect.STRESS_INCREASE, DialogueEffect.TRUST_DECREASE],
                    requirements={"swat_team_ready": True},
                    success_chance=0.6
                )
            ])
        else:
            options.extend([
                DialogueOption(
                    text="I want a helicopter and safe passage, or people start dying.",
                    type=DialogueType.DEMAND,
                    effects=[DialogueEffect.TENSION_INCREASE, DialogueEffect.TRUST_DECREASE],
                    requirements={},
                    success_chance=0.4
                ),
                DialogueOption(
                    text="I'm willing to release a hostage as a sign of good faith.",
                    type=DialogueType.REASON,
                    effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
                    requirements={"hostages_count": ">1"},
                    success_chance=0.9
                )
            ])
        
        return options
    
    def process_dialogue(self, option: DialogueOption, game_state: dict) -> dict:
        """Process a chosen dialogue option and return its effects."""
        effects = []
        
        # Calculate success based on various factors
        success = self._calculate_success(option, game_state)
        
        # Generate appropriate response
        response = self._generate_response(option, success, game_state)
        
        # Apply effects based on success/failure
        if success:
            for effect in option.effects:
                effect_result = self._apply_effect(effect, game_state)
                effects.append(effect_result)
                
                # Handle special effects
                if effect == DialogueEffect.HOSTAGE_RELEASE:
                    self.hostages_released += 1
                elif effect == DialogueEffect.DEMAND_ACCEPTED:
                    self.demands_met += 1
                elif effect == DialogueEffect.INTEL_GAINED:
                    self.intel_level = min(1.0, self.intel_level + 0.2)
        else:
            # Apply negative effects on failure
            effects.append(self._apply_effect(DialogueEffect.TRUST_DECREASE, game_state))
            effects.append(self._apply_effect(DialogueEffect.TENSION_INCREASE, game_state))
            
            # Special failure effects
            if option.type == DialogueType.THREAT:
                effects.append(self._apply_effect(DialogueEffect.THREAT_ESCALATION, game_state))
        
        # Record dialogue in history with context
        dialogue_entry = {
            "text": option.text,
            "type": option.type.value,
            "success": success,
            "effects": effects,
            "response": response,
            "turn": game_state.get("current_turn", 0),
            "trust_level": self.trust_level,
            "tension_level": self.tension_level,
            "intel_level": self.intel_level
        }
        self.dialogue_history.append(dialogue_entry)
        
        return {
            "success": success,
            "effects": effects,
            "response": response,
            "dialogue_history": self.dialogue_history,
            "state_changes": {
                "hostages_released": self.hostages_released,
                "demands_met": self.demands_met,
                "intel_level": self.intel_level
            }
        }
    
    def _calculate_success(self, option: DialogueOption, game_state: dict) -> bool:
        """Calculate if the dialogue option succeeds based on various factors."""
        base_chance = option.success_chance
        
        # Modify chance based on trust and tension
        if option.type in [DialogueType.EMPATHY, DialogueType.REASON]:
            base_chance += self.trust_level * 0.2
        elif option.type in [DialogueType.THREAT, DialogueType.DEMAND]:
            base_chance -= self.tension_level * 0.2
        
        # Consider special conditions
        if game_state.get("elderly_hostage_critical", False) and option.type == DialogueType.REASON:
            base_chance += 0.1
        
        # Ensure chance stays within bounds
        base_chance = max(0.1, min(0.9, base_chance))
        
        return random.random() < base_chance
    
    def _apply_effect(self, effect: DialogueEffect, game_state: dict) -> dict:
        """Apply a dialogue effect to the game state."""
        effect_magnitude = 0.1  # Base effect magnitude
        
        # Modify magnitude based on current state
        if self.tension_level > 0.7:
            effect_magnitude *= 1.5
        elif self.trust_level > 0.7:
            effect_magnitude *= 1.2
        
        # Apply the effect
        if effect in [DialogueEffect.STRESS_INCREASE, DialogueEffect.TENSION_INCREASE]:
            self.tension_level = min(1.0, self.tension_level + effect_magnitude)
        elif effect in [DialogueEffect.STRESS_DECREASE, DialogueEffect.TENSION_DECREASE]:
            self.tension_level = max(0.0, self.tension_level - effect_magnitude)
        elif effect == DialogueEffect.TRUST_INCREASE:
            self.trust_level = min(1.0, self.trust_level + effect_magnitude)
        elif effect == DialogueEffect.TRUST_DECREASE:
            self.trust_level = max(0.0, self.trust_level - effect_magnitude)
        elif effect == DialogueEffect.THREAT_ESCALATION:
            self.tension_level = min(1.0, self.tension_level + effect_magnitude * 2)
            self.trust_level = max(0.0, self.trust_level - effect_magnitude)
        
        return {
            "type": effect.value,
            "magnitude": effect_magnitude,
            "new_tension": self.tension_level,
            "new_trust": self.trust_level
        }
    
    def _generate_response(self, option: DialogueOption, success: bool, game_state: dict) -> str:
        """Generate an appropriate response based on the dialogue type, success, and game state."""
        if option.type == DialogueType.THREAT:
            if success:
                return [
                    "The hostage taker appears unsettled by your statement, but maintains composure. 'You think I haven't thought this through? I still have the upper hand here.'",
                    "You notice a slight tremor in the hostage taker's voice. 'Don't push me into doing something we'll both regret.'",
                    "The atmosphere becomes noticeably tenser. 'Your threats don't scare me, but they might scare the hostages.'"
                ][random.randint(0, 2)]
            else:
                return [
                    "The hostage taker laughs dismissively. 'You think threats will work on me? I've got nothing to lose here.'",
                    "'Is that supposed to scare me? Maybe I should show you who's really in control here.'",
                    "Your threat seems to have the opposite effect. The hostage taker's resolve appears to strengthen."
                ][random.randint(0, 2)]
        
        elif option.type == DialogueType.EMPATHY:
            if success:
                return [
                    "You notice a slight change in the hostage taker's tone. 'I don't want anyone to get hurt either, but I need guarantees.'",
                    "The hostage taker's stance softens slightly. 'At least you're trying to understand the situation.'",
                    "'Look, I'm not the bad guy here. I just need this to work out.'"
                ][random.randint(0, 2)]
            else:
                return [
                    "The hostage taker remains cold. 'Save your sympathy. Just get me what I want.'",
                    "'Don't try to play psychologist with me. Focus on meeting my demands.'",
                    "Your attempt at empathy seems to irritate the hostage taker. 'Stop wasting my time!'"
                ][random.randint(0, 2)]
        
        elif option.type == DialogueType.DEMAND:
            if success:
                return [
                    "The negotiator considers your demand carefully. 'We can work towards that, but we need a show of good faith.'",
                    "'I understand your demands. Let's talk about how we can make this work for everyone.'",
                    "There's a thoughtful pause. 'Those terms might be possible, but we need to establish trust first.'"
                ][random.randint(0, 2)]
            else:
                return [
                    "The negotiator stands firm. 'You know we can't agree to those terms immediately.'",
                    "'That's not how this works. We need to take this one step at a time.'",
                    "'Those demands are unrealistic. Let's focus on what's actually possible.'"
                ][random.randint(0, 2)]
        
        elif option.type == DialogueType.REASON:
            if success:
                return [
                    "Your logical approach seems to resonate. 'That's a fair point. Let's discuss this further.'",
                    "There's a moment of consideration. 'You make some sense. Maybe we can work something out.'",
                    "The tension eases slightly. 'Okay, I'm listening. What exactly are you proposing?'"
                ][random.randint(0, 2)]
            else:
                return [
                    "Your attempt at reasoning is met with skepticism. 'Words are cheap. I need action.'",
                    "'Logic isn't going to get us anywhere. I need results.'",
                    "The response is dismissive. 'Stop trying to rationalize and start meeting demands.'"
                ][random.randint(0, 2)]
        
        return "The situation remains tense as both sides consider their next move." 