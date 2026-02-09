"""Mission message builder for constructing mission messages with modular information."""
import localization


class MissionMessageBuilder:
    """Builder class for constructing mission messages with various information components."""
    
    def __init__(self, mission_id, description, rules, language='ru'):
        """Initialize the mission message builder.
        
        Args:
            mission_id: Mission ID
            description: Mission description
            rules: Mission rules/type
            language: Language code for localized messages
        """
        self.mission_id = mission_id
        self.description = description
        self.rules = rules
        self.language = language
        self.components = []
        
    async def add_double_exp_bonus(self, opponent_name=None):
        """Add information about double experience bonus.
        
        Args:
            opponent_name: Optional name of the opponent (for context)
        """
        if opponent_name:
            message = await localization.get_text(
                "mission_double_xp_bonus",
                self.language,
                opponent_name=opponent_name
            )
        else:
            message = await localization.get_text(
                "mission_double_xp_bonus_generic",
                self.language
            )
        self.components.append(message)
        return self
        
    def add_situation(self, situations):
        """Add situation information.
        
        Args:
            situations: List of situation strings
        """
        if situations:
            for situation in situations:
                self.components.append(situation)
        return self
        
    def add_reinforcement_message(self, message):
        """Add reinforcement restriction message.
        
        Args:
            message: Reinforcement restriction message
        """
        if message:
            self.components.append(message)
        return self
        
    def add_killzone(self, killzone):
        """Add killzone information.
        
        Args:
            killzone: Killzone type
        """
        if killzone:
            self.components.append(f"Killzone: {killzone}")
        return self
        
    def add_custom_info(self, info):
        """Add custom information.
        
        Args:
            info: Custom information string
        """
        if info:
            self.components.append(info)
        return self
        
    def build(self):
        """Build and return the complete mission message.
        
        Returns:
            str: Complete mission message
        """
        # Start with base mission info
        base_message = f"📜{self.description}: {self.rules}\n#{self.mission_id}"
        
        # Add all components
        if self.components:
            full_message = base_message + "\n" + "\n".join(self.components)
        else:
            full_message = base_message
            
        return full_message
