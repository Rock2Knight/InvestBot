# InvestBot
Это мой первый телеграм-бот. Он работает с TinkoffAPI. С помощью
него возможно будет получать информацию об аккаунте, портфеле,
ценных бумагах, покупать/продавать бумаги как в автоматическом, так и полуавтоматическом режиме, получать информацию
о ходе цены бумаги за период.

## Обновления
### 01.07.2023

- Метод getAccounts(), позволяющий узнать список всех аккантов<br>
Активируется командой /getAccounts<br>
- Метод PayIn(), позволяющий пополнить счет в песочнице (пока только<br>
первый, который вы создали). Команда:<br>
/PayIn amount<br>
amount - сумма в рублях. Можно в виде десятчиного числа (например: 130.50)
- Метод GetSandboxPortfolio(), позволяющий узнать баланс счета в рублях, который<br>
указан в качестве параметра в сообщении. Команда: <br>
/portfolio account_id<br>
где account_id - номер счета в песочнице. В случае, если такого счета не существует,<br>
будет выведено соответствующее сообщение

### 12.02.2024

- Изменены методы в core_bot.py, отвечающие за получение исторических свечей за<br>
запрашиваемый период. Теперь можно получать максимально актуальные данные и при<br>
нормально их сохранять и считывать

### 23.02.2024

- Добавлен графический интерфейс пользователя, для возможности статистики по тестированию
торговых стратегий.<br>На данный момент присутствует только возможность отображения диаграммы с
соотношением прибыльных и <br>убыточных сделок. Но также планируется ввести график отображения 
доходности портфеля за период торговли.
- Теперь алгоритм, моделирующий торговлю, сохраняет необходимые для анализа данные по состоянию портфеля<br>
в каждый момент времени и данные по сделкам в датафреймы, а также в CSV
- Лог торговли по историческим данным также записывается в файл, помимо консоли

### 01.03.2024

- Добавлена возможность отображения графика доходности на при моделировании торговли за определенный период<br>
- Добавлен код, реализующий выставление стоп-маркетов на продажу при покупке активов. Стоп-маркеты работают
как предохранительный клапан.

### 24.03.2024

- Добавлена база данных для хранения информации о котировках, инструментах и другой информации, связанной<br>
с инвестициями
- Добавлены методы, позволяющие выгрузить по TinkoffInvestAPI данные обо всех активах и инструментах Tinkoff.<br>
- Теперь при выгрузке инструментов учитывается иерархия: "Актив" > "Параметр" > "Инструмент" (но это пока не учтено)<br>
в схеме БД!)
- Обновление метода core_bot.get_candles(): теперь можно выгружать котировки по идентификатору instrument_uid

### 30.03.2024

- В тестовом модуле добавлены асинхронные операции. Теперь можно выгружать котировки сразу по нескольким бумагам<br>
в асинхронном режиме.
- Обновлен интерфейс пользователя: теперь можно выбирать таймфрейм, выбирать период моделирования торговли. Добавлена кнопка<br>
для получения котировок по инструментам. UID требуемых инструментов задаются в файле instruments.txt
- В тестовом модуле теперь можно моделировать торговлю по жестко заданной в коде стратегии сразу по нескольким торговым<br>
инструментам (до 10 за раз). Причем делается это асинхронно для всех инструментов. <br>
Ограничение: при выборе таймфрейма нужно аккуратно вводить заданный период времени, так-как у TinkoffInvestAPI есть<br>
ограничения на период выгрузку данных для каждого таймфрейма. В будущем будет доступна выгрузка пакетами, но пока этого нет.


### 31.03.2024

- Улучшена настройка логирования: теперь с выводом сообщения выводится и время вывода
- Полностью убран вызов метода моделирования торговли при создании объекта приложения. Также убран метод async_main() за ненадобностью
- Изменен класс SMAIndicator: теперь данные о котировках выгружаются из файла, а не пердаются как датафрейм. Также теперь, по аналогии<br>
с методами asyncRequestHandler и HistoryTrain, значения о SMA по каждому инструменту сохраняются в отдельном файле
- Класс RSI изменен по аналогии с SMAIndicator (но данные RSI по каждому инструменту пока перезаписываются в один и тот же файл)
- Улучшена логика работы стоп-маркетов на продажу: теперь заявки срабатывают в порядке от заявки по макимальному уровню до минимального.<br>
Также сообщения о срабатывании стоп-маркета выводятся в консоль и historyTrading.txt
- TODO: почему-то не метод HistoryTrain не работает без предварительного вызова GraphicApp.GetCandles. Надо это исправить

### 02.04.2024

- Добавлена функция проверки превышения риска для счета в функции HistoryTrain модуля tech_analyze. Теперь при достижении
риска для счета, функция выводит сообщение в консоль и возвращает кортеж из двух None
- Исправлен баг с получением токенов: теперь все токены хранятся файле окружения
- Улучшено логирование: теперь сообщения об ошибках записываются в логи
- Добавлен модуль excel_handler.py, позволяющий создавать сводные таблицы, по которым можно оценивать эффективность стратегий

### 03.04.2024

- Сформирован класс для работы со сводными таблиицами. Пока что работает хорошо

### 04.04.2024

- Определен метод в GraphicApp, позволяющий получать данные для визуализации по всем инструментам из instruments.txt
- Добавлены предупреждения об ошибках в графическом интерфейсе программы в виде всплывающих окон
- Метод drawHistTrades переопределен для отрисовки многоядерно гистограммы по нескольким инструментам

### 05.04.2024

- Метод drawProfitPlot переопределен для отрисовки графиков сразу по нескольким торрговым инструментам
- Настроено оформление графиков для лучшей читабельности

### 08.04.2024

- Добавлен модуль, тестирующий достоверность данных HistoryTrain модуля tech_analyze
- В графический интерфейс внесены изменения, позволяющие протестировать HistoryTrain на достоверность
- В app.bot изменены коррективы в инициализацию БД. Раньше, если какой-то актив присутствует, этот актив просто скипался,<br>
даже если в базе нет всех инструментов, принадлежащих ему
- Добавлен

### 23.04.2024

- Описана логика торговли по заданной стратегии в режиме реального времени в контуре песочницы. Но при первом тесте,
сессия не выдала торговых сигналов. В течение следующей недели будем активно тестировать и доводить до того, чтобы робот реально<br>
торговал.
- Были реализованы методы получения технических индикаторов с помощью методов TinkoffInvestAPI
- Также был опробован пример работы со стримом из tinkoff.invest.examples.
- Почему при асинхронном заполнении базы, она не заполняется всеми необходимыми инструментами. Я попробую это пофиксить потом

### 27.04.2024

- Были реализованы методы для получения данных по свечам в стриме. Теперь это делается в отдельном процессе
- Результаты по сделкам и состоянию портфеля записываются в CSV-файлы для дальнейшей статистки (правда пока еще немного криво)
- По результатам тестирования сигналы ловятся и сделки совершаются (правда пока только на продажу и как-то криво)

### 14.05.2024

- Класс InvestBot разделен на структуру из нескольких классов с целью улучшить читаемость кода и делегировать обязанности.
Теперь за работу с базой данных отвечает класс InstrumentLoader, за работу с котировками отвечает класс CandlesLoader, а
InvestBot отвечает исключительно за торговую логику
- Функции преобразования типов вынесены в класс app_utils.py

### 15.05.2024

- Добавлены unit-тесты для CandlesLoader

### 16.05.2024

- Добавлен модуль для телеграм чат-бота для управления торговым роботом
- Некоторые тестовые и ненужные файлы были удалены или добавлены в .gitignore