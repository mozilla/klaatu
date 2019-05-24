import typing

from selenium.webdriver.common.by import By

Locator = typing.Tuple[typing.Any, str]


class ToolBar:
    """Representation of the firefox toolbar"""

    _extension_locator: Locator = (By.TAG_NAME, "toolbarbutton")

    def __init__(self, selenium: typing.Any) -> None:
        self.selenium = selenium

    @property
    def toolbar_items(self) -> typing.List:
        """Tool bar items"""
        with self.selenium.context(self.selenium.CONTEXT_CHROME):
            els = self.selenium.find_elements(*self._extension_locator)
            return [self.Extension(el, self.selenium) for el in els]

    class Extension:
        def __init__(self, root: typing.Any, selenium: typing.Any) -> None:
            self.root = root
            self.selenium = selenium

        @property
        def _id(self) -> str:
            """Extension name."""
            with self.selenium.context(self.selenium.CONTEXT_CHROME):
                return f'{self.root.get_attribute("data-extensionid")}'
        
        @property
        def widget_id(self) -> str:
            with self.selenium.context(self.selenium.CONTEXT_CHROME):
                return f'{self.root.get_attribute("widget-id")}"'
