import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print(f"🧪 Players Helper using MOCK SQLite helper ({getattr(sqllite_helper, '__file__', 'no file')})")
else:
    import sqllite_helper
    print(f"✅ Players Helper using REAL SQLite helper ({getattr(sqllite_helper, '__file__', 'no file')})")

async def add_warmaster(user_id):
    await sqllite_helper.add_warmaster(user_id)
    
async def get_opponents(forUserId: int, callback_data):
    callback_data_arr = callback_data.split(',')
    rule = callback_data_arr[1].split(':')[1]
    weekday = callback_data_arr[0]

    alliance = await sqllite_helper.get_alliance_of_warmaster(forUserId)
    return await sqllite_helper.get_warmasters_opponents(alliance, rule=rule, date=weekday)

async def get_opponents_other_formats(forUserId: int, callback_data):
    callback_data_arr = callback_data.split(',')
    rule = callback_data_arr[1].split(':')[1]
    weekday = callback_data_arr[0]

    alliance = await sqllite_helper.get_alliance_of_warmaster(forUserId)
    return await sqllite_helper.get_other_rule_opponents(alliance, rule=rule, date=weekday)

async def set_name(user_telegram_id, nickname):
    await sqllite_helper.set_nickname(user_telegram_id, nickname)
