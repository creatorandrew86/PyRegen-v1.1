import dearpygui.dearpygui as dpg
import core.constants as ct

import ui.dynamic as dynamic
import ui.layout as layout
import ui.themes as themes


def run_interface(on_generate_nozzle: callable, on_solve: callable, state: dict):
    dpg.create_context()

    with dpg.font_registry():
        if ct.FONT_PATH.exists():
            default_font = dpg.add_font(str(ct.FONT_PATH), 16)
            dpg.bind_font(default_font)

    themes.build_themes()
    layout.build_interface(on_generate_nozzle, on_solve, state)

    dpg.create_viewport(title="PyRegen v1.1")
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dynamic.center_viewport_on_screen()
    dpg.set_viewport_resize_callback(dynamic.resize_main_window, user_data=state)
    dynamic.resize_main_window(user_data=state)
    dpg.set_primary_window("main_window", False)

    dpg.start_dearpygui()
    dpg.destroy_context()