# InvestBot
Это мой первый телеграм-бот. Он работает с TinkoffAPI. С помощью
него возможно будет получать информацию об аккаунте, портфеле,
ценных бумагах, покупать/продавать бумаги, получать информацию
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
будет выведено соответствующее сообщение<br>

### 10.02.2024

- Теперь новый функционал тестируется в ветке creative, либо main, если тестирование<br>
проходит успешно, то сливается с веткой master<br>
- Добавлен файл tech_analyze.py, содержащий функционал для технического анализа. Классы: <br>
<b>MA_indicator</b>: абстрактный класс для скользящей средней<br>
<b>SMA_indicator</b>: класс-наследник MA_indicator, реализует функционал для построения SMA<br>
<b>EMA_indicator</b>: класс-наследник MA_indicator, реализует функционал для построения EMA<br>
<b>RSI</b>: класс, реализующий функционал для построения RSI. Выдает значения RSI для каждого момента<br>
времени в виде списка<br>
<b>MACD</b>: класс, реализующий функционал для построения MACD в виде списка<br>
<b>HAS_Model</b>: класс, реализующий функционал, для выявления фигуры "Голова и плечи"

### 11.02.2024

- Классы MA_indicator и его наследники перенесены в отдельный модуль MA_indicator
- Классы, реализующие функционал MA, больше не являются статическими
- Классы, реализующие осцилляторы выведены в отдельный модуль oscillators
- Исправлены некоторые недочеты в моделировании торговли в run_main()