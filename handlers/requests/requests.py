from aiogram import F, Router
from aiogram.enums.chat_action import ChatAction
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionSender

from bitrix_api.bitrix_api import BitrixMethods
from bitrix_api.bitrix_params import update_json
from bot.bot import bot
from constants.buttons_init import (CreatorButtons,
                                    CurrentRequestActionButtons,
                                    RequestButtons)
from database.database import Database
from filters.callback_filters import (BreakTypeCallbackData,
                                      CurrentRequestActionCallbackData,
                                      GetCurrentRequestCallbackData,
                                      RequestActionCallbackData,
                                      RequestNavigationCallbackData,
                                      RequestPageInfoCallbackData,
                                      UserCreatorCallbackData,
                                      ZoneCallbackData)
from filters.message_filters import (IsActive, IsAdmin, IsMainAdmin, IsPhoto,
                                     IsPrivate, IsText, IsTop)
from keyboards.menu import (back_keyboard, cancel_keyboard,
                            create_break_type_menu, create_departments_menu,
                            create_menu_by_position, create_request_menu)
from messages.intro import auth_employee_pos_and_dep_message
from messages.request import (bitrix_creat_deal_error_message,
                              request_action_message,
                              request_break_type_message,
                              request_detailed_desc_message,
                              request_photo_message,
                              request_report_photo_message,
                              request_report_text_message,
                              request_short_desc_message,
                              request_wrong_photo_message,
                              request_wrong_text_message)
from messages.users import choose_department_message
from states.states import CloseRequest, CreatorRequest

router = Router()


@router.callback_query(
        UserCreatorCallbackData.filter(
            F.creator == CreatorButtons.REQUEST),
        IsActive(), or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def choose_request_action(
        query: CallbackQuery, state: FSMContext) -> None:
    current_query_data = query.data.split(':')[-1]
    await query.answer(current_query_data)
    await bot.clear_messages(message=query.message, state=state, finish=False)
    await query.message.answer(
        text=request_action_message(action=current_query_data),
        reply_markup=create_request_menu())


@router.callback_query(
        RequestActionCallbackData.filter(
            F.request == RequestButtons.CREATEREQUEST),
        IsActive(), or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def create_request_action(
        query: CallbackQuery, state: FSMContext) -> None:
    action_sender = ChatActionSender(
        bot=bot,
        chat_id=query.message.from_user.id,
        action=ChatAction.TYPING)
    async with action_sender:
        db = Database()
        current_query_data = query.data.split(':')[-1]
        await query.answer(current_query_data)
        await bot.clear_messages(
            message=query.message, state=state, finish=False)
        await state.set_state(CreatorRequest.start_message)
        await state.update_data(start_message=query.message.message_id + 1)
        await state.update_data(creator_telegram_id=query.from_user.id)
        await state.update_data(status_id=1)
        user_data = await db.get_employee_by_sign(query.from_user.id)
        await query.message.answer(
            text=choose_department_message(),
            reply_markup=create_departments_menu(
                position_id=user_data[4], department_id=user_data[6]))


@router.callback_query(
        ZoneCallbackData.filter(),
        IsActive(), or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def choose_zone_action(
        query: CallbackQuery, state: FSMContext) -> None:
    action_sender = ChatActionSender(
        bot=bot,
        chat_id=query.message.from_user.id,
        action=ChatAction.TYPING)
    async with action_sender:
        current_query_data = query.data.split(':')[-1]
        await query.answer(current_query_data)
        await bot.clear_messages(
            message=query.message, state=state, finish=False)
        await state.update_data(zone=current_query_data)
        data = await state.get_data()
        await state.set_state(CreatorRequest.break_type)
        await query.message.answer(
            text=request_break_type_message(),
            reply_markup=await create_break_type_menu(
                department_id=data['department_id']))


@router.callback_query(
        BreakTypeCallbackData.filter(),
        IsActive(), or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def choose_break_type_action(
        query: CallbackQuery, state: FSMContext) -> None:
    current_query_data = query.data.split(':')[-1]
    await query.answer(current_query_data)
    await bot.clear_messages(message=query.message, state=state, finish=False)
    await state.update_data(break_type=current_query_data)
    await state.set_state(CreatorRequest.creator_photo)
    await query.message.answer(
        text=request_photo_message(),
        reply_markup=back_keyboard)


@router.message(CreatorRequest.creator_photo, IsPhoto(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(creator_photo=message.photo[-1].file_id)
    await bot.clear_messages(message=message, state=state, finish=False)
    await state.set_state(CreatorRequest.short_description)
    await message.answer(
        text=request_short_desc_message(),
        reply_markup=back_keyboard)


@router.message(CreatorRequest.creator_photo, ~IsPhoto(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_wrong_photo(message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer(text=request_wrong_photo_message())


@router.message(CreatorRequest.short_description, IsText(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_request_short_descritpion(
        message: Message, state: FSMContext) -> None:
    await state.update_data(short_description=message.text)
    await bot.clear_messages(message=message, state=state, finish=False)
    await state.set_state(CreatorRequest.detailed_description)
    await message.answer(
        text=request_detailed_desc_message(),
        reply_markup=back_keyboard)


@router.message(CreatorRequest.short_description, ~IsText(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_request_wrong_short_descritpion(
        message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer(text=request_wrong_text_message())


@router.message(CreatorRequest.detailed_description, IsText(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_request_detailed_descritpion(
        message: Message, state: FSMContext) -> None:
    await bot.create_request(message=message, state=state)


@router.message(CreatorRequest.detailed_description, IsText(), IsPrivate(),
                or_f(IsMainAdmin(), IsAdmin(), IsTop()))
async def get_request_wrong_detailed_descritpion(
        message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer(text=request_wrong_text_message())


@router.callback_query(
        RequestActionCallbackData.filter(
            F.request == RequestButtons.MYREQUESTS), IsActive())
async def my_requests_action(
        query: CallbackQuery, state: FSMContext) -> None:
    await bot.open_my_request_list(query=query, page=1)


@router.callback_query(
        RequestActionCallbackData.filter(
            F.request == RequestButtons.REQUESTLIST), IsActive())
async def requests_list_action(
        query: CallbackQuery, state: FSMContext) -> None:
    await bot.open_any_request_list(query=query, page=1)


@router.callback_query(
        RequestPageInfoCallbackData.filter(), IsActive())
async def current_page_info(query: CallbackQuery) -> None:
    page = query.data.split(':')[-1]
    await query.answer(f'Вы на {page} странице')


@router.callback_query(
        RequestNavigationCallbackData.filter(), IsActive())
async def navigate_page(query: CallbackQuery) -> None:
    page = query.data.split(':')[-1]
    if 'ваших' in query.message.text.lower():
        await bot.open_my_request_list(query=query, page=int(page))
        return
    await bot.open_any_request_list(query=query, page=int(page))


@router.callback_query(
        GetCurrentRequestCallbackData.filter(), IsActive())
async def get_current_request(query: CallbackQuery) -> None:
    deal_id, department_id = query.data.split(':')[1:]
    await bot.open_current_request(
        query=query, depatment_id=department_id, deal_id=deal_id)


@router.callback_query(
        CurrentRequestActionCallbackData.filter(
            F.current_act.in_({
                CurrentRequestActionButtons.INROLE,
                CurrentRequestActionButtons.HANDOVERMGR,
                CurrentRequestActionButtons.HANGON})),
        IsActive())
async def action_to_request(query: CallbackQuery) -> None:
    act = query.data.split(':')[-1]
    await query.answer(f'{act}')
    request_data = query.message.caption.split('\n')
    db = Database()
    deal_id = request_data[0].split(':')[-1].strip()
    department_data = await db.get_department(
        department_sign=request_data[2].split(':')[-1].strip())
    department_id = department_data[0]
    if act == CurrentRequestActionButtons.INROLE.value:
        await db.update_executor_in_request(
            executor_telegram_id=query.from_user.id,
            department_id=department_id,
            bitrix_deal_id=deal_id)
        await db.update_status_id_in_request(
            status_id=2,
            department_id=department_id,
            bitrix_deal_id=deal_id)
        await query.message.delete()
        user_data = await db.get_employee_by_sign(query.from_user.id)
        await query.message.answer(
            text=auth_employee_pos_and_dep_message(
                position=user_data[5], department=user_data[7]),
            reply_markup=create_menu_by_position(
                position_id=user_data[4]))
        return
    elif act == CurrentRequestActionButtons.HANDOVERMGR.value:
        bm = await BitrixMethods(
            department_sign=department_id).collect_portal_data()
        json = update_json(
            deal_id=deal_id,
            params={
                'STAGE_ID': f'C{bm.category_id}:{bm.onmgr}',
                'ASSIGNED_BY_ID': bm.mgr_tech
            }
        )
        status = await bm.update_deal(json=json)
        if status != 200:
            await query.message.answer(
                text=bitrix_creat_deal_error_message())
            return
        await db.update_status_id_in_request(
            status_id=3,
            department_id=department_id,
            bitrix_deal_id=deal_id)
    elif act == CurrentRequestActionButtons.HANGON.value:
        bm = await BitrixMethods(
            department_sign=department_id).collect_portal_data()
        json = update_json(
            deal_id=deal_id,
            params={
                'STAGE_ID': f'C{bm.category_id}:{bm.hangon}',
                'ASSIGNED_BY_ID': bm.head_tech
            }
        )
        status = await bm.update_deal(json=json)
        if status != 200:
            await query.message.answer(
                text=bitrix_creat_deal_error_message())
            return
        await db.update_status_id_in_request(
            status_id=4,
            department_id=department_id,
            bitrix_deal_id=deal_id)
    await bot.open_current_request(
        query=query,
        depatment_id=department_id,
        deal_id=deal_id)


@router.callback_query(
        CurrentRequestActionCallbackData.filter(
            F.current_act == CurrentRequestActionButtons.DONE),
        IsActive())
async def action_done_to_request(
        query: CallbackQuery, state: FSMContext) -> None:
    act = query.data.split(':')[-1]
    await query.answer(f'{act}')
    request_data = query.message.caption.split('\n')
    db = Database()
    deal_id = request_data[0].split(':')[-1].strip()
    department_data = await db.get_department(
        department_sign=request_data[2].split(':')[-1].strip())
    department_id = department_data[0]
    await query.message.delete()
    await state.set_state(CloseRequest.start_message)
    await state.update_data(start_message=query.message.message_id + 1)
    await state.update_data(deal_id=deal_id)
    await state.update_data(department_id=department_id)
    await state.update_data(creator_telegram_id=query.from_user.id)
    await state.set_state(CloseRequest.executor_photo)
    await query.message.answer(
        text=request_report_photo_message(),
        reply_markup=cancel_keyboard)


@router.message(CloseRequest.executor_photo, IsPhoto(), IsPrivate())
async def get_report_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(executor_photo=message.photo[-1].file_id)
    await bot.clear_messages(message=message, state=state, finish=False)
    await state.set_state(CloseRequest.report)
    await message.answer(
        text=request_report_text_message(),
        reply_markup=cancel_keyboard)


@router.message(CloseRequest.executor_photo, ~IsPhoto(), IsPrivate())
async def get_report_wrong_photo(message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer(text=request_wrong_photo_message())


@router.message(CloseRequest.report, IsText(), IsPrivate())
async def get_report_text(message: Message, state: FSMContext) -> None:
    await bot.close_request(message=message, state=state)


@router.message(CloseRequest.executor_photo, ~IsText(), IsPrivate())
async def get_report_wrong_text(message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer(text=request_wrong_text_message())
