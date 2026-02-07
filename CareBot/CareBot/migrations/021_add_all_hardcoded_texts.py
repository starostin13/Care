"""
Migration 021: Add all hardcoded text messages to database for localization
This migration adds all missing text keys from handlers.py, keyboard_constructor.py, 
and mission_message_builder.py to enable multi-language support.
"""
from yoyo import step

def add_all_hardcoded_texts(conn):
    cursor = conn.cursor()
    
    # All text entries to add to the database
    texts = [
        # Error messages from handlers.py
        ("error_invalid_request", "ru", "❌ Ошибка: неверный формат запроса. Пожалуйста, попробуйте снова."),
        ("error_invalid_request", "en", "❌ Error: Invalid request format. Please try again."),
        
        ("error_mission_info_failed", "ru", "❌ Ошибка: не удалось получить информацию о миссии. Пожалуйста, попробуйте снова."),
        ("error_mission_info_failed", "en", "❌ Error: Failed to get mission information. Please try again."),
        
        ("error_no_opponent", "ru", "Ошибка: не удалось найти противника для битвы"),
        ("error_no_opponent", "en", "Error: Failed to find opponent for battle"),
        
        ("error_battle_creation", "ru", "Ошибка при создании битвы: {error}"),
        ("error_battle_creation", "en", "Error creating battle: {error}"),
        
        ("error_defender_notification", "ru", "Ошибка при отправке сообщения дефендеру {defender_id}: {error}"),
        ("error_defender_notification", "en", "Error sending message to defender {defender_id}: {error}"),
        
        ("error_mission_not_found", "ru", "Не удалось определить миссию."),
        ("error_mission_not_found", "en", "Failed to determine mission."),
        
        ("error_no_active_battle", "ru", "Не найден активный бой для этой миссии."),
        ("error_no_active_battle", "en", "No active battle found for this mission."),
        
        ("error_result_application", "ru", "❌ Ошибка при применении результата: {error}"),
        ("error_result_application", "en", "❌ Error applying result: {error}"),
        
        ("error_no_admin_rights", "ru", "❌ У вас нет прав администратора"),
        ("error_no_admin_rights", "en", "❌ You don't have administrator rights"),
        
        # Mission flow messages
        ("btn_back_to_missions", "ru", "⬅️ Назад к миссиям"),
        ("btn_back_to_missions", "en", "⬅️ Back to Missions"),
        
        ("mission_score_instructions", "ru", "Что бы укзать результат игры 'ответьте' на это сообщение указав счёт в формате [ваши очки] [очки оппонента], например:\n20 0"),
        ("mission_score_instructions", "en", "To submit the game result, 'reply' to this message with the score in format [your points] [opponent points], for example:\n20 0"),
        
        ("new_mission_prefix", "ru", "Новая миссия:"),
        ("new_mission_prefix", "en", "New Mission:"),
        
        ("no_signups_today", "ru", "Ещё никто не запился на этот день"),
        ("no_signups_today", "en", "No one has signed up for this day yet"),
        
        ("error_score_format", "ru", "❌ Неверный формат. Используйте формат: [ваши очки] [очки оппонента]"),
        ("error_score_format", "en", "❌ Invalid format. Use format: [your points] [opponent points]"),
        
        # Result confirmation messages
        ("result_pending_confirmation", "ru", "⏳ Результат ожидает подтверждения вторым игроком или администратором.\n\nВаш счёт: {my_score}\nСчёт оппонента: {opponent_score}"),
        ("result_pending_confirmation", "en", "⏳ Result awaiting confirmation from second player or administrator.\n\nYour score: {my_score}\nOpponent score: {opponent_score}"),
        
        ("error_not_participant", "ru", "❌ Вы не являетесь участником этой миссии."),
        ("error_not_participant", "en", "❌ You are not a participant of this mission."),
        
        ("error_already_submitted", "ru", "❌ Вы уже отправили результат для этой миссии. Ожидается подтверждение."),
        ("error_already_submitted", "en", "❌ You already submitted a result for this mission. Awaiting confirmation."),
        
        ("error_no_permission_confirm", "ru", "❌ У вас нет прав подтверждать этот результат."),
        ("error_no_permission_confirm", "en", "❌ You don't have permission to confirm this result."),
        
        ("result_confirm_question", "ru", "Подтвердить результат?\n\n{winner_text}\n\nСчёт: {my_score} - {opponent_score}"),
        ("result_confirm_question", "en", "Confirm result?\n\n{winner_text}\n\nScore: {my_score} - {opponent_score}"),
        
        ("btn_confirm", "ru", "✅ Подтвердить"),
        ("btn_confirm", "en", "✅ Confirm"),
        
        ("btn_reject", "ru", "❌ Отменить"),
        ("btn_reject", "en", "❌ Cancel"),
        
        ("result_confirmed", "ru", "✅ Результат подтверждён!\n\nСчёт: {my_score} - {opponent_score}"),
        ("result_confirmed", "en", "✅ Result confirmed!\n\nScore: {my_score} - {opponent_score}"),
        
        ("result_confirmed_notification", "ru", "✅ Ваш результат для миссии #{mission_id} подтверждён игроком {confirmer_name}.\n\nСчёт: {fst_score} - {snd_score}"),
        ("result_confirmed_notification", "en", "✅ Your result for mission #{mission_id} has been confirmed by player {confirmer_name}.\n\nScore: {fst_score} - {snd_score}"),
        
        ("error_pending_not_found", "ru", "❌ Ожидающий результат не найден."),
        ("error_pending_not_found", "en", "❌ Pending result not found."),
        
        ("error_cancellation_fetch", "ru", "❌ Ошибка при получении данных для отмены: {error}"),
        ("error_cancellation_fetch", "en", "❌ Error fetching cancellation data: {error}"),
        
        ("error_not_submitter", "ru", "❌ Только игрок, отправивший результат, может его отменить."),
        ("error_not_submitter", "en", "❌ Only the player who submitted the result can cancel it."),
        
        ("error_cancellation_failed", "ru", "❌ Ошибка при отмене результата: {error}"),
        ("error_cancellation_failed", "en", "❌ Error cancelling result: {error}"),
        
        ("result_cancelled", "ru", "✅ Результат отменён. Вы можете отправить новый результат."),
        ("result_cancelled", "en", "✅ Result cancelled. You can submit a new result."),
        
        ("result_cancelled_notification", "ru", "ℹ️ Игрок {submitter_name} отменил свой результат для миссии #{mission_id}. Вы можете отправить новый результат."),
        ("result_cancelled_notification", "en", "ℹ️ Player {submitter_name} cancelled their result for mission #{mission_id}. You can submit a new result."),
        
        # Name input
        ("prompt_enter_name", "ru", "⚠️ Просто напишите ваше имя следующим сообщением"),
        ("prompt_enter_name", "en", "⚠️ Just type your name in the next message"),
        
        # Admin messages
        ("admin_no_pending_missions", "ru", "✅ Нет миссий ожидающих подтверждения."),
        ("admin_no_pending_missions", "en", "✅ No missions awaiting confirmation."),
        
        ("admin_pending_missions_title", "ru", "⏳ Миссии ожидающие подтверждения ({count}):\n\nВыберите миссию для подтверждения результата:"),
        ("admin_pending_missions_title", "en", "⏳ Missions awaiting confirmation ({count}):\n\nSelect a mission to confirm result:"),
        
        ("btn_back", "ru", "« Назад"),
        ("btn_back", "en", "« Back"),
        
        ("btn_back_admin_menu", "ru", "« Назад в админ меню"),
        ("btn_back_admin_menu", "en", "« Back to Admin Menu"),
        
        ("admin_mission_details", "ru", "📋 Миссия #{mission_id}\n📅 Создана: {created_date}\n📜 Правила: {rules}\n\n👥 Участники:\n{participants}\n\n📝 Результат введён: {submitter}\nСчёт: {fst_score} - {snd_score}\n\n{winner_text}"),
        ("admin_mission_details", "en", "📋 Mission #{mission_id}\n📅 Created: {created_date}\n📜 Rules: {rules}\n\n👥 Participants:\n{participants}\n\n📝 Result submitted by: {submitter}\nScore: {fst_score} - {snd_score}\n\n{winner_text}"),
        
        ("admin_winner_text", "ru", "🏆 Победитель: {winner}"),
        ("admin_winner_text", "en", "🏆 Winner: {winner}"),
        
        ("admin_draw_text", "ru", "🤝 Ничья"),
        ("admin_draw_text", "en", "🤝 Draw"),
        
        ("admin_confirm_question", "ru", "Подтвердить результат?"),
        ("admin_confirm_question", "en", "Confirm result?"),
        
        ("admin_result_confirmed", "ru", "✅ Результат подтверждён администратором"),
        ("admin_result_confirmed", "en", "✅ Result confirmed by administrator"),
        
        ("admin_confirmed_notification", "ru", "Администратор подтвердил результат миссии #{mission_id}.\nСчёт: {fst_score} - {snd_score}"),
        ("admin_confirmed_notification", "en", "Administrator confirmed result of mission #{mission_id}.\nScore: {fst_score} - {snd_score}"),
        
        ("admin_result_rejected", "ru", "❌ Результат отклонён администратором"),
        ("admin_result_rejected", "en", "❌ Result rejected by administrator"),
        
        ("admin_rejected_notification", "ru", "Администратор отклонил результат миссии #{mission_id}. Пожалуйста, введите корректный результат."),
        ("admin_rejected_notification", "en", "Administrator rejected result of mission #{mission_id}. Please submit correct result."),
        
        # Days of week for keyboard_constructor.py
        ("day_monday_short", "ru", "Пн"),
        ("day_monday_short", "en", "Mon"),
        
        ("day_tuesday_short", "ru", "Вт"),
        ("day_tuesday_short", "en", "Tue"),
        
        ("day_wednesday_short", "ru", "Ср"),
        ("day_wednesday_short", "en", "Wed"),
        
        ("day_thursday_short", "ru", "Чт"),
        ("day_thursday_short", "en", "Thu"),
        
        ("day_friday_short", "ru", "Пт"),
        ("day_friday_short", "en", "Fri"),
        
        ("day_saturday_short", "ru", "Сб"),
        ("day_saturday_short", "en", "Sat"),
        
        ("day_sunday_short", "ru", "Вс"),
        ("day_sunday_short", "en", "Sun"),
        
        # Language button
        ("btn_language_russian", "ru", "🇷🇺 Русский"),
        ("btn_language_russian", "en", "🇷🇺 Russian"),
        
        # Alliance display format
        ("alliance_player_count", "ru", "{alliance_name} ({player_count} игроков)"),
        ("alliance_player_count", "en", "{alliance_name} ({player_count} players)"),
        
        ("admin_pending_count", "ru", "⏳ Подтверждение миссий ({pending_count})"),
        ("admin_pending_count", "en", "⏳ Confirm Missions ({pending_count})"),
        
        # Mission bonus messages from mission_message_builder.py
        ("mission_double_xp_bonus", "ru", "⚔️ {opponent_name} является членом доминирующего альянса! За убийство их юнитов вы получаете опыт в 2 раза быстрее!"),
        ("mission_double_xp_bonus", "en", "⚔️ {opponent_name} is a member of the dominant alliance! You gain experience twice as fast for killing their units!"),
        
        ("mission_double_xp_bonus_generic", "ru", "⚔️ Ваш оппонент является членом доминирующего альянса! За убийство их юнитов вы получаете опыт в 2 раза быстрее!"),
        ("mission_double_xp_bonus_generic", "en", "⚔️ Your opponent is a member of the dominant alliance! You gain experience twice as fast for killing their units!"),
        
        # Winner display texts
        ("winner_text", "ru", "Победитель: {winner} ({my_score}:{opponent_score})"),
        ("winner_text", "en", "Winner: {winner} ({my_score}:{opponent_score})"),
        
        ("draw_text", "ru", "Ничья ({my_score}:{opponent_score})"),
        ("draw_text", "en", "Draw ({my_score}:{opponent_score})"),
        
        # Cancel result messages
        ("error_cancel_not_found", "ru", "❌ Ошибка: результат не найден или уже обработан."),
        ("error_cancel_not_found", "en", "❌ Error: Result not found or already processed."),
        
        ("error_cannot_cancel_own", "ru", "❌ Вы не можете отменить свой собственный результат. Попросите противника сделать это."),
        ("error_cannot_cancel_own", "en", "❌ You cannot cancel your own result. Ask your opponent to do it."),
        
        ("result_cancelled_success", "ru", "❌ Результат отменён.\nВы можете ввести новый результат."),
        ("result_cancelled_success", "en", "❌ Result cancelled.\nYou can submit a new result."),
        
        ("result_cancelled_by_opponent", "ru", "❌ Ваш результат для миссии #{mission_id} был отменён игроком {canceler_name}. Вы можете ввести новый результат."),
        ("result_cancelled_by_opponent", "en", "❌ Your result for mission #{mission_id} was cancelled by player {canceler_name}. You can submit a new result."),
        
        # Admin confirmation messages
        ("admin_battle_not_found", "ru", "❌ Не найден бой для миссии #{mission_id}"),
        ("admin_battle_not_found", "en", "❌ Battle not found for mission #{mission_id}"),
        
        ("admin_pending_not_found", "ru", "❌ Не найден ожидающий результат для миссии #{mission_id}"),
        ("admin_pending_not_found", "en", "❌ Pending result not found for mission #{mission_id}"),
        
        ("admin_participants_label", "ru", "👥 Участники:"),
        ("admin_participants_label", "en", "👥 Participants:"),
        
        ("admin_result_submitted_label", "ru", "📝 Результат введён:"),
        ("admin_result_submitted_label", "en", "📝 Result submitted by:"),
        
        ("admin_confirm_result_success", "ru", "✅ Результат миссии #{mission_id} подтверждён!\nСчёт: {fst_score}:{snd_score}"),
        ("admin_confirm_result_success", "en", "✅ Mission #{mission_id} result confirmed!\nScore: {fst_score}:{snd_score}"),
        
        ("admin_confirmed_by_admin", "ru", "✅ Администратор подтвердил результат миссии #{mission_id}\nСчёт: {fst_score}:{snd_score}"),
        ("admin_confirmed_by_admin", "en", "✅ Administrator confirmed result of mission #{mission_id}\nScore: {fst_score}:{snd_score}"),
        
        ("admin_reject_result_success", "ru", "❌ Результат миссии #{mission_id} отклонён.\nПожалуйста, введите корректный результат."),
        ("admin_reject_result_success", "en", "❌ Mission #{mission_id} result rejected.\nPlease submit correct result."),
        
        ("admin_rejected_by_admin", "ru", "❌ Администратор отклонил результат миссии #{mission_id}\nПожалуйста, введите корректный результат."),
        ("admin_rejected_by_admin", "en", "❌ Administrator rejected result of mission #{mission_id}\nPlease submit correct result."),
        
        ("error_confirm_failed", "ru", "❌ Ошибка при подтверждении: {error}"),
        ("error_confirm_failed", "en", "❌ Error confirming: {error}"),
        
        ("error_reject_failed", "ru", "❌ Ошибка при отклонении: {error}"),
        ("error_reject_failed", "en", "❌ Error rejecting: {error}"),
    ]
    
    for key, language, text in texts:
        cursor.execute('''
            INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)
        ''', (key, language, text))
        print(f"✅ Added/updated text: {key} ({language})")
    
    print(f"✅ Successfully added {len(texts)} text entries")

steps = [step(add_all_hardcoded_texts)]
