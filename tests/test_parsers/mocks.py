from playwright.async_api import TimeoutError

# Мок элемента страницы
class MockElement:
    def __init__(self, text: str, is_visible_value: bool = True):
        self.text = text
        self.is_visible_value = is_visible_value

    async def text_content(self) -> str:
        return self.text

    async def is_visible(self) -> bool:
        return self.is_visible_value

# Мок страницы
class MockPage:
    def __init__(self, selectors_data):
        self.selectors_data = selectors_data
        self.mock_elements = []

    async def wait_for_selector(self, selector, timeout=2000):
        if selector in self.selectors_data:
            return MockElement(self.selectors_data[selector])
        raise TimeoutError("Timeout waiting for selector")  

    async def query_selector_all(self, selector):
        if selector == 'h1, h2, h3':
            return [MockElement(text) for text in self.selectors_data.get('headers', [])]
        elif selector.startswith('xpath'):
            return [MockElement(self.selectors_data.get('xpath', []), self.selectors_data.get('is_visible', True))]
        return []