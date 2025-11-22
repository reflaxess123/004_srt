# Whisper Fast Large v3 - YouTube Shorts Transcriber

Скрипт для автоматической пакетной транскрибации видео и аудио с помощью Whisper Fast (large v3) для YouTube Shorts с поддержкой DaVinci Resolve.

## Особенности

- **Пакетная обработка** - автоматически обрабатывает все файлы из папки `in`
- **Умный пропуск** - не обрабатывает заново уже транскрибированные файлы
- **Whisper Fast large v3** - быстрая и точная транскрибация
- **Поддержка аудио и видео** - MP4, MOV, AVI, WAV, MP3, M4A и многие другие форматы
- **Оптимизация для вертикального видео** - максимум 10 символов на строку субтитров (настраивается)
- **Совместимость с DaVinci Resolve** - формат SRT полностью совместим для импорта
- **Сохранение пауз** - все паузы сохраняются для корректной работы с "Remove Silence" в DaVinci
- **Поддержка слов-уровня timestamps** - точная синхронизация с речью

## Установка

```bash
# Установить зависимости через uv
uv sync
```

## Требования

- Python 3.10+
- FFmpeg (должен быть установлен в системе)
- CUDA (опционально, для GPU ускорения)

## Использование

### Базовое использование (РЕКОМЕНДУЕТСЯ)

1. Положите все ваши видео/аудио файлы в папку `in/`
2. Запустите скрипт:

```bash
# Обработать все файлы из папки in/ → результаты в out/
uv run python transcribe.py

# Или через bat файл (Windows)
run.bat
```

Скрипт автоматически:
- Найдет все видео и аудио файлы в папке `in/`
- Создаст `.srt` файлы в папке `out/`
- Пропустит уже обработанные файлы
- Покажет прогресс и статистику

### Расширенные опции

```bash
# Использовать свои папки
uv run python transcribe.py -i my_videos -o my_subtitles

# Изменить максимальное количество символов (по умолчанию 10)
uv run python transcribe.py --max-chars 15

# Использовать другую модель Whisper (быстрее, но менее точно)
uv run python transcribe.py --model medium

# Указать язык (по умолчанию русский)
uv run python transcribe.py --language en

# Принудительно использовать CPU
uv run python transcribe.py --device cpu

# Использовать GPU (CUDA) - намного быстрее!
uv run python transcribe.py --device cuda

# Указать тип вычислений (для оптимизации)
uv run python transcribe.py --compute-type int8
```

### Полная справка

```bash
uv run python transcribe.py --help
```

Опции:
- `-i, --input-dir` - Папка с видео/аудио файлами (по умолчанию: `in`)
- `-o, --output-dir` - Папка для SRT файлов (по умолчанию: `out`)
- `-m, --model` - Размер модели Whisper (large-v3, medium, small, base, tiny)
- `-c, --max-chars` - Максимум символов на субтитр (по умолчанию: 10)
- `-l, --language` - Код языка (ru, en, и т.д.)
- `-d, --device` - Устройство (auto, cpu, cuda)
- `--compute-type` - Тип вычислений (auto, int8, float16, float32)

## Формат вывода

Скрипт генерирует SRT файлы в формате, совместимом с DaVinci Resolve:

```
1
00:00:01,000 --> 00:00:02,500
 Привет

2
00:00:02,500 --> 00:00:04,000
 мир!
```

Каждый субтитр:
- Начинается с пробела (формат DaVinci Resolve)
- Содержит максимум указанное количество символов
- Разбивается по словам (не разрывает слова)
- Имеет точные временные метки на уровне слов

## Работа с паузами в DaVinci Resolve

Скрипт сохраняет ВСЕ паузы и моменты тишины в субтитрах с правильными временными метками. Это позволяет:
- Использовать функцию "Remove Silence" в DaVinci Resolve для автоматического удаления пауз
- Точно синхронизировать субтитры с речью после удаления тишины
- Вручную контролировать, какие паузы удалять, а какие оставить

Субтитры будут корректно привязаны к таймлайну даже после обработки Remove Silence.

## Импорт в DaVinci Resolve

1. Откройте ваш проект в DaVinci Resolve
2. Перейдите в Edit панель
3. Правый клик на таймлайне → Subtitles → Import Subtitle...
4. Выберите сгенерированный .srt файл
5. Субтитры появятся на таймлайне и готовы к редактированию

## Поддерживаемые форматы

### Видео форматы
- MP4, MOV, AVI, MKV, WebM
- FLV, WMV, M4V, MPG, MPEG

### Аудио форматы
- WAV, MP3, M4A, FLAC
- AAC, OGG, WMA, OPUS

Скрипт автоматически извлекает аудио из видео файлов.

## Примеры работы

```bash
# Базовый workflow
# 1. Копируем видео в папку in/
cp video1.mp4 video2.mov audio.wav in/

# 2. Запускаем обработку
uv run python transcribe.py

# Вывод:
# Found 3 file(s) to process
# Loading Whisper model: large-v3...
#
# [1/3] Processing video1.mp4...
#   Transcribing video1.mp4...
#   Detected language: ru (probability: 0.95)
#   Generated SRT file: video1.srt
#   Total subtitles: 142
#
# [2/3] Processing video2.mov...
#   ...
#
# [3/3] Processing audio.wav...
#   ...
#
# ==================================================
# Batch processing complete!
#   Processed: 3
#   Skipped (already done): 0
#   Errors: 0
# ==================================================

# 3. Результаты в папке out/
ls out/
# video1.srt  video2.srt  audio.srt

# Повторный запуск пропустит уже обработанные файлы
uv run python transcribe.py
# [1/3] Skipping video1.mp4 (already processed)
# [2/3] Skipping video2.mov (already processed)
# [3/3] Skipping audio.wav (already processed)
```

### Дополнительные примеры

```bash
# Английские субтитры с 12 символами на строку
uv run python transcribe.py -l en -c 12

# Быстрая обработка с моделью medium
uv run python transcribe.py -m medium

# Максимальная точность с GPU
uv run python transcribe.py -d cuda --compute-type float16

# Свои папки
uv run python transcribe.py -i videos -o subtitles
```

## Производительность

- **large-v3**: Наилучшее качество, медленнее (рекомендуется)
- **medium**: Хороший баланс скорости и качества
- **small/base**: Быстрая обработка, меньшая точность

С GPU (CUDA) обработка значительно быстрее (5-10x).

## Структура проекта

```
004_srt/
├── in/              # Положите сюда видео/аудио файлы
├── out/             # Здесь появятся .srt файлы
├── transcribe.py    # Основной скрипт
├── run.bat          # Быстрый запуск (Windows)
├── pyproject.toml   # Зависимости
└── README.md        # Документация
```

## Лицензия

MIT
