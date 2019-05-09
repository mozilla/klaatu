from selenium.webdriver.common.by import By


class ToolBar:
    """Representation of the firefox toolbar"""

    _extension_locator = (By.TAG_NAME, "toolbarbutton")

    def __init__(self, selenium):
        self.selenium = selenium

    @property
    def toolbar_items(self):
        """Tool bar items"""
        with self.selenium.context(self.selenium.CONTEXT_CHROME):
            els = self.selenium.find_elements(*self._extension_locator)
            return [self.Extension(el, self.selenium) for el in els]

    class Extension:
        def __init__(self, root, selenium):
            self.root = root
            self.selenium = selenium

        @property
        def _id(self):
            """Extension name."""
            with self.selenium.context(self.selenium.CONTEXT_CHROME):
                return self.root.get_attribute("data-extensionid")
