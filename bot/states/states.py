from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    marketplace = State()    # Состояние выбора маркетплейса
    product_url = State()    # Ввод ссылки
    target_price = State()   # Ввод целевой цены

class RemoveProductStates(StatesGroup):
    choosing_product = State()