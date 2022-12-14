from .settings import BoolSetting, CategoricalSetting, SettingItem


class InstanceManagerBase:
    def __init__(self):
        self._settings = SettingItem("ace")
        self._setting = CategoricalSetting("ace")
        self.boolSetting = BoolSetting("ace")

    def shutdown(self):
        self._settings = None
        self._setting = None
        self.boolSetting = None