import webbrowser

import customtkinter as ctk
import requests
from PIL import Image
from packaging import version

from core import logger, i18n, config, util
from core.config import REPO_URL, VERSION, REPO_RELEASE_CHECK_URL
from core.midi_handler import MidiHandler, get_ports
from ui import components
from ui.components import I18nButton
from ui.style import Theme
from ui.view.bridge_view import BridgeView
from ui.view.manual_player_view import ManualPlayerView
from ui.view.player_view import PlayerView
from ui.view.settings_view import SettingsView


def check_for_updates() -> bool:
    try:
        logger.log(i18n.t("version.checking"))
        response = requests.get(REPO_RELEASE_CHECK_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            new_version = data['tag_name'].replace('v', '')

            if version.parse(new_version) > version.parse(VERSION):
                return True
        return False
    except Exception as e:
        logger.log(i18n.t("version.error_checking", error=e))
        return False


def open_url(url: str):
    logger.log(f"Opening URL: {url}")
    webbrowser.open(url)


class MidiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.midi_handler = MidiHandler()

        self.title(i18n.t("app_title"))
        self.geometry("900x800")
        self.configure(fg_color=Theme.BG_MAIN)

        self.iconbitmap(util.resource_path("assets/icon.ico"))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view = None

        self.lang_select = None
        self.check_verbose = None
        self.device_list = None
        self.btn_refresh = None
        self.btn_run = None
        self.working_area = None

        self.setup_sidenav()
        self.setup_main_area()

        # Load initial state
        self.refresh_devices()

        self.open_menu("bridge")

        # Auto-connect if filter is set
        filter_name = config.get_device_name_filter()
        if filter_name:
            self.auto_connect(filter_name)

    def setup_sidenav(self):
        sidenav = ctk.CTkFrame(self, corner_radius=0, fg_color=Theme.BG_PANEL)
        sidenav.grid(row=0, column=0, sticky="nsew")
        sidenav.grid_rowconfigure(3, weight=1)
        sidenav.grid_columnconfigure(0, weight=1)

        # --- Header Section---
        header = ctk.CTkFrame(sidenav, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=(0, 1))
        header.grid_columnconfigure(1, weight=1)
        image_path = util.resource_path("assets/logo_256.png")
        logo_image = ctk.CTkImage(Image.open(image_path), size=(32, 32))

        lbl_image = ctk.CTkLabel(header, text="", image=logo_image)
        lbl_image.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

        lbl_header = components.create_header_label(header, "ui.logo_title")
        lbl_header.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="w")

        # --- Divider ---
        divider = ctk.CTkFrame(sidenav, height=2, corner_radius=0, fg_color=Theme.TEXT_DIM)
        divider.grid(row=1, column=0, sticky="ew")

        # --- Menu Section ---
        menu = ctk.CTkFrame(sidenav, corner_radius=0, fg_color="transparent")
        menu.grid(row=2, column=0, sticky="nsew", padx=(0, 1))
        menu.grid_columnconfigure(0, weight=1)

        bridge_item = components.I18nMenuButton(menu, "ui.menu.bridge", command=lambda: self.open_menu("bridge"))
        bridge_item.grid(row=0, column=0, sticky="ew")

        manual_player_item = components.I18nMenuButton(menu, "ui.menu.manual_player",
                                                       command=lambda: self.open_menu("manual_player"))
        manual_player_item.grid(row=1, column=0, sticky="ew")

        player_item = components.I18nMenuButton(menu, "ui.menu.player", command=lambda: self.open_menu("player"))
        player_item.grid(row=2, column=0, sticky="ew")

        settings_item = components.I18nMenuButton(menu, "ui.menu.settings", command=lambda: self.open_menu("settings"))
        settings_item.grid(row=3, column=0, sticky="ew")

        # --- Footer Controls ---
        footer = ctk.CTkFrame(sidenav, corner_radius=0, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ews", padx=(0, 1))
        footer.grid_columnconfigure(0, weight=1)

        image_path = util.resource_path("assets/github-mark-white.png")
        github_image = ctk.CTkImage(Image.open(image_path), size=(32, 32))
        github_btn = ctk.CTkButton(footer, text="GitHub", image=github_image, command=lambda: open_url(REPO_URL),
                                   fg_color="transparent", hover_color=Theme.TEXT_DIM, corner_radius=0,
                                   border_spacing=0,
                                   compound="left")
        github_btn.grid(row=0, column=0, sticky="ew")

        lbl_version = components.create_normal_label(footer, "version.label", version=VERSION)
        lbl_version.grid(row=1, column=0, sticky="ew")

        # Perform check
        if check_for_updates():
            lbl_update_available = components.create_normal_label(footer, "version.update_available")
            lbl_update_available.grid(row=2, column=0, sticky="ew")

    def setup_main_area(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew")

        # --- Top Bar with MIDI Selection ---
        top_bar = ctk.CTkFrame(main_frame, fg_color=Theme.BG_PANEL, corner_radius=0)
        top_bar.pack(fill="x")

        lbl_device = components.create_normal_label(top_bar, "ui.midi.select_device")
        lbl_device.pack(side="left", padx=(10, 5))

        self.device_list = ctk.CTkOptionMenu(top_bar, values=[i18n.t("ui.midi.no_devices_found")], width=250)
        self.device_list.pack(side="left", padx=5, pady=10)

        self.btn_refresh = ctk.CTkButton(top_bar, text="↻", width=30, fg_color=Theme.ACCENT,
                                         command=self.refresh_devices)
        self.btn_refresh.pack(side="left", padx=5)

        self.btn_run = I18nButton(top_bar, "ui.midi.connect",
                                  fg_color=Theme.SUCCESS, font=Theme.FONT_HEADER,
                                  hover_color=Theme.SUCCESS_HOVER if hasattr(Theme, 'SUCCESS_HOVER') else Theme.SUCCESS,
                                  command=self.toggle_running)
        self.btn_run.pack(side="right", padx=10, pady=10)

        self.working_area = ctk.CTkFrame(main_frame, corner_radius=Theme.CORNER_RADIUS, fg_color=Theme.BG_PANEL)
        self.working_area.pack(fill="both", expand=True, padx=Theme.PAD_STD, pady=Theme.PAD_STD)

        log_box = ctk.CTkTextbox(main_frame, font=Theme.FONT_MONO, state="disabled")
        log_box.pack(side="bottom", fill="x", padx=Theme.PAD_STD, pady=Theme.PAD_STD)
        logger.set_target(log_box)

    def open_menu(self, name: str):
        if self.current_view is not None:
            self.current_view.destroy()

        if name == "bridge":
            self.current_view = BridgeView(self.working_area, corner_radius=8, fg_color=Theme.BG_PANEL)
        elif name == "player":
            self.current_view = PlayerView(self.working_area, corner_radius=8, fg_color=Theme.BG_PANEL)
        elif name == "settings":
            self.current_view = SettingsView(self.working_area, corner_radius=8, fg_color=Theme.BG_PANEL)
        elif name == "manual_player":
            self.current_view = ManualPlayerView(self.working_area, self.midi_handler, corner_radius=8,
                                                 fg_color=Theme.BG_PANEL)

        if self.current_view:
            self.current_view.pack(fill="both", expand=True)

    def refresh_devices(self):
        devices = get_ports()
        if not devices:
            self.device_list.configure(values=["No devices found"])
            self.device_list.set("No devices found")
        else:
            self.device_list.configure(values=devices)
            self.device_list.set(devices[0])

    def auto_connect(self, filter_name):
        devices = get_ports()
        for device in devices:
            if filter_name.lower() in device.lower():
                self.device_list.set(device)
                logger.log(f"Auto-selected device matching '{filter_name}': {device}")
                break

    def toggle_running(self):
        if self.midi_handler.is_running:
            self.midi_handler.stop()
            self.btn_run.set_key("ui.midi.connect")
            self.btn_run.configure(fg_color=Theme.SUCCESS)
            self.device_list.configure(state="normal")
            self.btn_refresh.configure(state="normal")
        else:
            device_name = self.device_list.get()
            if device_name == "No devices found":
                logger.log("Error: No device selected")
                return

            if self.midi_handler.start(device_name):
                self.btn_run.set_key("ui.midi.disconnect")
                self.btn_run.configure(fg_color=Theme.DANGER)
                self.device_list.configure(state="disabled")
                self.btn_refresh.configure(state="disabled")
