import os
import omni.ui as ui
from omni.ui import color as cl

ELEM_MARGIN = 4
BORDER_RADIUS = 4
VSPACING = ELEM_MARGIN * 2
RECORDER_BTN_WIDTH = 75
LABEL_WIDTH = 100
BTN_WIDTH = 40
BTN_HEIGHT = 16
WAVEFORM_HEIGHT = 22 * 2 + VSPACING + 10
ERROR_CLR = 0xCC7777FF
WARN_CLR = 0xCC77FFFF
KEYFRAME_CLR = 0xAAAA77FF
IMAGE_SIZE = 25

A2F_SERVER_TYPE = "omniverse:"
EXT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../"))
DATA_PATH = os.path.join(EXT_ROOT, "icons")


PlayBtnStyle = {"image_url": DATA_PATH + "/timeline_play.svg"}
PauseBtnStyle = {"image_url": DATA_PATH + "/timeline_pause.svg"}
ComposeBtnStyle = {"image_url": DATA_PATH + "/timeline_loop.svg"}
LoadingBtnStyle = {"image_url": DATA_PATH + "/loading.gif"}
LocationBtnStyle = {"image_url": DATA_PATH + "/folder.svg"}
AUDIO_FILE_TYPES = [".ufdata"]


StringFieldStyle = {"margin_height": 0, "margin_width": ELEM_MARGIN, "border_radius": BORDER_RADIUS}

ComboBoxStyle = {"border_radius": BORDER_RADIUS + 2}

HandlePlaybackStyle = {"border_radius": 0, "background_color": 0xFFEEEE33}

HandleRecordingStyle = {"border_radius": 0, "background_color": 0xFF3333EE}

HandleStreamingStyle = {"border_radius": 0, "background_color": 0xFF33EE33}

TrackWaveformStyle = {"margin_height": 0, "margin_width": 0, "border_radius": 0}

RangeStartSpacerStyle = {"border_width": 0, "padding": 0, "border_radius": 0, "margin_width": 0}

BigLableStyle = {"font_size": 16, "color": 0xFFFFFFFF}
SmallLableStyle = {"font_size": 14, "color": 0xFF4B4B4B}
ScrollingFrameStyle = {"background_color": 0xFF323232}

MainWindowStyle = {
    "Image::header_frame": {"image_url": DATA_PATH + "/head.png"},
    "Line::group_line": {"color": cl("#4B4B4B"), "margin_height": 0, "padding": 0},
    "Slider::float_slider": {
        "background_color": cl("#FF3300"),
        "secondary_color": cl("#24211F"),
        "border_radius": 3,
        "corner_flag": ui.CornerFlag.ALL,
        "draw_mode": ui.SliderDrawMode.FILLED,
    },
}

PlaybackSliderBackgroundStyle = {
    "background_color": 0xFF24211F,
    "margin_height": 0,
    "margin_width": 0,
    "border_radius": 0,
}

LargeBtnStyle = {
    "border_radius": BORDER_RADIUS,
    "border_width": 0,
    "font_size": 14,
    "padding": ELEM_MARGIN * 2,
    "margin_width": ELEM_MARGIN,
    "margin_height": ELEM_MARGIN,
}

FileBrowseBtnStyle = {
    "image_url": DATA_PATH + "/folder.svg",
    "background_color": 0xFF333333,
    ":hovered": {"background_color": 0xFF9E9E9E},
}

ModalBtnStyle = {
    "border_radius": BORDER_RADIUS,
    "border_width": 0,
    "font_size": 14,
    "padding": ELEM_MARGIN * 2,
    "margin_width": ELEM_MARGIN,
    "margin_height": ELEM_MARGIN,
}

TrashBtnStyle = {
    "image_url": "${glyphs}/trash.svg",
    "background_color": 0xFF333333,
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

TrashDarkBtnStyle = {
    "image_url": "${glyphs}/trash.svg",
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

PlusBtnStyle = {
    "image_url": "${glyphs}/plus.svg",
    "background_color": 0xFF333333,
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

PlusDarkBtnStyle = {
    "image_url": "${glyphs}/plus.svg",
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

PlusDarkExcitedBtnStyle = {
    "image_url": "${glyphs}/plus.svg",
    "color": WARN_CLR,
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

MinusDarkBtnStyle = {
    "image_url": "${omni_audio2face_common_resources}/minus.png",
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

AngleLeftDarkBtnStyle = {
    "image_url": "${glyphs}/angle_left.svg",
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

AngleRightDarkBtnStyle = {
    "image_url": "${glyphs}/angle_right.svg",
    ":hovered": {"background_color": 0xFF9E9E9E},
    ":disabled": {"color": 0x60FFFFFF},
}

FileBrowseBtnStyle = {
    "image_url": "resources/glyphs/folder.svg",
    "background_color": 0xFF333333,
    ":hovered": {"background_color": 0xFF9E9E9E},
}

RangeRectStyle = {
    "background_color": 0x30BBAB58,
    "padding": 0,
    "margin_width": 0,
    "margin_height": 0,
    "border_radius": 0,
    "border_color": 0x70BBAB58,
    "border_width": 1,
}

RangeRectRecordingStyle = {
    "background_color": 0x305858BB,
    "padding": 0,
    "margin_width": 0,
    "margin_height": 0,
    "border_radius": 0,
    "border_color": 0x705858BB,
    "border_width": 1,
}

RangeRectStreamingStyle = {
    "background_color": 0x3058BB58,
    "padding": 0,
    "margin_width": 0,
    "margin_height": 0,
    "border_radius": 0,
    "border_color": 0x7058BB58,
    "border_width": 1,
}
