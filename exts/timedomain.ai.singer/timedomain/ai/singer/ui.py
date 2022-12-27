import os
import pathlib
import json
import omni.kit.pipapi
from .scripts.ui import BoolSettingWidgetBase, SimpleWidget
from threading import Thread
from .styles import (
    A2F_SERVER_TYPE,
    AUDIO_FILE_TYPES,
    BTN_HEIGHT,
    BTN_WIDTH,
    DATA_PATH,
    EXT_ROOT,
    LABEL_WIDTH,
    WAVEFORM_HEIGHT,
    ComboBoxStyle,
    FileBrowseBtnStyle,
    HandlePlaybackStyle,
    HandleRecordingStyle,
    HandleStreamingStyle,
    BigLableStyle,
    LargeBtnStyle,
    LocationBtnStyle,
    PauseBtnStyle,
    PlayBtnStyle,
    PlaybackSliderBackgroundStyle,
    RangeRectRecordingStyle,
    RangeRectStreamingStyle,
    RangeRectStyle,
    RangeStartSpacerStyle,
    ScrollingFrameStyle,
    SmallLableStyle,
    StringFieldStyle,
    TrackWaveformStyle,
)
from .instance import InstanceManagerBase
import omni.client
import omni.ui as ui
import numpy as np
import scipy.ndimage
os.environ["PATH"] += os.pathsep + os.path.join(EXT_ROOT, "dep/ffmpeg")
omni.kit.pipapi.install("pydub")
omni.kit.pipapi.install("requests")
from pydub import AudioSegment
import requests
from .requestData import GetData


class PathWidgetWithReset(InstanceManagerBase):
    def __init__(self):
        super().__init__()
        self._lbl = None
        self._field_model = None
        self._field = None
        self._browse_btn = None
        self._browse_dialog = None

    def _on_browse_selected(self, filename, dirname):
        if self._field is not None:
            self._settings.set_val(dirname, use_callback=True)
        if self._browse_dialog is not None:
            self._browse_dialog.hide()
        self._field_model.set_value(self._settings.get_val())

    def _on_browse_canceled(self, filename, dirname):
        if self._browse_dialog is not None:
            self._browse_dialog.hide()

    def _on_browse(self):
        if self._browse_dialog is None:
            self._browse_dialog = omni.kit.window.filepicker.FilePickerDialog(
                "Select Audio Directory",
                allow_multi_selection=False,
                apply_button_label="Select",
                click_apply_handler=self._on_browse_selected,
                click_cancel_handler=self._on_browse_canceled,
                current_directory=str(pathlib.Path.home()),
                enable_filename_input=False,
            )
        else:
            self._browse_dialog.show()
        self._browse_dialog.refresh_current_directory()

    def _on_changed(self, val):
        self._settings.set_val(val, use_callback=True)
        self._field_model.set_value(self._settings.get_val())

    def _on_begin_edit(self, *_):
        pass

    def _build_content(self):
        with ui.VStack(height=28):
            ui.Label("Import Your Score", style=BigLableStyle)
            ui.Label("Support format: ufdata", style=SmallLableStyle)
        with ui.HStack(height=20):
            ui.Label("Score Root Path", width=LABEL_WIDTH)
            value = self._settings.get_val()
            self._field_model = StringFieldModel(value, self._on_changed)
            self._field_model.add_begin_edit_fn(self._on_begin_edit)
            self._field_model.set_value(self._settings.get_val())
            self._field = ui.StringField(self._field_model, style=StringFieldStyle)
            self._browse_btn = ui.Button(
                width=BTN_WIDTH, image_height=BTN_HEIGHT, style=FileBrowseBtnStyle, clicked_fn=self._on_browse
            )


class CategoricalSettingWidgetWithReset(InstanceManagerBase):
    def __init__(self):
        super().__init__()
        self._lbl = None
        self._combo_model = None
        self._combo = None
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)
        self._frame = None

    def shutdown(self):
        self._update_sub = None
        self._lbl = None
        if self._combo_model is not None:
            self._combo_model.shutdown()
            self._combo_model = None
        self._combo = None
        super().shutdown()

    def _build_content(self):
        self._frame = ui.HStack(height=20)

        with self._frame:
            self._lbl = ui.Label("Score Name", width=LABEL_WIDTH)
            #     # options: 列表数组
            tracks = self._load_track_list(self.get_abs_track_root_path())
            self._setting.set_options_and_keep(tracks)
            options = self._setting.get_options()
            cur_option = self._setting.get_index()
            self._combo_model = ComboBoxMinimalModel(options, cur_option, self._on_changed)
            if len(self._setting.get_options()) == 0 or self._setting.get_val() is None:
                self._combo = None
                ui.Label("No options")
            else:
                self._combo = ui.ComboBox(self._combo_model, style=ComboBoxStyle)

    def _on_changed(self, val_index):
        self._setting.set_index(val_index)

    def _on_update(self, *_):
        if self.get_abs_track_root_path():
            tracks = self._load_track_list(self.get_abs_track_root_path())
            if tracks != self._setting.get_options():
                self._setting.set_options_and_keep(tracks)
            if self._combo_model is not None:
                if self._setting.get_val() is not None:
                    self._combo_model.set_index(self._setting.get_index())
                if self._combo_model.get_options() != self._setting.get_options():
                    self._refresh()

    def _load_track_list(self, path: str):
        # path = path.replace("\\", "/")
        if not self.is_folder(path):
            print(f"Unable to load list of tracks from {path}")
            return []
        dir_files = self.list_folder(path)
        return [x for x in dir_files if (os.path.splitext(x)[1] in AUDIO_FILE_TYPES)]

    def is_folder(self, path):
        result, entry = omni.client.stat(path)
        # bitewise operation, folder flags is 4
        return entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN

    def list_folder(self, path):
        items = []
        # rstrip() 删除 string 字符串末尾的指定字符，默认为空白符，包括空格、换行符、回车符、制表符。
        # path = path.rstrip("/")
        result, entries = omni.client.list(path)
        if result != omni.client.Result.OK:
            return items
        for en in entries:
            # Skip if it is a folder
            if en.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN:
                continue
            name = en.relative_path
            items.append(name)
        return items

    def is_ov_path(path):
        return A2F_SERVER_TYPE in path

    def get_abs_track_root_path(self):
        """normpath if it is local path
        for ov path not apply normpath
        """
        path = self._setting.get_val()
        # path = self._setting._val
        # if not self.is_ov_path(path):
        #     if not os.path.isabs(path):
        #         path = os.path.abspath(os.path.join(PLAYER_DEPS_ROOT, path))
        #         return os.path.normpath(path).replace("\\", "/")
        return path

    def _changed_fn(self, model):
        index = model.as_int
        self._item_changed(None)
        if not self._from_set_index:
            if self._changed_callback_fn is not None:
                self._changed_callback_fn(index)

    def _build_content_wrapper(self):  # Required for extra UI wrapers in intermediate dervied classes
        self._build_content()

    def _refresh(self):
        if self._frame is not None:
            self._frame.clear()
            with self._frame:
                self._build_content_wrapper()


class StringFieldModel(ui.AbstractValueModel):
    def __init__(self, initial_value, changed_callback_fn=None):
        super().__init__()
        self._value = initial_value
        self._changed_callback_fn = changed_callback_fn
        self.add_end_edit_fn(self._end_edit_fn)

    def shutdown(self):
        self._changed_callback_fn = None

    def get_value(self):
        return self._value

    def get_value_as_string(self):
        return str(self._value)

    def set_value(self, value):
        self._value = value
        self._value_changed()

    def _end_edit_fn(self, model):
        value = model.get_value()
        if self._changed_callback_fn is not None:
            self._changed_callback_fn(value)


class ComboBoxMinimalItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)


class ComboBoxMinimalModel(ui.AbstractItemModel):
    def __init__(self, options, initial_index, changed_callback_fn=None):
        super().__init__()
        self._options = options
        self._changed_callback_fn = changed_callback_fn
        self._items = [ComboBoxMinimalItem(text) for text in self._options]
        self._current_index = ui.SimpleIntModel()
        if initial_index is not None:
            self._current_index.as_int = initial_index
        self._from_set_index = False
        self._current_index.add_value_changed_fn(self._changed_fn)

    def shutdown(self):
        self._changed_callback_fn = None
        self._current_index = None
        self._items = None

    def get_options(self):
        return self._options

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model

    def get_index(self):
        return self._current_index.as_int

    def set_index(self, index):
        if index is not None:
            if index >= 0 and index < len(self._items):
                self._from_set_index = True
                self._current_index.as_int = index
                self._from_set_index = False

    def _changed_fn(self, model):
        index = model.as_int
        self._item_changed(None)
        if not self._from_set_index:
            if self._changed_callback_fn is not None:
                self._changed_callback_fn(index)


class FemaleEntertainerWidger(InstanceManagerBase):
    list_array_name = []
    list_array_id = []
    list_array_float = []
    list_array_avatar = []

    def __init__(self):
        self._btn_create_timedomain_pipeline = None
        self._btn_create_audio_palyer = None
        self._btn_create_a2f_core = None
        self._btn_create_head_template = None
        self._frame = None
        self._female_entertainer_data = None
        self._id = None

    def shutdown(self):
        self._btn_create_timedomain_pipeline = None
        self._btn_create_audio_palyer = None
        self._btn_create_a2f_core = None
        self._btn_create_head_template = None
        self._frame = None
        self._female_entertainer_data = None
        self._id = None

    def _add_menu_item(self, *args, **kwargs):
        editor_menu = omni.kit.ui.get_editor_menu()
        self._menu_items.append(editor_menu.add_item(*args, **kwargs))

    def _build_content(self):
        if self._frame is None:
            self._frame = ui.ScrollingFrame(height=ui.Percent(35), style=ScrollingFrameStyle)
            self._frame.set_build_fn(self._build_fn)
        self._frame.rebuild()

    def _build_fn(self):
        with self._frame:
            with ui.VStack(spacing=5):
                sliders = [self.create_ui_float_slider(i) for i in range(len(FemaleEntertainerWidger.list_array_name))]
                if len(FemaleEntertainerWidger.list_array_name) > 0:
                    for i in range(len(FemaleEntertainerWidger.list_array_name)):
                        with ui.HStack(height=25):
                            IMAGE = FemaleEntertainerWidger.list_array_avatar[i]
                            ui.Image(IMAGE, width=25, height=25)
                            ui.Label(
                                f"{FemaleEntertainerWidger.list_array_name[i]}",
                                width=ui.Percent(8),
                                name="text",
                            )
                            sliders[i]()
                else:
                    ui.Label("No Voiceseed Selected", alignment=ui.Alignment.CENTER)

    def _build_glyph(self):
        self._request_female_entertainer_data()
        with ui.VStack(height=28):
            ui.Label("Choose Your Voice Style (up to 10)", style=BigLableStyle)
            ui.Label("Choose one or more voiceseeds to mix a voice", style=SmallLableStyle)
        with ui.ScrollingFrame(height=ui.Percent(15)):
            with ui.VGrid(column_width=200):
                glyph_plus = ui.get_custom_glyph_code("${glyphs}/plus.svg")
                if isinstance(self._female_entertainer_data["data"], list):
                    functions = [
                        self.create_female_entertainer_clicked(i) for i in range(len(self._female_entertainer_data["data"]))
                    ]

                for index in range(len(self._female_entertainer_data["data"])):
                    _name = self._female_entertainer_data["data"][index]["name_chn"]
                    _tooltip = self._female_entertainer_data["data"][index]["characteristic"]
                    with ui.HStack():
                        ui.Button(
                            f"{_name}  {glyph_plus}",
                            style=LargeBtnStyle,
                            clicked_fn=functions[index],
                            tooltip=_tooltip
                        )

    def _refresh(self):
        if self._frame is not None:
            self._frame.rebuild()

    def _build_content_wrapper(self):  # Required for extra UI wrapers in intermediate dervied classes
        self._build_content()

    def create_ui_float_slider(self, index):
        def set_value(value, index):
            value = round(value, 2)
            FemaleEntertainerWidger.list_array_float[index] = value

        def _delete_avatar():
            del FemaleEntertainerWidger.list_array_name[index]
            del FemaleEntertainerWidger.list_array_id[index]
            del FemaleEntertainerWidger.list_array_avatar[index]
            del FemaleEntertainerWidger.list_array_float[index]
            self._refresh()

        def _click_get_model_value():
            IMAGE_DELETE = DATA_PATH + "/delete.svg"
            slider = ui.FloatSlider(name="float_slider", min=0, max=1).model
            slider.set_value(0.5)
            FemaleEntertainerWidger.list_array_float[index] = 0.5
            slider.add_value_changed_fn(lambda m: set_value(m.get_value_as_float(), index))
            ui.Button(width=25, height=25, image_url=IMAGE_DELETE, clicked_fn=_delete_avatar)

        return _click_get_model_value

    def create_female_entertainer_clicked(self, index):
        name = self._female_entertainer_data["data"][index]["name_chn"]
        id = self._female_entertainer_data["data"][index]["id"]
        avatar = self._female_entertainer_data["data"][index]["avatar"]

        def _on_btn_create_female_entertainer_clicked():
            if name not in FemaleEntertainerWidger.list_array_name:
                FemaleEntertainerWidger.list_array_name.append(name)
                FemaleEntertainerWidger.list_array_id.append(id)
                FemaleEntertainerWidger.list_array_avatar.append(avatar)
                FemaleEntertainerWidger.list_array_float.append([])
                self._refresh()

        return _on_btn_create_female_entertainer_clicked

    def _request_female_entertainer_data(self):
        self._female_entertainer_data = GetData._get_female_entertainer_data()

    def _get_female_data():
        _array = []

        for i in range(len(FemaleEntertainerWidger.list_array_name)):
            _array.append([])
            _array[i] = [FemaleEntertainerWidger.list_array_id[i], FemaleEntertainerWidger.list_array_float[i]]
        return _array


class ScalarSliderModel(ui.AbstractValueModel):
    def __init__(self, initial_value, min_val, max_val, changed_callback_fn=None, fast_change=True):
        super().__init__()
        self._value = initial_value
        self._min_val = min_val
        self._max_val = max_val
        self._changed_callback_fn = changed_callback_fn
        self._fast_change = fast_change
        if not self._fast_change:
            self.add_end_edit_fn(self._end_edit_fn)

    def shutdown(self):
        self._changed_callback_fn = None

    def get_value(self):
        return self._value

    def get_min(self):
        return self._min_val

    def get_max(self):
        return self._max_val

    def get_value_as_int(self):
        return int(self._value)

    def get_value_as_float(self):
        return float(self._value)

    def set_value(self, value):
        self._value = value
        self._value_changed()
        if self._fast_change and self._changed_callback_fn is not None:
            self._changed_callback_fn(self._value)

    def set_field(self, value):
        if value is not None:
            self._value = value
            self._value_changed()

    def _end_edit_fn(self, model):
        value = model.get_value()
        if self._changed_callback_fn is not None:
            self._changed_callback_fn(value)


class WaveformWidget(SimpleWidget):
    def __init__(self, height):
        super().__init__()
        self._height = height
        self._waveform_image_provider = None
        self._waveform_image = None
        self._canvas = None
        self._canvas_width = 1024
        self._canvas_height = WAVEFORM_HEIGHT

    def shutdown(self):
        self._waveform_image_provider = None
        self._waveform_image = None
        self._canvas = None
        super().shutdown()

    def update_track_waveform(self, track):
        num_samples = track.get_num_samples()
        width, height = self._canvas_width, self._canvas_height
        ex_factor = 1
        width_ex = width * ex_factor
        shrink_factor = max(num_samples // width_ex, 1)
        if 0:
            volume = np.abs(track.data[::shrink_factor][:width_ex])
        else:
            if num_samples >= shrink_factor * width_ex:
                volume = track.data[: shrink_factor * width_ex].reshape(width_ex, shrink_factor)
            else:
                tmp = np.zeros((shrink_factor * width_ex), np.float32)
                tmp[:num_samples] = track.data
                volume = tmp.reshape(width_ex, shrink_factor)
            volume = np.abs(np.max(volume, axis=1))
        # volume /= max(np.max(volume), 1e-8)
        # dB logarithmic scale
        if 0:
            volume = np.maximum(volume, 1e-6)
            volume = 20.0 * np.log10(volume / 1.0)
            #  [-50, 0] dB
            volume = np.maximum((volume / 50.0) + 1.0, 0.0)
            volume *= 0.7
        canvas = np.zeros((height, width_ex, 4), dtype=np.uint8)
        print("canvas.shape[1]======>", canvas.shape[1])
        for x in range(canvas.shape[1]):
            start = int(round((1.0 - volume[x]) * float(height) / 2))
            end = int(round((1.0 + volume[x]) * float(height) / 2))
            canvas[start:end, x, :] = [255, 255, 255, 130]
            if start == end:
                canvas[start: end + 1, x, :] = [255, 255, 255, 60]
        if ex_factor > 1:
            canvas = scipy.ndimage.zoom(canvas.astype(np.float32), (1, 1.0 / ex_factor, 1), order=1).astype(np.uint8)
        self._canvas = canvas.flatten().tolist()
        if self._waveform_image_provider is not None:
            self._waveform_image_provider.set_bytes_data(self._canvas, [self._canvas_width, self._canvas_height])

    def _build_content(self):
        self._waveform_image_provider = ui.ByteImageProvider()
        if self._canvas is not None:
            self._waveform_image_provider.set_bytes_data(self._canvas, [self._canvas_width, self._canvas_height])
        with ui.HStack():
            self._waveform_image = ui.ImageWithProvider(
                self._waveform_image_provider,
                height=self._height,
                style=TrackWaveformStyle,
                fill_policy=ui.IwpFillPolicy.IWP_STRETCH,
            )


class TimelineRangeWidget(InstanceManagerBase):
    def __init__(self, height):
        super().__init__()
        self._height = height
        self._rect_range_start = None
        self._rect_range = None

    def shutdown(self):
        self._rect_range_start = None
        self._rect_range = None
        super().shutdown()

    def set_rect_style(self, style):
        if self._rect_range is not None:
            self._rect_range.set_style(style)

    def update_range_rect(self, range_start, range_end, track_len):
        if self._rect_range_start is not None and self._rect_range is not None:
            if track_len == 0:
                start_perc = 0
                rect_perc = 0
            else:
                start_perc = range_start / track_len * 100.0
                rect_perc = (range_end - range_start) / track_len * 100.0
            self._rect_range_start.width = ui.Percent(start_perc)
            self._rect_range.width = ui.Percent(rect_perc)

    def _build_content(self):
        with ui.HStack(height=self._height):
            self._rect_range_start = ui.Spacer(width=omni.ui.Percent(0), style=RangeStartSpacerStyle)
            self._rect_range = ui.Rectangle(width=omni.ui.Percent(100), height=self._height, style=RangeRectStyle)


class PlaybackSliderWidget(SimpleWidget):
    def __init__(self, height, on_changed_fn=None, on_changed_from_mouse_fn=None):
        super().__init__()
        self._height = height
        self._on_changed_fn = on_changed_fn
        self._on_changed_from_mouse_fn = on_changed_from_mouse_fn
        self._max_value = 0.001
        self._value = 0.0
        self._handle_width = 1
        self._pressed = False
        self._mouse_catcher = None
        self._slider_placer = None
        self._handle = None
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)

    def shutdown(self):
        self._update_sub = None
        self._on_changed_fn = None
        self._on_changed_from_mouse_fn = None
        self._max_value = 0.001
        self._value = 0.0
        self._pressed = False
        self._mouse_catcher = None
        self._slider_placer = None
        self._handle = None
        super().shutdown()

    def set_value(self, value):
        if self._pressed:
            return  # pressed mouse overrides external change of the value
        self._value = value
        if self._value < 0.0:
            self._value = 0.0
        elif self._value > self._max_value:
            self._value = self._max_value
        if self._on_changed_fn is not None:
            self._on_changed_fn(self._value)
        if self._max_value > 0:
            rel_x_perc = self._value / self._max_value
            self._set_slider_position(rel_x_perc)
        elif self._max_value == 0:
            self._set_slider_position(0)

    def get_value(self):
        return self._value

    def set_max(self, max_value):
        if max_value < 0:
            raise ValueError("Playback Slider max value can't be less than zero")
        self._max_value = max_value if max_value > 0 else 0.001

    def set_handle_style(self, style):
        if self._handle is not None:
            self._handle.set_style(style)

    def _set_slider_position(self, rel_x_perc):
        if self._slider_placer is not None:
            self._slider_placer.offset_x = ui.Percent(rel_x_perc * 100.0)

    def _on_mouse_moved(self, x, y, _, btn):
        if btn is True:
            self._update_from_mouse(x)

    def _on_mouse_pressed(self, x, y, btn, *args):
        if btn == 0:
            self._pressed = True
            self._update_from_mouse(x)

    def _on_mouse_released(self, x, y, btn, *args):
        if btn == 0:
            self._pressed = False

    def _update_from_mouse(self, x):
        if self._mouse_catcher is not None and self._slider_placer is not None:
            rel_x = x - self._mouse_catcher.screen_position_x
            if rel_x < 0:
                rel_x = 0
            elif rel_x >= self._mouse_catcher.computed_width:
                rel_x = self._mouse_catcher.computed_width
            rel_x_perc = rel_x / self._mouse_catcher.computed_width
            self._set_slider_position(rel_x_perc)
            self._value = self._max_value * rel_x_perc
            if self._on_changed_fn is not None:
                self._on_changed_fn(self._value)

    def _build_content(self):
        with ui.ZStack():
            self._mouse_catcher = ui.Rectangle(
                height=self._height,
                style={
                    "background_color": 0x0,
                    "padding": 0,
                    "margin_width": 0,
                    "margin_height": 0,
                    "border_radius": 0,
                    "border_color": 0x0,
                    "border_width": 0,
                },
                mouse_moved_fn=self._on_mouse_moved,
                mouse_pressed_fn=self._on_mouse_pressed,
                mouse_released_fn=self._on_mouse_released,
            )
            with ui.HStack():
                self._slider_placer = ui.Placer(draggable=False, stable_size=True)
                with self._slider_placer:
                    with ui.HStack():
                        self._handle = ui.Rectangle(
                            width=self._handle_width, height=self._height, style=HandlePlaybackStyle
                        )
                        ui.Spacer()

    def _on_update(self, *_):
        if self._pressed:
            if self._on_changed_from_mouse_fn is not None:
                self._on_changed_from_mouse_fn(self._value)


class TimelineWidget(BoolSettingWidgetBase):
    _frame = None

    def __init__(self):
        super().__init__()
        self._waveform_widget = WaveformWidget(height=WAVEFORM_HEIGHT)
        self._timeline_range_widget = TimelineRangeWidget(height=WAVEFORM_HEIGHT)
        self._playback_slider_widget = PlaybackSliderWidget(
            height=WAVEFORM_HEIGHT, on_changed_fn=None, on_changed_from_mouse_fn=self._on_changed
        )
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)

    def shutdown(self):
        self._update_sub = None
        self._waveform_widget.shutdown()
        self._waveform_widget = None
        self._timeline_range_widget.shutdown()
        self._timeline_range_widget = None
        self._playback_slider_widget.shutdown()
        self._playback_slider_widget = None
        # super().shutdown()

    def set_style(self, style):
        if style == "regular":
            self._playback_slider_widget.set_handle_style(HandlePlaybackStyle)
            self._timeline_range_widget.set_rect_style(RangeRectStyle)
        elif style == "streaming":
            self._playback_slider_widget.set_handle_style(HandleStreamingStyle)
            self._timeline_range_widget.set_rect_style(RangeRectStreamingStyle)
        elif style == "recording":
            self._playback_slider_widget.set_handle_style(HandleRecordingStyle)
            self._timeline_range_widget.set_rect_style(RangeRectRecordingStyle)

    def update_track_waveform(self):
        track = self._audio_player.get_track_ref()
        self._waveform_widget.update_track_waveform(track)

    def _build_content(self):
        TimelineWidget._frame = ui.ZStack()
        with TimelineWidget._frame:
            ui.Rectangle(style=PlaybackSliderBackgroundStyle)
            self._waveform_widget._build_content()
            self._timeline_range_widget._build_content()
            self._playback_slider_widget._build_content()

    def _refresh(self):
        if TimelineWidget._frame is not None:
            TimelineWidget._frame.clear()
            with TimelineWidget._frame:
                self._build_content_wrapper()

    def _build_content_wrapper(self):  # Required for extra UI wrapers in intermediate dervied classes
        self._build_content()

    def _on_changed(self, t):
        if self._track is not None:
            track_len = self._track.get_length()
            self._playback_slider_widget.set_max(track_len)
            self._playback_slider_widget.set_value(t)
            seek_sample = self._track.sec_to_sample(t)
            self._audio_player.seek(seek_sample)

    def _on_update(self, *_):
        if self._track is not None and self._audio_player is not None:
            self._pressed = False
            track_len = self._track.get_length()
            self._playback_slider_widget.set_max(track_len)
            t = self._audio_player.get_current_time()
            self._playback_slider_widget.set_value(t)
            # if t == track_len and not self.boolSetting._state:
            #     self.boolSetting._state = True
                # self._on_toggled()


class TimecodeWidget(BoolSettingWidgetBase):
    def __init__(self):
        super().__init__()
        self.ts = None
        self._timecode_lbl = None
        self._timecode_tms_lbl = None
        self._timecode_max_lbl = None
        self._timecode_max_tms_lbl = None
        self._button_play_pause = ButtonPlayPause()
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)

    def shutdown(self):
        self.ts = None
        self._update_sub = None
        self._timecode_lbl = None
        self._timecode_tms_lbl = None
        self._timecode_max_lbl = None
        self._timecode_max_tms_lbl = None
        # super().shutdown()

    def _build_content(self):
        with ui.HStack(height=22, style={"margin_width": 0}):
            ui.Spacer()
            self._timecode_lbl = ui.Label("0:00", width=0)
            self._timecode_tms_lbl = ui.Label(".00", width=0, style={"color": 0x50FFFFFF})
            ui.Label("  |  ", style={"color": 0x70FFFFFF})
            self._timecode_max_lbl = ui.Label("0:00", width=0)
            self._timecode_max_tms_lbl = ui.Label(".00", width=0, style={"color": 0x50FFFFFF})
            ui.Spacer()

    def _set_timecode(self, t, m_sec_lbl, tms_lbl):
        tmss = int(round(t * 100))
        secs = tmss // 100
        mins = secs // 60
        secs_sub = secs % 60
        tmss_sub = tmss % 100
        m_sec_lbl.text = "{}:{:02d}".format(mins, secs_sub)
        tms_lbl.text = ".{:02d}".format(tmss_sub)
        if self.ts is not None and t == self.ts:
            self._button_play_pause._update_from_state(is_playing=False)
        else:
            self.ts = t

    def _on_update(self, *_):
        if self._timecode_lbl is not None and self._timecode_tms_lbl is not None:
            t = self._audio_player.get_current_time()
            self._set_timecode(t, self._timecode_lbl, self._timecode_tms_lbl)
        if self._timecode_max_lbl is not None and self._timecode_max_tms_lbl is not None and self._track is not None:
            track_len = self._track.get_length()
            self._set_timecode(track_len, self._timecode_max_lbl, self._timecode_max_tms_lbl)


class ButtonPlayPause(BoolSettingWidgetBase):
    _btn = None

    def __init__(self):
        super().__init__()

    def shutdown(self):
        ButtonPlayPause._btn = None
        super().shutdown()

    def _build_widget(self):
        with ui.HStack(width=BTN_WIDTH, height=30):
            ButtonPlayPause._btn = ui.Button(width=BTN_WIDTH, style=PlayBtnStyle, tooltip="Play/Pause (P)")
            ButtonPlayPause._btn.set_clicked_fn(self._on_toggled)

    def _update_from_state(self, is_playing):
        if ButtonPlayPause._btn is not None:
            if is_playing is True:
                ButtonPlayPause._btn.set_style(PauseBtnStyle)
            else:
                ButtonPlayPause._btn.set_style(PlayBtnStyle)


class ButtonComposing(BoolSettingWidgetBase):
    def __init__(self):
        super().__init__()
        self._btn = None
        self._compose_data = None
        self._timeline_widget = TimelineWidget()

    def shutdown(self):
        self._btn = None
        super().shutdown()

    def _build_widget(self):
        with ui.VStack():
            self._btn = ui.Button('Synthesis your song', height=BTN_HEIGHT*2.5, tooltip="Synthesized Voice")
            self._btn.set_clicked_fn(self._on_compound)

    def _on_compound(self):
        thread = Thread(target=self._request_compose_data)
        thread.start()

    def _update_from_state(self, is_looping):
        if self._btn is not None:
            self._btn.selected = is_looping

    def _request_compose_data(self):
        _array = FemaleEntertainerWidger._get_female_data()
        path = os.path.join(self.boolSetting._val, self.boolSetting._filename)
        files = {"file": open(path, "rb")}
        mix_str = json.dumps(
            {
                "duration": _array,
                "pitch": _array,
                "air": _array,
                "falsetto": _array,
                "tension": _array,
                "energy": _array,
                "mel": _array,
            },
        )
        data_dict = {"flag": 135, "is_male": 1, "mix_info": mix_str}
        try:
            self._btn.text = 'processing...'
            res = GetData._get_compose_data(files, data_dict)
            if res["code"] == 200:
                r = requests.get(res["data"][-1]["audio"], stream=True)
                if not os.path.exists(os.path.join(EXT_ROOT, "voice")):
                    os.makedirs(os.path.join(EXT_ROOT, "voice"))
                memory_address_ogg = os.path.join(EXT_ROOT, "voice\\voice.ogg")
                memory_address_wav = os.path.join(EXT_ROOT, "voice\\voice.wav")
                with open(memory_address_ogg, "wb") as ace_music:
                    for chunk in r.iter_content(chunk_size=1024):  # 1024 bytes
                        if chunk:
                            ace_music.write(chunk)
                song = AudioSegment.from_ogg(memory_address_ogg)
                song.export(memory_address_wav, format="wav")
                self._load_track(memory_address_wav)
                self._timeline_widget.update_track_waveform()
                self._timeline_widget._refresh()
            else:
                print(res)
        except BaseException as e:
            print(e)
        self._btn.text = 'Synthesis your song'
        self._btn.set_style({})


class ButtonLocation(BoolSettingWidgetBase):
    def __init__(self):
        self._btn = None

    def shutdown(self):
        self._btn = None
        super().shutdown()

    def _build_widget(self):
        with ui.HStack(width=BTN_WIDTH, height=30):
            self._btn = ui.Button(width=BTN_WIDTH, style=LocationBtnStyle, tooltip="Locate the composite file")
            self._btn.set_clicked_fn(self.get_location)

    def get_location(self):
        # memory_address为需要打开文件夹的路径
        if not os.path.exists(os.path.join(EXT_ROOT, "voice")):
            os.makedirs(os.path.join(EXT_ROOT, "voice"))
        memory_address = os.path.join(EXT_ROOT, "voice")
        os.startfile(memory_address)

    def _update_from_state(self, recorder_enabled):
        if self._btn is not None:
            self._btn.selected = recorder_enabled
