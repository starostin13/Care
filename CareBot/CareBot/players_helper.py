from sqllite_helper import get_alliance_of_warmaster, get_warmasters_opponents
import sqllite_helper

async def add_warmaster(user_id):
    sqllite_helper.add_warmaster(user_id)
    
async def get_opponents(forUserId: int, callback_data):
    callback_data_arr = callback_data.split(',')
    rule = callback_data_arr[1].split(':')[1]
    weekday = callback_data_arr[0]
    alliance = await get_alliance_of_warmaster(forUserId)
    return await get_warmasters_opponents(alliance, rule=rule, date=weekday)

async def set_name(user_telegram_id, nickname):
    sqllite_helper.set_nickname(user_telegram_id, nickname)