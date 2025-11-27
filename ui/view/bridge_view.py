import customtkinter as ctk

from ui.components import create_header_label, create_normal_label


class BridgeView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        create_header_label(self, "bridge.header").pack(anchor="nw", pady=(20, 10), padx=20)

        self.instruction_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.instruction_frame.pack(fill="x", padx=20, pady=10)

        steps = [
            "bridge.step1",
            "bridge.step2",
            "bridge.step3",
            "bridge.step4",
            "bridge.step5",
            "bridge.step6",
        ]

        for i, step_key in enumerate(steps, 1):
            lbl = create_normal_label(self.instruction_frame, step_key)
            lbl.pack(anchor="w", pady=2)

        lbl_description = create_normal_label(self.instruction_frame, "bridge.description")
        lbl_description.pack(anchor="s", expand=True, pady=(20, 10))
