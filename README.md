# grankin_logic

Фиды и план запуска поисковых товарных кампаний Яндекс Директа для novostroyka-pro.ru (Ризалта Резорт, ЛОК Вера, Палаццо де Агой).

- Фид для загрузки в Директ: [`feeds/estate_start_feed.yml`](feeds/estate_start_feed.yml)
- Минус-фразы: [`feeds/minus_words.txt`](feeds/minus_words.txt)
- План запуска: [`docs/launch.md`](docs/launch.md)
- Запуск донора по шагам: [`docs/launch_steps.md`](docs/launch_steps.md)
- Правила Директа для фидов: [`docs/direct_feed_rules.md`](docs/direct_feed_rules.md)
- Логика: [`docs/method.md`](docs/method.md)

## Как изменить фид

1. Правим `data/feed.json`.
2. Собираем и проверяем:

```bash
python3 scripts/build_feed.py
```

3. Загружаем `feeds/estate_start_feed.yml` в Директ.
