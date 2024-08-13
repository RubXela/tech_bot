from aiogram.fsm.state import State, StatesGroup


class AuthStart(StatesGroup):
    start_message = State()
    phone_number = State()


class CreatorRequest(StatesGroup):
    start_message = State()
    creator_telegram_id = State()
    status_id = State()
    department_id = State()
    zone = State()
    break_type = State()
    creator_photo = State()
    short_description = State()
    detailed_description = State()
    bitrix_deal_id = State()


class CloseRequest(StatesGroup):
    start_message = State()
    deal_id = State()
    department_id = State()
    executor_telegram_id = State()
    executor_photo = State()
    report = State()


class RequestChange(StatesGroup):
    start_message = State()
    short_description = State()
    detailed_description = State()


class ActionsToEmployee(StatesGroup):
    start_message = State()
    action = State()
    phone = State()
    department_id = State()
    position_id = State()
