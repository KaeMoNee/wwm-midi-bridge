import customtkinter as ctk
from customtkinter import CTkBaseClass

from core import i18n
from ui.style import Theme


class I18nMixin(CTkBaseClass):
    """Mixin to auto-update text when the language changes."""

    def __init__(self, text_key, i18n_kwargs=None, **kwargs):
        self.text_key = text_key
        self.i18n_kwargs = i18n_kwargs or {}
        kwargs['text'] = i18n.t(self.text_key, **self.i18n_kwargs)
        super().__init__(**kwargs)
        i18n.add_listener(self)

    def update_text(self):
        """Callback when the language changes. Called by i18n."""
        try:
            if self.winfo_exists():
                self.configure(text=i18n.t(self.text_key, **self.i18n_kwargs))
        except Exception as e:
            # Widget likely destroyed, but not yet garbage collected, log for debugging
            print(f"Error updating text: {e}")
            pass

    def set_key(self, new_key):
        """Allow changing the key dynamically (e.g., for state changes like Start/Stop)."""
        self.text_key = new_key
        self.update_text()

    def destroy(self):
        # CustomTkinter widgets usually clean up well, but we can be explicit if needed.
        # Since we use WeakSet in i18n, strict manual removal isn't critical but is good practice.
        super().destroy()


class I18nLabel(I18nMixin, ctk.CTkLabel):
    def __init__(self, master, text_key, **kwargs):
        super().__init__(text_key, master=master, **kwargs)


class I18nButton(I18nMixin, ctk.CTkButton):
    def __init__(self, master, text_key, **kwargs):
        super().__init__(text_key, master=master, **kwargs)


class I18nCheckBox(I18nMixin, ctk.CTkCheckBox):
    def __init__(self, master, text_key, **kwargs):
        super().__init__(text_key, master=master, **kwargs)


class I18nMenuButton(I18nButton):
    def __init__(self, master, text_key, icon=None, **kwargs):
        super().__init__(master, text_key, **kwargs)
        self.configure(
            fg_color="transparent",  # Blend with background
            hover_color=Theme.TEXT_DIM,  # Highlight color
            text_color=Theme.TEXT_MAIN,
            anchor="w",  # Align text to the left
            corner_radius=0,
            font=Theme.FONT_NORMAL,
            image=icon,
            compound="left",  # Icon to the left of text,
            border_spacing=8,
        )


def create_header_label(parent, text_key, **i18n_args):
    return I18nLabel(parent, text_key, font=Theme.FONT_HEADER,
                     i18n_kwargs=i18n_args)


def create_normal_label(parent, text_key, **i18n_args):
    return I18nLabel(parent, text_key, font=Theme.FONT_NORMAL,
                     i18n_kwargs=i18n_args)

def create_action_button(parent, text_key, command, **i18n_args):
    return I18nButton(parent, text_key,
                      font=Theme.FONT_HEADER,
                      fg_color=Theme.SUCCESS,
                      hover_color=Theme.SUCCESS_HOVER if hasattr(Theme, 'SUCCESS_HOVER') else Theme.SUCCESS,
                      command=command,
                      i18n_kwargs=i18n_args)


def create_danger_button(parent, text_key, command, **i18n_args):
    return I18nButton(parent, text_key,
                      font=Theme.FONT_HEADER,
                      fg_color=Theme.DANGER,
                      hover_color=Theme.DANGER_HOVER if hasattr(Theme, 'DANGER_HOVER') else Theme.DANGER,
                      command=command,
                      i18n_kwargs=i18n_args)
