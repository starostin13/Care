# Care
bot for caring wh40k crusadess deals

## 🚀 Быстрое развертывание

### WSL2 Deployment (РЕКОМЕНДУЕТСЯ - January 2026)

Новый способ деплоя через WSL2 + Docker на локальной машине:

- **⚡ Быстрый старт:** [WSL2_QUICKSTART.md](WSL2_QUICKSTART.md)
- **📖 Полная документация:** [WSL2_DEPLOYMENT.md](WSL2_DEPLOYMENT.md)
- **🤖 Для AI агентов:** [agents.md](agents.md) - см. секцию "WSL2 + Docker деплой"
- **🔧 Основной скрипт:** `scripts\wsl2-deploy.ps1`

```powershell
# Полный цикл деплоя (build → test → deploy)
.\scripts\wsl2-deploy.ps1 full

# Или поэтапно:
.\scripts\wsl2-deploy.ps1 build     # Сборка образа в WSL2
.\scripts\wsl2-deploy.ps1 inspect   # Проверка содержимого
.\scripts\wsl2-deploy.ps1 test      # Локальное тестирование
.\scripts\wsl2-deploy.ps1 deploy    # Деплой на production
```

### Legacy Deployment (УСТАРЕЛ)

- **📖 Документация:** [DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)
- **⚡ Скрипт:** `scripts\update-production.ps1`

```powershell
# Legacy способ (собирает образ на production)
.\scripts\update-production.ps1 update
```

## 📊 Рабочие сервисы

После развертывания доступны:
- **CareBot API:** http://192.168.0.125:5555
- **SQLite Web UI:** http://192.168.0.125:8080
- **Health Check:** http://192.168.0.125:5555/health
