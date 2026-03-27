from ursina import *
# At the top of abilities.py add:
from code.entity.player.weapons import Sword, Spear, Mace, Knife, Bow, Crossbow, MagicStaff


# ============================================================
#  ABILITY BASE CLASS
# ============================================================

class Ability:
    """
    Base class for all abilities.
    Every ability must implement apply() and remove().
    """
    name        = "Unknown"
    description = ""
    kind        = "Passive"   # "Passive", "Active" or "Weapon"

    def apply(self, player_stats, player):
        """Called when the player picks this ability."""
        pass

    def remove(self, player_stats, player):
        """Called when abilities are reset."""
        pass


# ============================================================
#  PASSIVE ABILITIES
# ============================================================

class AbilityHealing(Ability):
    name        = "Regeneration"
    description = "+1 HP every second"
    kind        = "Passive"

    def apply(self, player_stats, player):
        player_stats.health_regen_per_second += 1.0

    def remove(self, player_stats, player):
        player_stats.health_regen_per_second = 0.0


class AbilityMaxHealth(Ability):
    name        = "+25 Max Health"
    description = "Increases maximum health by 25"
    kind        = "Passive"

    def apply(self, player_stats, player):
        player_stats.MAX_HEALTH += 25
        player_stats.health     += 25   # also heal the bonus amount

    def remove(self, player_stats, player):
        player_stats.MAX_HEALTH  = 100
        player_stats.health      = 100
        # player_stats.MAX_HEALTH  = max(1, player_stats.MAX_HEALTH - 25) OG
        # player_stats.health      = min(player_stats.health, player_stats.MAX_HEALTH) OG


class AbilityMaxStamina(Ability):
    name        = "+25 Max Stamina"
    description = "Increases maximum stamina by 25"
    kind        = "Passive"

    def apply(self, player_stats, player):
        player_stats.MAX_STAMINA += 25
        player_stats.stamina     += 25

    def remove(self, player_stats, player):
        player_stats.MAX_STAMINA = max(1, player_stats.MAX_STAMINA - 25)
        player_stats.stamina     = min(player_stats.stamina, player_stats.MAX_STAMINA)


class AbilityStaminaRegen(Ability):
    name        = "Stamina Regen+"
    description = "Stamina recharges faster"
    kind        = "Passive"
    BONUS       = 8.0   # extra regen per second

    def apply(self, player_stats, player):
        player_stats.STAMINA_REGEN_RATE += self.BONUS

    def remove(self, player_stats, player):
        player_stats.STAMINA_REGEN_RATE = 12.0
        # player_stats.STAMINA_REGEN_RATE -= self.BONUS


class AbilityLowerGravity(Ability):
    name        = "Lower Gravity"
    description = "Gravity is reduced (floatier jumps)"
    kind        = "Passive"

    def apply(self, player_stats, player):
        player.gravity = max(0.0, player.gravity - 0.1)

    def remove(self, player_stats, player):
        player.gravity = 1.0


class AbilityFasterMovement(Ability):
    name        = "Swift Feet"
    description = "Walk and sprint speed x1.25"
    kind        = "Passive"
    MULTIPLIER  = 1.25

    def apply(self, player_stats, player):
        player_stats.walk_speed   *= self.MULTIPLIER
        player_stats.sprint_speed *= self.MULTIPLIER

    def remove(self, player_stats, player):
        player_stats.walk_speed   /= 10
        player_stats.sprint_speed /= 22
        # player_stats.walk_speed   /= self.MULTIPLIER
        # player_stats.sprint_speed /= self.MULTIPLIER


class AbilityHigherJump(Ability):
    name        = "High Jump"
    description = "Jump height is doubled"
    kind        = "Passive"

    def apply(self, player_stats, player):
        player.jump_height *= 2

    def remove(self, player_stats, player):
        player.jump_height = 2


# ============================================================
#  ACTIVE ABILITIES
# ============================================================

class AbilityDoubleJump(Ability):
    name        = "Double Jump"
    description = "Jump a second time in the air"
    kind        = "Active"

    def apply(self, player_stats, player):
        player_stats.can_double_jump = True 

    def remove(self, player_stats, player):
        player_stats.can_double_jump = False


# ============================================================
#  WEAPON ABILITIES
# ============================================================

class AbilitySword(Ability):
    name        = "Sword"
    description = "Default melee, 15-25 damage, medium range"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Sword)

    def remove(self, player_stats, player):
        pass


class AbilitySpear(Ability):
    name        = "Spear"
    description = "15-20 damage (±5) at longer range"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Spear)

    def remove(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Sword)


class AbilityMace(Ability):
    name        = "Mace"
    description = "More damage the longer you've been airborne"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Mace)

    def remove(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Sword)


class AbilityKnife(Ability):
    name        = "Knife"
    description = "3-7 damage, very fast, cheap stamina cost"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Knife)

    def remove(self, player_stats, player):
        from code.entity.player.playerdata import _swap_melee
        _swap_melee(Sword)


class AbilityBow(Ability):
    name        = "Bow"
    description = "Default ranged, standard arrow, costs 20 stamina"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_ranged
        _swap_ranged(Bow)

    def remove(self, player_stats, player):
        pass


class AbilityCrossbow(Ability):
    name        = "Crossbow"
    description = "Fast heavy bolts, costs 35 stamina"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_ranged
        _swap_ranged(Crossbow)

    def remove(self, player_stats, player):
        from code.entity.player.playerdata import _swap_ranged
        _swap_ranged(Bow)


class AbilityMagicStaff(Ability):
    name        = "Magic Staff"
    description = "Fireballs with gentle arc, costs 40 stamina"
    kind        = "Weapon"

    def apply(self, player_stats, player):
        from code.entity.player.playerdata import _swap_ranged
        _swap_ranged(MagicStaff)

    def remove(self, player_stats, player):
        from code.entity.player.playerdata import _swap_ranged
        _swap_ranged(Bow)



# ============================================================
#  ABILITY POOL  (all available abilities to pick from)
# ============================================================

ALL_ABILITIES = [
    AbilityHealing(),
    AbilityMaxHealth(),
    AbilityMaxStamina(),
    AbilityStaminaRegen(),
    AbilityLowerGravity(),
    AbilityFasterMovement(),
    AbilityHigherJump(),
    AbilityDoubleJump(),
    # Melee weapons
    AbilitySword(),      # default, only offered if player has a different melee
    AbilitySpear(),
    AbilityMace(),
    AbilityKnife(),
    # Ranged weapons
    AbilityBow(),        # default, only offered if player has a different ranged
    AbilityCrossbow(),
    AbilityMagicStaff(),
]


# ============================================================
#  ABILITY MANAGER
# ============================================================

class AbilityManager:
    """
    Tracks which abilities the player currently has.
    Handles offering random choices and applying/removing abilities.
    """

    def __init__(self, player_stats, player):
        self.player_stats     = player_stats
        self.player           = player

        # Abilities the player has currently picked
        self.current_abilities: list[Ability] = []

    def offer_choices(self, on_chosen_callback):
        import random

        # Names of abilities the player already owns
        already_owned_names = {a.name for a in self.current_abilities}

        # Also exclude the current active weapons by name
        # so the player is never offered what they already have equipped
        from code.entity.player.playerdata import current_melee, current_ranged
        if current_melee is not None:
            already_owned_names.add(current_melee.name)
        if current_ranged is not None:
            already_owned_names.add(current_ranged.name)

        # Filter out anything already owned or equipped
        available = [
            a for a in ALL_ABILITIES
            if a.name not in already_owned_names
        ]

        if not available:
            print("[AbilityManager] No abilities left to offer!")
            if on_chosen_callback:
                on_chosen_callback()
            return

        choices = random.sample(available, min(3, len(available)))
        AbilityPickerUI(choices, self._on_ability_picked, on_chosen_callback)

    def _on_ability_picked(self, ability: Ability, on_chosen_callback):
        """Apply the chosen ability and add it to the active list."""
        ability.apply(self.player_stats, self.player)
        self.current_abilities.append(ability)
        print(f"[Abilities] Picked: {ability.name}")
        if on_chosen_callback:
            on_chosen_callback()

    def reset_all(self):
        """Remove every active ability, used on player death."""
        for ability in self.current_abilities:
            ability.remove(self.player_stats, self.player)
        self.current_abilities.clear()
        print("[Abilities] All abilities reset.")


# ============================================================
#  ABILITY PICKER UI
# ============================================================

# Card colors per ability kind
KIND_COLORS = {
    "Passive": color.rgba(0.10, 0.10, 0.40, 0.95),
    "Active":  color.rgba(0.10, 0.35, 0.10, 0.95),
    "Weapon":  color.rgba(0.40, 0.10, 0.10, 0.95),
}
KIND_HIGHLIGHT = {
    "Passive": color.rgba(0.20, 0.20, 0.60, 0.95),
    "Active":  color.rgba(0.20, 0.55, 0.20, 0.95),
    "Weapon":  color.rgba(0.60, 0.20, 0.20, 0.95),
}


class AbilityPickerUI:
    """
    Shows 3 ability cards and lets the player pick one.
    Pauses the player while the menu is open.
    """

    def __init__(self, choices: list, on_picked, on_done):
        self.choices   = choices
        self.on_picked = on_picked
        self.on_done   = on_done
        self._entities = []

        # Pause the player
        from code.entity.player.playerdata import player
        player.enabled = False
        mouse.locked   = False
        mouse.visible  = True

        # -- Dark overlay --------------------------------------------------
        bg = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0, 0, 0, 0.75),
            scale    = (2, 2),
            z        = 0.1,
        )
        self._entities.append(bg)

        # -- Title ---------------------------------------------------------
        title = Text(
            text     = "Choose an Ability",
            parent   = camera.ui,
            scale    = 3.0,
            position = (0, 0.38, -0.1),
            origin   = (0, 0),
            color    = color.rgba(1.0, 0.85, 0.20, 1.0),
        )
        self._entities.append(title)

        # -- Three ability cards -------------------------------------------
        card_positions = [-0.45, 0.0, 0.45]
        for i, ability in enumerate(choices):
            self._make_card(ability, card_positions[i])

    def _make_card(self, ability: Ability, x: float):
        """Build a single ability card button."""
        card_col      = KIND_COLORS.get(ability.kind,     color.rgba(0.2, 0.2, 0.2, 0.95))
        card_hover    = KIND_HIGHLIGHT.get(ability.kind,  color.rgba(0.4, 0.4, 0.4, 0.95))

        # Card background button
        card = Button(
            parent          = camera.ui,
            position        = (x, 0.0, -0.1),
            scale           = (0.30, 0.45),
            color           = card_col,
            highlight_color = card_hover,
            pressed_color   = card_hover,
        )
        card.on_click = lambda a=ability: self._pick(a)
        self._entities.append(card)

        # Kind label (Passive / Active / Weapon)
        kind_text = Text(
            text     = ability.kind.upper(),
            parent   = camera.ui,
            scale    = 0.9,
            position = (x, 0.18, -0.2),
            origin   = (0, 0),
            color    = color.rgba(1.0, 1.0, 0.5, 0.9),
        )
        self._entities.append(kind_text)

        # Ability name
        name_text = Text(
            text     = ability.name,
            parent   = camera.ui,
            scale    = 1.3,
            position = (x, 0.10, -0.2),
            origin   = (0, 0),
            color    = color.rgba(1.0, 1.0, 1.0, 1.0),
        )
        self._entities.append(name_text)

        # Ability description
        desc_text = Text(
            text     = ability.description,
            parent   = camera.ui,
            scale    = 0.85,
            position = (x, -0.02, -0.2),
            origin   = (0, 0),
            color    = color.rgba(0.85, 0.85, 0.85, 0.9),
            wordwrap = 18,
        )
        self._entities.append(desc_text)

    def _pick(self, ability: Ability):
        """Player picked an ability, apply it and close the UI."""
        self._close()
        self.on_picked(ability, self.on_done)

    def _close(self):
        """Destroy all UI elements and re-enable the player."""
        from code.entity.player.playerdata import player
        player.enabled = True
        mouse.locked   = True
        mouse.visible  = False

        for e in self._entities:
            destroy(e)
        self._entities.clear()