from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    waiting_for_message = State()


class AdminStates(StatesGroup):
    broadcast_text       = State()
    broadcast_confirm    = State()
    find_user_input      = State()
    add_balance_id       = State()
    add_balance_amount   = State()
    ban_user_input       = State()
    answer_ticket_id     = State()
    answer_ticket_text   = State()


class TopupStates(StatesGroup):
    custom_amount = State()
