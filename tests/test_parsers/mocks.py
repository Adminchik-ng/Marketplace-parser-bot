from tkinter import N, NO
from playwright.async_api import TimeoutError

# Мок элемента страницы
class MockElement:
    def __init__(self, text: str, is_visible_value: bool = True):
        self.text = text
        self.is_visible_value = is_visible_value

    async def text_content(self) -> str:
        return self.text
    
    async def inner_text(self) -> str:
        return self.text

    async def is_visible(self) -> bool:
        return self.is_visible_value

# Мок страницы
class MockPage:
    def __init__(self, selectors_data):
        self.selectors_data = selectors_data

    async def wait_for_selector(self, selector, timeout=2000):
        if selector in self.selectors_data:
            return MockElement(self.selectors_data[selector])
        raise TimeoutError("Timeout waiting for selector")  

    async def query_selector(self, selector):
        if selector in self.selectors_data:
            return MockElement(self.selectors_data[selector])
        return None

    async def query_selector_all(self, selector):
        if selector == 'h1, h2, h3':
            return [MockElement(text) for text in self.selectors_data.get('headers', [])]
        elif selector in ['span', 'div', 'p', 'strong', 'b']:
            return [MockElement(text) for text in self.selectors_data.get('сontainers', [])]
        elif selector.startswith('xpath'):
            return [MockElement(self.selectors_data.get('xpath', ''), self.selectors_data.get('is_visible', True))]
        return []
 
    
class MockPageOzon:
    def __init__(self, selectors_data):
        self.selectors_data = selectors_data

    async def query_selector(self, selector):
        if selector in self.selectors_data.keys():
            return self.selectors_data[selector]
        return None
    
    async def query_selector_all(self, selector):
        if selector.startswith('xpath'):
            visibles = self.selectors_data.get('is_visible', None)
            elements = self.selectors_data.get('xpath', None)
            if visibles and elements:
                return [MockElement(elem, visible) for elem, visible in zip(elements, visibles)]
        return []

    
class MockElementForLocator:
    def __init__(self, data):
        self.text = data.get("text", "")
        self.cls = data.get("class", "")
        self.tag = data.get("tag", "")

    async def inner_text(self):
        return self.text

    async def get_attribute(self, attr_name):
        if attr_name == "class":
            return self.cls
        return None

    async def evaluate(self, js_code):
        if js_code == "(el) => el.tagName.toLowerCase()":
            return self.tag
        return None


class MockLocator:
    def __init__(self, elements_data):
        self.elements_data = elements_data

    async def count(self):
        return len(self.elements_data)

    def nth(self, index):
        return MockElementForLocator(self.elements_data[index])


class MockPageWithLocator:
    def __init__(self, elements_data):
        self.elements_data = elements_data

    def locator(self, selector):
        return MockLocator(self.elements_data)