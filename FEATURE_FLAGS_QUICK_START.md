# Feature Flags Quick Start

## Для администраторов (For Administrators)

### Как включить/выключить фичи (How to toggle features)

1. Откройте бота и перейдите в главное меню
2. Нажмите кнопку "🔧 Админ панель" (Admin Menu)
3. Выберите "⚙️ Управление фичами" (Feature Flags)
4. Нажмите на нужную фичу для переключения

### Доступные фичи (Available Features)

#### 💎 Общие ресурсы альянсов (Alliance Common Resources)
- **Включено:** Альянсы получают и теряют ресурсы в битвах
- **Выключено:** Все механики ресурсов отключены, битвы проходят без изменения ресурсов

### Интерфейс (Interface)

```
⚙️ Управление фичами

Включите или выключите функции системы:

💎 Общие ресурсы альянсов: ✅ Включено

[Нажмите на фичу чтобы переключить]

« Назад
```

### Что происходит при изменении (What happens when toggling)

- Изменения вступают в силу немедленно
- Все новые битвы учитывают новое состояние
- Активные битвы продолжают использовать старую логику

## For Developers

### Current Feature Flags

| Flag Name | Default | Description |
|-----------|---------|-------------|
| `common_resource` | Enabled | Controls alliance resource gain/loss mechanics |

### API Usage

```python
import feature_flags_helper

# Check if feature is enabled
if await feature_flags_helper.is_feature_enabled('common_resource'):
    # Feature-specific code
    pass

# Toggle feature programmatically
new_state = await feature_flags_helper.toggle_feature_flag('common_resource')

# Get all features
flags = await feature_flags_helper.get_all_feature_flags()
for flag_name, enabled, description in flags:
    print(f"{flag_name}: {'ON' if enabled else 'OFF'}")
```

### Adding New Features

See `FEATURE_FLAGS_IMPLEMENTATION.md` for detailed instructions.

## Security Summary

✅ All feature flag operations require admin privileges
✅ Feature flags are persisted in the database
✅ No SQL injection vulnerabilities detected
✅ Fail-safe design: unknown flags default to enabled
✅ No breaking changes to existing functionality
