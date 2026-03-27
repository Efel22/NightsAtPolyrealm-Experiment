from ursina import *
from code.entity.player.night_tracker import night_tracker
from code.sound import play_sound


class DeathScreen:
    """
    Shown when the player dies.
    Displays nights survived and buttons to play again or quit.
    """

    # -- Button colors -----------------------------------------------------
    COLOR_PLAY_NORMAL   = color.rgba(0/255,   228/255,  54/255,  1.0)   # #00e436
    COLOR_PLAY_HOVER    = color.rgba(0/255,   135/255,  81/255,  1.0)   # #008751
    COLOR_QUIT_NORMAL   = color.rgba(255/255, 0/255,    77/255,  1.0)   # #ff004d
    COLOR_QUIT_HOVER    = color.rgba(126/255, 37/255,   83/255,  1.0)   # #7e2553

    def __init__(self, player, on_play_again, on_quit):
        self.on_play_again = on_play_again
        self.on_quit       = on_quit
        self._visible      = False
        self.player        = player
        self._entities     = []   # track all UI entities for cleanup

    def show(self):
        """Display the death screen."""
        if self._visible:
            return
        self._visible = True

        play_sound("entity/death_player")

        # Lock player movement by disabling the controller
        from code.entity.player.playerdata import player
        player.gravity = 0.0
        p_x = self.player.position.x
        p_y = self.player.position.y * 2
        p_z = self.player.position.z
        self.player.position = (p_x, p_y, p_z)
        if hasattr(self.player, 'velocity'):
            self.player.velocity = Vec3(0,0,0)

        mouse.locked  = False
        mouse.visible = True

        player.enabled = False

        # -- Dark overlay, use a high Z so it's behind buttons but above world -
        bg = Entity(
            parent   = camera.ui,
            model    = 'quad',
            color    = color.rgba(0, 0, 0, 0.82),
            scale    = (2, 2),
            z        = 0.1,    # <- positive Z is BEHIND in camera.ui space
        )
        self._entities.append(bg)

        # -- YOU DIED title ------------------------------------------------
        title = Text(
            text     = "YOU DIED",
            parent   = camera.ui,
            scale    = 5,
            position = (0, 0.28, -0.1),   # <- negative Z = in front
            origin   = (0, 0),
            color    = color.rgba(1.0, 0.0, 0.30, 1.0),
        )
        self._entities.append(title)

        # -- Nights survived -----------------------------------------------
        nights_text = Text(
            text     = f"Nights Survived: {night_tracker.nights_survived}",
            parent   = camera.ui,
            scale    = 2.2,
            position = (0, 0.12, -0.1),
            origin   = (0, 0),
            color    = color.rgba(1.0, 1.0, 1.0, 0.9),
        )
        self._entities.append(nights_text)

        # -- Play Again button ---------------------------------------------
        self._play_btn = self._make_button(
            text         = "Play Again",
            position     = (0, -0.05, -0.1),
            normal_color = self.COLOR_PLAY_NORMAL,
            hover_color  = self.COLOR_PLAY_HOVER,
            on_click     = self._on_play_clicked,
        )

        # -- Quit button ---------------------------------------------------
        self._quit_btn = self._make_button(
            text         = "Quit",
            position     = (0, -0.18, -0.1),
            normal_color = self.COLOR_QUIT_NORMAL,
            hover_color  = self.COLOR_QUIT_HOVER,
            on_click     = self._on_quit_clicked,
        )

    def _make_button(self, text, position, normal_color, hover_color, on_click):
        btn = Button(
            text            = text,
            parent          = camera.ui,
            position        = position,
            scale           = (0.28, 0.07),
            color           = normal_color,
            highlight_color = hover_color,
            pressed_color   = hover_color,
        )
        btn.on_click = on_click
        self._entities.append(btn)
        return btn

    def hide(self):
        """Remove the death screen and re-enable the player."""
        from code.entity.player.playerdata import player
        player.enabled = True

        for e in self._entities:
            destroy(e)
        self._entities.clear()
        self._visible = False
        mouse.locked  = True
        mouse.visible = False

    def _make_button(self, text, position, normal_color, hover_color, on_click):
        """Create a styled button with hover color change."""
        btn = Button(
            text          = text,
            parent        = camera.ui,
            position      = position,
            scale         = (0.28, 0.07),
            color         = normal_color,
            highlight_color = hover_color,
            pressed_color = hover_color,
        )
        btn.on_click = on_click
        self._entities.append(btn)
        return btn

    def _on_play_clicked(self):
        play_sound("gui/click_button")
        self.hide()
        self.on_play_again()

    def _on_quit_clicked(self):
        play_sound("gui/click_button")
        self.on_quit()