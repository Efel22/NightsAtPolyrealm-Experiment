from ursina import *
from code.sound import play_sound


from code.entity.player.xp_system import xp_system


class PlayerStats:
    """
    Tracks and displays the player's health, stamina and XP.
    Layout (bottom center of screen):
      ❤ [health bar]    level number    ⚡ [stamina bar]
                        [xp bar]
    """

    STAMINA_DRAIN_RATE  = 18.0
    STAMINA_REGEN_RATE  = 12.0

    def __init__(self, player, walk_speed: float, sprint_speed: float):

        
        self.MAX_HEALTH   = 100.0
        self.MAX_STAMINA  = 100.0

        self.player       = player
        self.walk_speed   = walk_speed
        self.sprint_speed = sprint_speed

        self.health       = self.MAX_HEALTH
        self.stamina      = self.MAX_STAMINA

        self._sprinting   = False

        # Set by playerdata.setup_combat() after everything is initialised
        self.death_screen   = None
        self.entity_manager = None

        self.health_regen_per_second  = 0.0
        self.time_in_air              = 0.0
        self.can_double_jump          = False
        self.has_done_double_jump     = False
        self.player.jump_height       = 4
        self.active_melee_weapon      = "sword"
        self.active_ranged_weapon     = "bow"

        # Create the UI for health, stamina, lvl, etc...
        self.create_ui()

    def create_ui(self):

        # -- Layout constants ----------------------------------------------
        bar_w      = 0.32    # width of health and stamina bars
        bar_h      = 0.032   # height of health and stamina bars
        xp_bar_w   = 0.40    # XP bar is wider and centered
        xp_bar_h   = 0.022
        bottom_y   = -0.42   # Y position of health/stamina row
        xp_y       = -0.47   # Y position of XP bar row

        icon_scale = 0.055   # size of heart and lightning icons

        # health bar is left of center, stamina bar is right of center
        health_bar_x  = -0.22
        stamina_bar_x =  0.22
        level_x       =  0.0   # level number sits in the middle

        # -- Health value text (shown inside the health bar) ---------------
        self._health_text = Text(
            text     = f"{int(self.health)}/{int(self.MAX_HEALTH)}",
            parent   = camera.ui,
            scale    = 0.7,
            position = (health_bar_x, bottom_y - 0.003),
            origin   = (0, 0),
            color    = color.rgba(1, 1, 1, 0.95),
        )

        # -- Stamina value text (shown inside the stamina bar) -------------
        self._stamina_text = Text(
            text     = f"{int(self.stamina)}/{int(self.MAX_STAMINA)}",
            parent   = camera.ui,
            scale    = 0.7,
            position = (stamina_bar_x, bottom_y - 0.003),
            origin   = (0, 0),
            color    = color.rgba(1, 1, 1, 0.95),
        )

        # -- Health icon (heart texture) -----------------------------------
        self._heart_icon = Entity(
            parent   = camera.ui,
            model    = 'quad',
            texture  = 'assets/textures/heart.png',
            scale    = icon_scale,
            position = (health_bar_x - bar_w/2 - 0.04, bottom_y),
        )

        # -- Health bar background -----------------------------------------
        self._health_bg = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.20, 0.03, 0.03, 0.85),
            scale    = (bar_w, bar_h),
            position = (health_bar_x, bottom_y),
        )

        # -- Health bar fill -----------------------------------------------
        self._health_fill = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.85, 0.10, 0.10, 0.95),
            scale    = (bar_w, bar_h),
            position = (health_bar_x - bar_w/2, bottom_y),
            origin   = (-0.5, 0),
        )

        # -- Level number (center between the two bars) --------------------
        self._level_text = Text(
            text     = "0",
            parent   = camera.ui,
            scale    = 1.8,
            position = (level_x, bottom_y - 0.05),
            origin   = (0, 0),
            color    = color.rgba(1, 1, 1, 1.0),
        )

        # -- Stamina icon (lightning texture) -----------------------------
        self._lightning_icon = Entity(
            parent   = camera.ui,
            model    = 'quad',
            texture  = 'assets/textures/stamina.png',
            scale    = icon_scale,
            position = (stamina_bar_x - bar_w/2 - 0.04, bottom_y),
        )

        # -- Stamina bar background ----------------------------------------
        self._stamina_bg = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.25, 0.18, 0.02, 0.85),
            scale    = (bar_w, bar_h),
            position = (stamina_bar_x, bottom_y),
        )

        # -- Stamina bar fill ----------------------------------------------
        self._stamina_fill = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.95, 0.65, 0.05, 0.95),
            scale    = (bar_w, bar_h),
            position = (stamina_bar_x - bar_w/2, bottom_y),
            origin   = (-0.5, 0),
        )

        # -- XP bar background (full width, centered below the other bars) -
        self._xp_bg = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.05, 0.15, 0.25, 0.85),
            scale    = (xp_bar_w, xp_bar_h),
            position = (0, xp_y),
        )

        # -- XP bar fill (cyan/blue) ---------------------------------------
        self._xp_fill = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.10, 0.70, 0.95, 0.95),
            scale    = (xp_bar_w, xp_bar_h),
            position = (-xp_bar_w/2, xp_y),
            origin   = (-0.5, 0),
        )

         # -- Damage flash overlay, full screen red that fades out ---------
        self._damage_flash = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0.8, 0.0, 0.0, 0.0),  # starts fully transparent
            scale    = (2, 2),                            # covers the whole screen
            z        = -1,                                # render behind UI bars
        )

        # -- Controls info text (disappears after 15 seconds) -----------
        controls_text = Text(
            text="Controls:\nWASD = Move | SPACE = Jump | L_SHIFT = Sprint\nLeft-Click = Melee Attack \n Right-Click = Ranged Attack",
            parent=camera.ui,
            scale=1.2,
            position=(0, 0.35),  # top-center of the screen
            origin=(0, 0),
            color=color.rgba(1, 1, 1, 0.95)
        )
        invoke(destroy, controls_text, delay=15)  # remove after 15 seconds

        # Store bar widths for scaling in update
        self._bar_w    = bar_w
        self._xp_bar_w = xp_bar_w

    def use_stamina(self, amount: float) -> bool:
        """
        Spend stamina for an action.
        Returns True if there was enough stamina and it was spent,
        False if there wasn't enough and the action should be blocked.
        """
        if self.stamina < amount:
            return False
        self.stamina = max(0.0, self.stamina - amount)
        return True

    # ------------------------------------------------------------------ #
    #  Sprinting                                                           #
    # ------------------------------------------------------------------ #

    def try_start_sprint(self):
        """Only starts sprint if there is any stamina left."""
        if self.stamina <= 0 or self.health <= 0:
            return
        self._sprinting   = True
        self.player.speed = self.sprint_speed

    def stop_sprint(self):
        self._sprinting   = False
        self.player.speed = self.walk_speed

    @property
    def is_sprinting(self) -> bool:
        return self._sprinting

    # ------------------------------------------------------------------ #
    #  Damage                                                              #
    # ------------------------------------------------------------------ #

    def take_damage(self, amount: float):
        self.health = max(0.0, self.health - amount)
        play_sound("entity/hurt_player", volume=0.8)
        self._trigger_damage_flash()
        if self.health <= 0:
            self._on_death()

    def _trigger_damage_flash(self):
        """Flash the screen red then fade back to transparent."""
        # Snap to full red instantly
        self._damage_flash.color = color.rgba(0.8, 0.0, 0.0, 0.55)
        # Fade back to transparent over 0.5 seconds
        self._damage_flash.animate_color(
            color.rgba(0.8, 0.0, 0.0, 0.0),
            duration = 0.5,
            curve    = curve.linear
        )

    def _on_death(self):
        """Kill all enemies and show the death screen."""
        # Kill every living entity
        for e in list(self.entity_manager.entities):
            e.dead = True

        # Show the death screen
        if self.death_screen is not None:
            self.death_screen.show()

    # ------------------------------------------------------------------ #
    #  Level Up                                                           #
    # ------------------------------------------------------------------ #

    def on_level_up(self, new_level: int):
        """
        Called every time the player levels up.
        Each level grants +2 max health and +2 max stamina.
        At level 5 that's +10 to each, at level 10 that's +20, etc.
        """
        bonus = 2
        # bonus = new_level * 2 # OLD

        # Increase the max values
        # self.MAX_HEALTH  = new_level + bonus 
        # self.MAX_STAMINA  = new_level + bonus 
        self.MAX_HEALTH  += bonus 
        self.MAX_STAMINA += bonus

        # Also heal and restore stamina to the new max so the level up feels rewarding
        self.health  = self.MAX_HEALTH
        self.stamina = self.MAX_STAMINA

        print(f"[PlayerStats] Level {new_level}! "
              f"Max HP: {self.MAX_HEALTH} Max SP: {self.MAX_STAMINA}")

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #
    
    def update(self, dt: float):
        self._update_stamina(dt)
        self._update_bars()

        # Passive health regeneration (from Healing ability)
        if self.health_regen_per_second > 0 and self.health < self.MAX_HEALTH:
            self.health = min(self.MAX_HEALTH,
                              self.health + self.health_regen_per_second * dt)

    def _update_stamina(self, dt: float):
        is_moving = (held_keys['w'] or held_keys['s'] or
                     held_keys['a'] or held_keys['d'])

        if self._sprinting and is_moving:
            self.stamina -= self.STAMINA_DRAIN_RATE * dt

            # Stop sprinting if stamina runs out
            if self.stamina <= 0:
                self.stamina = 0
                self.stop_sprint()
        else:
            # Regen stamina when not sprinting
            self.stamina = min(self.MAX_STAMINA,
                               self.stamina + self.STAMINA_REGEN_RATE * dt)

    def _update_bars(self):
        """Resize all bars and update the level number."""
        health_pct  = self.health  / self.MAX_HEALTH
        stamina_pct = self.stamina / self.MAX_STAMINA
        xp_pct      = xp_system.xp_progress()

        # Scale fills from the left anchor
        self._health_fill.scale_x  = self._bar_w    * health_pct
        self._stamina_fill.scale_x = self._bar_w    * stamina_pct
        self._xp_fill.scale_x      = self._xp_bar_w * xp_pct

        # Update level number
        self._level_text.text = str(xp_system.player_level)

        self._health_text.text  = f"{int(self.health)}/{int(self.MAX_HEALTH)}"
        self._stamina_text.text = f"{int(self.stamina)}/{int(self.MAX_STAMINA)}"

    def double_jump(self):
        if self.player.grounded or self.has_done_double_jump:
            return

        self.has_done_double_jump = True
        self.player.animate_y(self.player.y+self.player.jump_height, self.player.jump_up_duration, resolution=int(1//time.dt), curve=curve.out_expo)
        invoke(self.player.start_fall, delay=self.player.fall_after)