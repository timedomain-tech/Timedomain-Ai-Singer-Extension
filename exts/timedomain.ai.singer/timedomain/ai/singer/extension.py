from .styles import VSPACING, BigLableStyle, MainWindowStyle
from .ui import (
    WAVEFORM_HEIGHT,
    ButtonComposing,
    ButtonLocation,
    ButtonPlayPause,
    CategoricalSettingWidgetWithReset,
    PathWidgetWithReset,
    FemaleEntertainerWidger,
    TimecodeWidget,
    TimelineWidget,
)
import omni.ext
import omni.ui as ui
import omni.client


class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[timedomain.ai.singer] MyExtension startup")

        self._window = ui.Window("TIMEDOMAIN AI SINGER", width=840, height=650)
        self._window.frame.set_build_fn(self.show_window)
        self._window.frame.style = MainWindowStyle

    def on_shutdown(self):
        print("[timedomain.ai.singer] MyExtension shutdown")
        self._root_path_widget = None
        self._track_widget = None
        self._range_widget = None
        self.frame = None
        self._btn_loop = None
        self._timecode_widget.shutdown()
        self._timecode_widget = None
        self._btn_play.shutdown()
        self._btn_play = None
        self._timeline_widget.shutdown()
        self._timeline_widget = None
        self._btn_recorder = None
        if self._window:
            self._window.destroy()
            self._window = None

    def show_window(self):
        with self._window.frame:
            with ui.VStack(spacing=10):
                self._root_path_widget = PathWidgetWithReset()
                self._root_path_widget._build_content()
                self._track_widget = CategoricalSettingWidgetWithReset()
                self._track_widget._build_content()
                with ui.VStack(height=5):
                    ui.Line(name="group_line", alignment=ui.Alignment.CENTER)
                self.frame = FemaleEntertainerWidger()
                self.frame._build_glyph()
                with ui.HStack(height=0):
                    ui.Line(name="group_line", alignment=ui.Alignment.CENTER)
                with ui.VStack(height=20):
                    ui.Label("Mix Your Voice Style", style=BigLableStyle)
                self.frame._build_content()
                self._btn_loop = ButtonComposing()
                self._btn_loop._build_widget()
                with ui.HStack(height=WAVEFORM_HEIGHT):
                    self._timeline_widget = TimelineWidget()
                    self._timeline_widget._build_content()
                    ui.Spacer(width=4)
                    with ui.VStack(spacing=VSPACING, width=0):
                        self._timecode_widget = TimecodeWidget()
                        self._timecode_widget._build_content()
                        with ui.HStack():
                            self._btn_play = ButtonPlayPause()
                            self._btn_play._build_content()
                            self._btn_recorder = ButtonLocation()
                            self._btn_recorder._build_widget()
