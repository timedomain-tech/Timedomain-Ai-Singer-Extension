from timedomain.ai.singer.instance import InstanceManagerBase
from timedomain.ai.singer.utils_io import read_file

import omni.ui as ui
import omni.kit.ui
import omni.kit.app
import omni.kit.window.filepicker
import omni.kit.pipapi

a2f_audio = omni.audio2face.player_deps.import_a2f_audio()


class Refreshable:
    def __init__(self):
        self.__need_refresh = False
        self.__update_sub = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.__on_update)
        )

    def shutdown(self):
        self.__update_sub = None

    def refresh(self):
        # We can't call self._refresh() directly, since it will clear the UI
        # while the caller of this function could be that UI too
        self.__need_refresh = True

    def __on_update(self, *_):
        if self.__need_refresh:
            self.__need_refresh = False
            self._refresh()

    def _refresh(self):  # Should be implemented in the derived class
        raise NotImplementedError


class SimpleWidget(Refreshable):
    def __init__(self):
        super().__init__()
        self._frame = None

    def shutdown(self):
        self._frame = None
        super().shutdown()

    def build(self):
        self._frame = ui.VStack(height=0, spacing=0)
        with self._frame:
            self._build_content_wrapper()

    def show(self):
        if self._frame is not None:
            self._frame.visible = True

    def hide(self):
        if self._frame is not None:
            self._frame.visible = False

    def enable(self):
        if self._frame is not None:
            self._frame.enabled = True

    def disable(self):
        if self._frame is not None:
            self._frame.enabled = False

    def clear(self):
        if self._frame is not None:
            self._frame.clear()

    def _refresh(self):
        if self._frame is not None:
            self._frame.clear()
            with self._frame:
                self._build_content_wrapper()

    def _build_content_wrapper(self):  # Required for extra UI wrapers in intermediate dervied classes
        self._build_content()

    def _build_content(self):  # Should be implemented in the derived class
        raise NotImplementedError


class BoolSettingWidgetBase(InstanceManagerBase):
    _track = None
    _audio_player = a2f_audio.AudioPlayer(verbose=True)

    def __init__(self):
        super().__init__()
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)

    def shutdown(self):
        self._update_sub = None
        BoolSettingWidgetBase._audio_player.pause()
        BoolSettingWidgetBase._audio_player = None
        super().shutdown()

    def _build_content(self):
        self._build_widget()
        if self.boolSetting._state is not None:
            self._update_from_state(self.boolSetting._state)

    def _on_toggled(self):
        self.boolSetting._state = not self.boolSetting._state
        if self.boolSetting._state:
            if self.boolSetting._val is not None and self.boolSetting._filename is not None:
                BoolSettingWidgetBase._audio_player.play()
                self._update_from_state(True)
                self.boolSetting._state = True
            else:
                self._update_from_state(False)
                BoolSettingWidgetBase._audio_player.pause()
                self.boolSetting._state = False
        else:
            self._update_from_state(False)
            BoolSettingWidgetBase._audio_player.pause()

    def _load_track(self, track_fpath):
        bytes_data = read_file(track_fpath)
        track = a2f_audio.read_track_from_bytes(bytes_data)
        BoolSettingWidgetBase._track = track
        BoolSettingWidgetBase._audio_player.set_track(track)

    def _on_update(self, *_):
        if self.boolSetting._state:
            self.boolSetting.toggle()

    def _build_widget(self):  # Should be implemented in the derived class
        raise NotImplementedError

    def _update_from_state(self):  # Should be implemented in the derived class
        raise NotImplementedError