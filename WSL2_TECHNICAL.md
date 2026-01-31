# WSL2 Technical Details

## Технические детали интеграции WSL2 + Docker

### Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│ Windows Host (PowerShell)                                   │
│  ├─ VS Code                                                 │
│  ├─ Git Repository: c:\Users\staro\Projects\Care           │
│  └─ Scripts: scripts\wsl2-deploy.ps1                       │
└────────────────────┬────────────────────────────────────────┘
                     │ wsl -d Ubuntu-22.04
┌────────────────────▼────────────────────────────────────────┐
│ WSL2 Ubuntu 22.04                                           │
│  ├─ Project Path: /mnt/c/Users/staro/Projects/Care        │
│  ├─ Docker Engine                                           │
│  └─ Docker Images: carebot:latest                          │
└────────────────────┬────────────────────────────────────────┘
                     │ docker save/load
┌────────────────────▼────────────────────────────────────────┐
│ Production Server (ubuntu@192.168.1.125)                   │
│  ├─ Path: /home/ubuntu/carebot-production/                │
│  ├─ Docker Compose                                         │
│  └─ Container: carebot_production                          │
└─────────────────────────────────────────────────────────────┘
```

### Компоненты системы

#### 1. Windows Host

**Роль:** Среда разработки и оркестрация  
**Компоненты:**
- VS Code для редактирования кода
- PowerShell для запуска скриптов
- Git для версионирования
- SSH клиент для связи с production

**Основной скрипт:** `scripts\wsl2-deploy.ps1`

#### 2. WSL2 (Ubuntu 22.04)

**Роль:** Сборка Docker образов  
**Компоненты:**
- Docker Engine (v28.5.1+)
- Docker Compose (v2.40.0+)
- Build кеш Docker слоев

**Путь к проекту:** `/mnt/c/Users/staro/Projects/Care`

**Преимущества:**
- Нативная производительность Linux
- Полная совместимость с Docker
- Локальный кеш сборки
- Быстрый доступ к Windows файлам через /mnt/

#### 3. Production Server

**Роль:** Хостинг production приложения  
**Компоненты:**
- Docker Engine
- Docker Compose
- Volumes для данных и миграций

**Путь:** `/home/ubuntu/carebot-production/`

### Процесс сборки образа

```bash
# Команда в PowerShell
.\scripts\wsl2-deploy.ps1 build

# Что происходит:
# 1. PowerShell вызывает WSL2
wsl -d Ubuntu-22.04 -e bash -c "cd /mnt/c/Users/staro/Projects/Care && sudo docker build ..."

# 2. Docker в WSL2 собирает образ
# - Читает Dockerfile.production
# - Использует локальный кеш слоев
# - Создает образ carebot:latest
# - Сохраняет в WSL2 Docker registry

# 3. Результат доступен в WSL2
sudo docker images carebot
```

### Трансфер образа на production

```
┌──────────────┐    docker save    ┌─────────────┐    scp    ┌────────────────┐
│ WSL2 Docker  │ ────────────────> │  .tar file  │ ────────> │ Production     │
│ carebot:     │                   │  (temp)     │           │ Server         │
│ latest       │                   └─────────────┘           │                │
└──────────────┘                                             │ docker load    │
                                                              │    ↓           │
                                                              │ carebot:latest │
                                                              └────────────────┘
```

### Пути в разных средах

| Среда | Путь к проекту | Формат |
|-------|----------------|--------|
| Windows | `c:\Users\staro\Projects\Care` | Windows path |
| WSL2 | `/mnt/c/Users/staro/Projects/Care` | Unix path |
| Production | `/home/ubuntu/carebot-production` | Unix path |

### Конвертация путей в скрипте

```powershell
# В wsl2-deploy.ps1
$PROJECT_PATH_WIN = Get-Location  # c:\Users\staro\Projects\Care
$PROJECT_PATH_WSL = $PROJECT_PATH_WIN.Path `
    -replace '\\', '/' `          # Замена \ на /
    -replace 'C:', '/mnt/c' `     # C: -> /mnt/c
    -replace 'c:', '/mnt/c'       # c: -> /mnt/c
# Результат: /mnt/c/Users/staro/Projects/Care
```

### Volumes и persistent данные

```yaml
# docker-compose.production.yml
volumes:
  - ./data:/app/data                    # База данных
  - ./migrations:/app/CareBot/migrations # Миграции
```

**Почему НЕ в образе:**
- База данных: должна сохраняться между обновлениями
- Миграции: можно обновлять без пересборки образа

### Команды Docker в разных средах

#### Локально в WSL2

```bash
# Прямой вызов
wsl -d Ubuntu-22.04
sudo docker images
sudo docker run --rm carebot:latest ls /app

# Из PowerShell
wsl -d Ubuntu-22.04 -e bash -c "sudo docker images"
```

#### На production

```bash
# Через SSH
ssh ubuntu@192.168.1.125 "docker images"

# С docker compose
ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production && docker compose ps"
```

### Безопасность и изоляция

#### Test контейнер (локальный)

- **Порт:** 5556 (не конфликтует с production)
- **Данные:** test-data/ (отдельная папка)
- **Токен:** Из .env файла
- **Цель:** Тестирование образа перед деплоем

#### Production контейнер

- **Порт:** 5555
- **Данные:** /home/ubuntu/carebot-production/data/
- **Токен:** Из .env на production
- **Цель:** Production сервис

### Производительность

#### Время сборки

| Операция | Legacy (remote) | WSL2 (local) |
|----------|----------------|--------------|
| Первая сборка | ~3-5 мин | ~2-3 мин ✅ |
| Повторная (с кешем) | ~2-3 мин | ~30-60 сек ✅ |
| Трансфер | N/A | ~1-2 мин |
| **Итого** | ~3-5 мин | ~2-4 мин ✅ |

#### Размер образа

```bash
# Проверка размера
wsl -d Ubuntu-22.04 -e bash -c "sudo docker images carebot"

# Типичный размер
REPOSITORY   TAG      SIZE
carebot      latest   ~250-300MB
```

### Диагностика

#### Проверка WSL2

```powershell
# Версия WSL
wsl --version

# Статус
wsl --status

# Список дистрибутивов
wsl -l -v

# Вход в WSL2
wsl -d Ubuntu-22.04
```

#### Проверка Docker в WSL2

```bash
# Из WSL2
docker --version
docker compose version
sudo service docker status

# Из PowerShell
wsl -d Ubuntu-22.04 -e bash -c "docker --version"
wsl -d Ubuntu-22.04 -e bash -c "sudo service docker status"
```

#### Проверка образа

```powershell
# Что попало в образ
.\scripts\wsl2-deploy.ps1 inspect

# Проверка конкретного файла
wsl -d Ubuntu-22.04 -e bash -c "sudo docker run --rm carebot:latest cat /app/CareBot/handlers.py | head"

# Размер образа и слоев
wsl -d Ubuntu-22.04 -e bash -c "sudo docker history carebot:latest"
```

### Автозапуск Docker в WSL2

```bash
# /etc/wsl.conf
[boot]
command = "service docker start"

# Применить (из PowerShell)
wsl --shutdown
```

### Интеграция с VS Code

VS Code может использовать WSL2 для разработки:

```json
// .vscode/settings.json
{
    "remote.WSL.useShellEnvironment": true
}
```

**Расширения:**
- Remote - WSL
- Docker (работает с WSL2 Docker)

### Troubleshooting

#### Docker не запускается в WSL2

```bash
sudo service docker start
sudo service docker status

# Если не помогает
sudo apt remove docker.io
sudo apt install docker.io
```

#### WSL2 не видит изменения файлов

```powershell
# Перезапустить WSL
wsl --shutdown
wsl -d Ubuntu-22.04

# Проверить доступ к файлам
wsl -d Ubuntu-22.04 -e bash -c "ls /mnt/c/Users/staro/Projects/Care"
```

#### Образ не собирается

```bash
# Очистить кеш
wsl -d Ubuntu-22.04 -e bash -c "sudo docker system prune -a"

# Сборка без кеша
.\scripts\wsl2-deploy.ps1 build -NoCache
```

#### Permission denied в WSL2

```bash
# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться
exit
wsl -d Ubuntu-22.04
```

### Best Practices

1. **Регулярная очистка:** `.\scripts\wsl2-deploy.ps1 cleanup`
2. **Проверка образа:** Всегда `inspect` перед `deploy`
3. **Локальное тестирование:** Используйте `test` для новых фич
4. **Версионирование:** Используйте `-Tag` для версий
5. **Бэкапы:** Автоматические при `deploy`, ручные через `backup`

### Миграция с legacy

```powershell
# 1. Финальный бэкап старым способом
.\scripts\update-production.ps1 backup

# 2. Первый деплой через WSL2
.\scripts\wsl2-deploy.ps1 full

# 3. Проверка
.\scripts\wsl2-deploy.ps1 status
curl http://192.168.1.125:5555/health
```

### Мониторинг

```powershell
# Health check
.\scripts\wsl2-deploy.ps1 status

# Логи
.\scripts\wsl2-deploy.ps1 logs

# Метрики образа
wsl -d Ubuntu-22.04 -e bash -c "sudo docker stats --no-stream carebot_production"
```

---

**Версии:**
- WSL2: 2.0+
- Ubuntu: 22.04 LTS
- Docker: 28.5.1+
- Docker Compose: 2.40.0+

**Дата:** January 31, 2026
