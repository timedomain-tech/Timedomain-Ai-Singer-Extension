from typing import TypeVar
from pxr import Sdf

SettingType = TypeVar("SettingType", bound="SettingItem")


class SettingItem:

    _val = None
    _filename = None
    _state = None
    _mix_info = {
        "duration": [],
        "pitch": [],
        "air": [],
        "falsetto": [],
        "tension": [],
        "energy": [],
        "mel": [],
    }

    def __init__(self, name):
        self._name = name
        self._init_fn = None
        self._changed_fn = None
        self._prim = None
        self._default_val = None
        self._org_default_val = None
        self._initialized = False

    def shutdown(self):
        self._prim = None

    def init(self, default_val=None, init_fn=None, changed_fn=None, prim=None):
        self._init_fn = init_fn
        self._changed_fn = changed_fn
        self._prim = prim
        self._default_val = self._check(default_val)
        self._org_default_val = self._default_val
        SettingItem._val = self._default_val  # Required if set_val(val) will fail
        if self._prim is not None and self._prim.HasAttribute(self.get_usd_attr_name()):
            val = self._prim.GetAttribute(self.get_usd_attr_name()).Get()
        else:
            val = self._default_val
        self.set_val(val, use_callback=True, use_init_fn=True)
        self._initialized = True

    def initialized(self):
        return self._initialized

    def get_name(self):
        return self._name

    def get_ui_name(self):
        return self._name.replace("_", " ").title()

    def get_usd_attr_name(self):
        return f"state:setting_{self._name}"

    def get_val(self):
        if SettingItem._filename is not None:
            SettingItem._state = False
        return SettingItem._val

    def get_default(self):
        return self._default_val

    def is_default(self):
        return SettingItem._val == self._default_val

    def set_val(self, val, use_callback=True, use_init_fn=False):
        # val_checked = self._check(val)
        # callback_fn = self._init_fn if use_init_fn else self._changed_fn
        # val_prev = SettingItem._val
        SettingItem._val = val
        # if use_callback and callback_fn is not None:
        #     try:
        #         callback_fn(val_checked)
        #     except Exception as e:
        #         SettingItem._val = val_prev
        #         print(e)
        #         raise
        # self._update_usd_prim_attr()

    def set_default(self, default_val):
        self._default_val = self._check(default_val)

    def reset_default(self):
        self._default_val = self._get_safe_default()

    def reset(self):
        self.set_val(self._default_val, use_callback=True, use_init_fn=False)

    def get_usd_type(self):
        raise NotImplementedError

    def get_arr_usd_type(self):
        raise NotImplementedError  # Should be implemented in derived class

    def to_arr_usd_data(self, arr):
        raise NotImplementedError  # Should be implemented in derived class

    def from_arr_usd_data(self, arr, arr_len):
        raise NotImplementedError  # Should be implemented in derived class

    def interpolate(self, val1, val2, alpha):
        raise NotImplementedError  # Should be implemented in derived class

    def _update_usd_prim_attr(self):
        if self._prim is not None and self._prim.IsValid():
            if SettingItem._val is not None:
                self._prim.CreateAttribute(self.get_usd_attr_name(), self.get_usd_type()).Set(SettingItem._val)

    def _check(self, val):
        return val


class CategoricalSetting(SettingItem):
    def __init__(self, name, options=[], value=None):
        self.options = options
        self._value = value
        super().__init__(name)

    def init(self, default_val, init_fn, changed_fn, prim):
        super().init(default_val, init_fn, changed_fn, prim)

    def get_options(self):
        if len(self._options) > 0:
            SettingItem._filename = self._options[0]
        return self._options

    def set_options_and_keep(self, options):
        self._options = options
        # if SettingItem._val not in self._options:
        #     # log_warn(
        #     #     f"Setting [{self.get_name()}]: Old value [{self._val}]
        #     #     is not in the new list [{self._options}], resetting to default"
        #     # )
        #     self.reset_default()
        #     self.reset()

    def set_options_and_reset(self, options):
        self._options = options
        self.reset_default()
        self.reset()

    def set_value(self, val):
        self._value = val
        SettingItem._filename = val
        SettingItem._state = False

    def get_value(self):
        return self._value

    def set_options_and_val(self, options, val):
        self._options = options
        self.reset_default()
        self.set_value(val, use_callback=True, use_init_fn=False)

    def get_index(self):
        if self._value is not None:
            BoolSetting._filename = self._value
            return self._options.index(self._value)
        else:
            return None

    def set_index(self, val_index):
        val = self._options[val_index]
        self.set_value(val)

    def get_usd_type(self):
        return Sdf.ValueTypeNames.String

    def get_arr_usd_type(self):
        return Sdf.ValueTypeNames.StringArray

    def to_arr_usd_data(self, arr):
        return list(arr)

    def from_arr_usd_data(self, arr, arr_len):
        return list(arr)

    def interpolate(self, val1, val2, alpha):
        return val1

    def _get_safe_default(self):
        if len(self._options) > 0:
            return self._options[0]
        else:
            return None

    def _check(self, val):
        if val is None:
            return self._get_safe_default()
        if val not in self._options:
            raise AttributeError(
                f"Setting [{self.get_name()}]: value '{val}' is not in the list of options {self._options}"
            )
        return val


class BoolSetting(SettingItem):
    def __init__(self, name):
        super().__init__(name)

    def init(self, default_val, init_fn, changed_fn, prim):
        super().init(default_val, init_fn, changed_fn, prim)

    def get_usd_type(self):
        return Sdf.ValueTypeNames.Bool

    def get_arr_usd_type(self):
        return Sdf.ValueTypeNames.BoolArray

    def to_arr_usd_data(self, arr):
        return list(arr)

    def from_arr_usd_data(self, arr, arr_len):
        return list(arr)

    def interpolate(self, val1, val2, alpha):
        return val1

    def toggle(self, use_callback=True):
        pass

    def get_state(self):
        return SettingItem._state

    def _get_safe_default(self):
        return False

    def _check(self, val):
        if val is None:
            return self._get_safe_default()
        return bool(val)
