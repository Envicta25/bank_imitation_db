import mysql.connector

# Подключение к базе данных
conn = mysql.connector.connect(
    host="localhost",
    port = "3306",
    user="root",
    password="8&5jypSfzFyDhL",
)

# Создание курсора для выполнения SQL-запросов
cursor = conn.cursor()

# Создание БД
cursor.execute('''
    CREATE SCHEMA IF NOT EXISTS `hobbiton_bank`;
''')

# Подключение к базе данных
conn = mysql.connector.connect(
    host="localhost",
    port = "3306",
    user="root",
    password="8&5jypSfzFyDhL",
    database = 'hobbiton_bank'
)

# Создание курсора для выполнения SQL-запросов
cursor = conn.cursor()

# Создание таблицы для жителей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS citizens (
        id INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        surname VARCHAR(255) NOT NULL,
        address TEXT NOT NULL,
        phone_number VARCHAR(20) NOT NULL
    )
''')


# Создание таблицы для предприятий
cursor.execute('''
    CREATE TABLE IF NOT EXISTS commercial_entities (
        id INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        location_coordinates VARCHAR(20) NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        
        CONSTRAINT chk_location_coordinates CHECK (location_coordinates REGEXP '[0-9]{2}\.[0-9]{4}, [0-9]{2}\.[0-9]{4}')
    )
''')

# Создание таблицы для интернет-магазинов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS internet_shops (
        id INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
''')

# Создание таблицы для счетов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        account_number VARCHAR(20) NOT NULL,
        balance INT NOT NULL,
        
        citizen_id INT NULL,
        commercial_entity_id INT NULL,
        internet_shop_id INT NULL,
    
        account_type INT NOT NULL,
        
        FOREIGN KEY (citizen_id) REFERENCES citizens(id),
        FOREIGN KEY (commercial_entity_id) REFERENCES commercial_entities(id),
        FOREIGN KEY (internet_shop_id) REFERENCES internet_shops(id),
        CHECK (account_type IN (1, 2, 3, 4))
    )
''')


# Создание таблицы для карт
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INT AUTO_INCREMENT PRIMARY KEY,
        account_id INT NOT NULL,
        card_number VARCHAR(16) NOT NULL,
        
        daily_limit INT,
        monthly_limit INT,
        daily_limit_left INT,
        monthly_limit_left INT,
        
        FOREIGN KEY (account_id) REFERENCES bank_accounts(id) ON DELETE CASCADE
    )
''')

# Создание таблицы для банкоматов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS atms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        location_coordinates VARCHAR(20) NOT NULL,
        cash_balance INT NOT NULL,
        
        CONSTRAINT atms_location_coordinates CHECK (location_coordinates REGEXP '[0-9]{2}\.[0-9]{4}, [0-9]{2}\.[0-9]{4}')
    );
''')

# Создание таблицы для терминалов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS terminals (
        id INT AUTO_INCREMENT PRIMARY KEY,
        account_id INT NOT NULL,
        FOREIGN KEY (account_id) REFERENCES bank_accounts(id) ON DELETE CASCADE
    )
''')

# Создание таблицы для транзакций
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount INT NOT NULL,
        date_time DATETIME NOT NULL,
        sender_account INT NOT NULL,
        recipient_account INT NOT NULL,
               
        card_id INT NULL,
        atm_id INT NULL,
        terminal_id INT NULL,
        
        FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
        FOREIGN KEY (atm_id) REFERENCES atms(id) ON DELETE CASCADE,
        FOREIGN KEY (terminal_id) REFERENCES terminals(id) ON DELETE CASCADE,
               
        FOREIGN KEY (sender_account) REFERENCES bank_accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_account) REFERENCES bank_accounts(id) ON DELETE CASCADE
    )
''')

# Создание триггера для проверки корректности формата номера счета
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS check_account_number_format
    BEFORE INSERT ON bank_accounts
    FOR EACH ROW
    BEGIN
        DECLARE account_number_prefix CHAR(5);
        SET account_number_prefix = LEFT(NEW.account_number, 5);
        
        IF account_number_prefix != '40817' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Номер счета имеет неправильный формат!';
        END IF;
    END;
''')

# Создание триггера для проверки корректности формата номера карты
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS check_card_number_format
    BEFORE INSERT ON cards
    FOR EACH ROW
    BEGIN
        DECLARE card_number_prefix CHAR(6);
        SET card_number_prefix = LEFT(NEW.card_number, 6);
        
        IF card_number_prefix != '220072' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Номер карты имеет неправильный формат!';
        END IF;
    END;
''')

# Создание триггера для проверки корректности формата номера телефона
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS check_phone_number_format
    BEFORE INSERT ON citizens
    FOR EACH ROW
    BEGIN
        DECLARE phone_number_prefix CHAR(2);
        SET phone_number_prefix = LEFT(NEW.phone_number, 2);
        
        IF phone_number_prefix != '+7' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Номер телефона имеет неправильный формат!';
        END IF;
    END;
''')

# Создание триггера для проверки ссылочной целостности данных в транзакциях (при добавлении транзакции должны существовать счета отправителей и получателей)
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS check_transaction_accounts_existence
    BEFORE INSERT ON transactions
    FOR EACH ROW
    BEGIN
        DECLARE sender_exists INT;
        DECLARE recipient_exists INT;

        SELECT COUNT(*) INTO sender_exists FROM bank_accounts WHERE id = NEW.sender_account;
        SELECT COUNT(*) INTO recipient_exists FROM bank_accounts WHERE id = NEW.recipient_account;

        IF sender_exists = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Отправителя транзакции не существует!';
        END IF;

        IF recipient_exists = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Получателя транзакции не существует!';
        END IF;
    END;
''')

# Триггер, реализующий уменьшение лимитов и контроль за ними
cursor.execute('''

CREATE TRIGGER decrease_limits
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    -- Проверяем, является ли операция отправкой средств с карты
    IF NEW.sender_account <> 1 THEN
        -- Уменьшаем daily_limit_left только если после операции значение не станет отрицательным
        IF (SELECT daily_limit_left - NEW.amount >= 0 FROM cards WHERE id = NEW.card_id) THEN
            UPDATE cards SET daily_limit_left = daily_limit_left - NEW.amount WHERE id = NEW.card_id;
                    -- Уменьшаем monthly_limit_left только если после операции значение не станет отрицательным
            IF (SELECT monthly_limit_left - NEW.amount >= 0 FROM cards WHERE id = NEW.card_id) THEN
                UPDATE cards SET monthly_limit_left = monthly_limit_left - NEW.amount WHERE id = NEW.card_id;
            END IF;
        END IF;

    END IF;
END;
''')


# Создание триггера для снятия наличных
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS withdraw_from_atm
    AFTER INSERT ON transactions
    FOR EACH ROW
    BEGIN
        DECLARE atm_cash_balance INT;
        DECLARE atm_cash_balance_new INT;
        
        SELECT cash_balance INTO atm_cash_balance FROM atms WHERE id = NEW.atm_id;
        
        IF NEW.recipient_account = 1 THEN
            SET atm_cash_balance_new = atm_cash_balance - NEW.amount;
            
            IF atm_cash_balance_new < 0 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Недостаточно наличных в банкомате!';
            ELSE
                UPDATE atms SET cash_balance = atm_cash_balance_new WHERE id = NEW.atm_id;
            END IF;
        END IF;
    END;
''')

# Триггер, реализующий пополнение через банкомат наличными
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS deposit_to_client
    AFTER INSERT ON transactions
    FOR EACH ROW
    BEGIN
        IF NEW.sender_account = 1 THEN
            UPDATE atms
            SET cash_balance = cash_balance + NEW.amount
            WHERE id = NEW.atm_id;
        END IF;
    END;
''')

# Создание триггера для проверки привязки терминалов к счетам только к предприятиям
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS enforce_terminal_account_check
    BEFORE INSERT ON terminals
    FOR EACH ROW
    BEGIN
        DECLARE account_type_value INT;
        
        -- Получаем значение account_type для соответствующего счета
        SELECT account_type INTO account_type_value FROM bank_accounts WHERE id = NEW.account_id;
        
        -- Проверяем значение account_type
        IF account_type_value != 1 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Терминал можно привязать только к счету предприятия!';
        END IF;
    END;
''')

# Триггер, который проверяет что карта будет привязана к счету гражданина
cursor.execute('''
    CREATE TRIGGER check_account_type_before_insert
    BEFORE INSERT ON cards
    FOR EACH ROW
    BEGIN
        DECLARE account_type_value INT;
        
        -- Получаем значение account_type для соответствующего счета
        SELECT account_type INTO account_type_value FROM bank_accounts WHERE id = NEW.account_id;
        
        -- Проверяем значение account_type
        IF account_type_value != 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Карту можно привязать только к счету гражданина!';
        END IF;
    END;
''')

# Поиск счета с максимальным балансом
cursor.execute('''
    CREATE PROCEDURE find_account_with_max_balance()
    BEGIN
        SELECT id, account_number, balance
        FROM bank_accounts
        WHERE id != 1
        ORDER BY balance DESC
        LIMIT 1;
    END;
''')

# Поиск счета с максимальным количеством карточек
cursor.execute('''
    CREATE PROCEDURE find_account_with_max_cards()
    BEGIN
        SELECT bank_accounts.id, account_number, COUNT(cards.id) AS card_count
        FROM bank_accounts
        LEFT JOIN cards ON bank_accounts.id = cards.account_id
        GROUP BY bank_accounts.id
        ORDER BY card_count DESC
        LIMIT 1;
    END;
''')

# Двойная покупка
cursor.execute('''
    CREATE PROCEDURE find_double_purchase()
    BEGIN
        SELECT 
                t1.id AS transaction_id_1,
                t1.amount AS amount_1,
                t1.date_time AS date_time_1,
                t2.id AS transaction_id_2,
                t2.amount AS amount_2,
                t2.date_time AS date_time_2
            FROM 
                transactions t1
            JOIN 
                transactions t2 ON t1.amount = t2.amount AND t1.id < t2.id
            WHERE
                t1.id <> t2.id AND
                t2.recipient_account IN (SELECT id FROM bank_accounts WHERE account_type = 1) AND
                t1.recipient_account IN (SELECT id FROM bank_accounts WHERE account_type = 1) AND
                ABS(TIMEDIFF(t1.date_time, t2.date_time)) < 500;
    END;
''')

# Поломанный банкомат
cursor.execute('''
    CREATE PROCEDURE find_inactive_atm()
    BEGIN
        DECLARE last_transaction_date DATE;
        -- Находим день последней транзакции
        SELECT DATE(MAX(date_time)) INTO last_transaction_date FROM transactions;
        
        -- Выбираем банкоматы, в которых не было операций снятия наличных за последние сутки
        SELECT atms.id, atms.location_coordinates
        FROM atms
        WHERE atms.id NOT IN (
            SELECT DISTINCT t.atm_id 
            FROM transactions t
            WHERE t.date_time > DATE_SUB(last_transaction_date, INTERVAL 1 DAY) AND t.atm_id IS NOT NULL);
    END
''')

# Поиск операций которые выходят за лимиты
cursor.execute('''
    CREATE PROCEDURE find_overlimit()
    BEGIN
        SELECT 
            t.id, 
            t.amount, 
            t.date_time,
            c.id,
            c.daily_limit,
            c.monthly_limit,
            c.daily_limit_left,
            c.monthly_limit_left
        FROM transactions t
        INNER JOIN cards c ON t.card_id = c.id
        WHERE (t.amount > c.daily_limit_left OR t.amount > c.monthly_limit_left) and t.sender_account <> 1;
    END
            
''')


# Запрос который выводит карту с наибольшим количеством операций в указанный день
cursor.execute('''
CREATE PROCEDURE find_card_with_most_transactions(IN search_date DATE)
BEGIN
    DECLARE card_id_with_most_transactions INT;
    DECLARE transaction_count_with_most_transactions INT;

    -- Проверка даты
    IF search_date NOT IN (
        SELECT DISTINCT DATE(date_time)
        FROM transactions
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'На данную дату нет информации!';
    END IF;

    -- Выбираем карту с наибольшим количеством транзакций за указанный день
    SELECT
        card_id, COUNT(*) AS transaction_count
    INTO
        card_id_with_most_transactions, transaction_count_with_most_transactions
    FROM
        transactions
    WHERE
        DATE(date_time) = search_date
    GROUP BY
        card_id
    ORDER BY
        transaction_count DESC
    LIMIT 1;

    SELECT
        card_id_with_most_transactions AS card_id,
        transaction_count_with_most_transactions AS transaction_count;

END;
''')

# Запрос который выводит операции проведенные в нерабочее время предприятий
cursor.execute('''
CREATE PROCEDURE find_transactions_in_non_working_hours()
    BEGIN
        SELECT t.id, amount, date_time, start_time, end_time
        FROM transactions t
        INNER JOIN commercial_entities ce ON t.sender_account = ce.id
        WHERE (DATE_FORMAT(t.date_time, '%H:%i') < ce.start_time OR DATE_FORMAT(t.date_time, '%H:%i') > ce.end_time);
    END;
''')

# Запрос который выводит интернет магазин с максимальным количеством продаж
cursor.execute('''
CREATE PROCEDURE find_shop_with_max_orders(IN start_date DATE, IN end_date DATE)
    BEGIN
        DECLARE earliest_date DATE;
        DECLARE latest_date DATE;
        
        -- Проверка начала периода
        SELECT MIN(date_time) INTO earliest_date
        FROM transactions;
        
        IF start_date < earliest_date THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Начало периода указано некорректно!';
        END IF;
        
        -- Проверка конца периода
        SELECT MAX(date_time) INTO latest_date
        FROM transactions;
        
        IF end_date > latest_date THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Конец периода указан некорректно!';
        END IF;
               
        IF end_date = start_date THEN 
            SET end_date = end_date + INTERVAL 1 DAY;
        END IF;
        
        SELECT 
            i.id AS shop_id,
            i.name AS shop_name,
            COUNT(t.id) AS total_orders
        FROM 
            internet_shops i
        JOIN 
            bank_accounts b ON i.id = b.internet_shop_id
        JOIN 
            transactions t ON b.id = t.recipient_account
        WHERE 
            t.date_time BETWEEN start_date AND end_date
        GROUP BY 
            i.id, i.name
        ORDER BY 
            total_orders DESC
        LIMIT 5;
    END;
''')

# Запрос который выводит статистику по предприятию за последние несколько дней
cursor.execute('''
CREATE PROCEDURE transaction_statistics(IN num_days INT, IN commercial_entity_id INT, IN search_date DATE)
BEGIN
    DECLARE avg_profit DECIMAL(10, 2);
    DECLARE max_profit INT;
    DECLARE max_transactions INT;
    DECLARE name TEXT; 
    DECLARE earliest_date DATE;
    DECLARE latest_date DATE;
    DECLARE account_entity_id INT;
               
    -- Проверка на то что счет принадлежит предприятию           
    SELECT commercial_entity_id INTO account_entity_id
    FROM bank_accounts
    WHERE bank_accounts.commercial_entity_id = commercial_entity_id AND account_type = 1;
               
    IF account_entity_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Этот id не принадлежит предприятию!';
    END IF;
    
               
    -- Проверка числовых значений
    IF num_days < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Количество дней не может быть отрицательным!';
    END IF;  
    
    -- Проверка даты    
    SELECT MIN(date_time) INTO earliest_date
    FROM transactions;
    
    SELECT MAX(date_time) INTO latest_date
    FROM transactions;
               
    IF (search_date < earliest_date) OR (search_date - INTERVAL num_days DAY > latest_date) OR (search_date - INTERVAL num_days DAY < earliest_date) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Нет информации на данный период!';
    END IF;
               
    -- Средняя прибыль с одной операции у выбранного предприятия
    SELECT AVG(t.amount) INTO avg_profit
    FROM transactions t
    JOIN bank_accounts ba ON t.recipient_account = ba.id
    WHERE ba.commercial_entity_id = commercial_entity_id
    AND t.date_time >= DATE_SUB(search_date, INTERVAL num_days DAY) AND t.date_time <= search_date;

    -- Максимальная прибыль с одной операции для выбранного предприятия
    SELECT MAX(t.amount) INTO max_profit
    FROM transactions t
    JOIN bank_accounts ba ON t.recipient_account = ba.id
    WHERE ba.commercial_entity_id = commercial_entity_id
    AND t.date_time >= DATE_SUB(search_date, INTERVAL num_days DAY) AND t.date_time <= search_date;

    -- Максимальное количество операций для выбранного предприятия
    SELECT transaction_count INTO max_transactions
    FROM (
        SELECT COUNT(*) AS transaction_count
        FROM transactions t
        JOIN bank_accounts ba ON t.recipient_account = ba.id
        WHERE ba.commercial_entity_id = commercial_entity_id
        AND t.date_time >= DATE_SUB(search_date, INTERVAL num_days DAY) AND t.date_time <= search_date
    ) AS transaction_counts;

    -- Вывод результатов
    SELECT 
        ce.name AS commercial_entity,
        avg_profit AS average_profit_per_transaction,
        max_profit AS maximum_profit_per_transaction,
        max_transactions AS transaction_count
    FROM commercial_entities ce
    WHERE ce.id = commercial_entity_id;
END;
               
    ''')

# Запрос на вывод статистики по гражданину
cursor.execute('''
CREATE PROCEDURE citizen_statistics(IN citizen_id INT, IN start_date DATE, IN end_date DATE)
BEGIN
    DECLARE avg_spent DECIMAL(10, 2);
               
    DECLARE favourite_internet_shop_account_id INT;
    DECLARE favourite_internet_shop_name TEXT;
    DECLARE favourite_internet_shop_count_transactions INT;
               
    DECLARE favourite_commercial_entity_account_id INT;
    DECLARE favourite_commercial_entity_name TEXT;
    DECLARE favourite_commercial_entity_transactions INT;
         
    DECLARE earliest_date DATE;
    DECLARE latest_date DATE; 
    DECLARE account_entity_id INT;
               
    -- Проверка на то что счет принадлежит гражданину           
    SELECT citizen_id INTO account_entity_id
    FROM bank_accounts
    WHERE bank_accounts.citizen_id = citizen_id AND account_type = 2;
               
    IF account_entity_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Этот id не принадлежит гражданину!';
    END IF;
    
    -- Проверка начала периода
    SELECT MIN(date_time) INTO earliest_date
    FROM transactions;
        
    IF start_date < earliest_date THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Начало периода указано некорректно!';
    END IF;
        
    -- Проверка конца периода
    SELECT MAX(date_time) INTO latest_date
    FROM transactions;
        
    IF end_date > latest_date THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Конец периода указан некорректно!';
    END IF;
    
    IF end_date = start_date THEN 
        SET end_date = end_date + INTERVAL 1 DAY;
    END IF;
          
    -- Средняя сумма операции с одной операции у выбранного жителя
    SELECT AVG(t.amount) INTO avg_spent
    FROM transactions t
    JOIN bank_accounts ba ON t.sender_account = ba.id
    WHERE ba.citizen_id = citizen_id 
    AND t.date_time BETWEEN start_date AND end_date
    AND recipient_account IN (SELECT id FROM bank_accounts WHERE account_type = 1 OR account_type = 3);
    
    -- Любимый интернет магазин
    SELECT recipient_account, COUNT(*) AS transactions_count INTO favourite_internet_shop_account_id, favourite_internet_shop_count_transactions
    FROM transactions t
    WHERE recipient_account IN (SELECT id FROM bank_accounts WHERE account_type = 3) AND sender_account = 
    (SELECT bank_accounts.id FROM bank_accounts WHERE bank_accounts.citizen_id = citizen_id) AND (t.date_time BETWEEN start_date AND end_date)
    GROUP BY recipient_account
    ORDER BY transactions_count DESC
    LIMIT 1;
    
    -- Название любимого интернет-магазина
    SELECT internet_shops.name INTO favourite_internet_shop_name 
    FROM internet_shops
    WHERE internet_shops.id = (SELECT bank_accounts.internet_shop_id FROM bank_accounts WHERE bank_accounts.id = favourite_internet_shop_account_id);
    
    -- Любимое предприятие
    SELECT recipient_account, COUNT(*) AS transactions_count INTO favourite_commercial_entity_account_id, favourite_commercial_entity_transactions
    FROM transactions t
    WHERE recipient_account IN (SELECT id FROM bank_accounts WHERE account_type = 1) AND sender_account = 
    (SELECT bank_accounts.id FROM bank_accounts WHERE bank_accounts.citizen_id = citizen_id) AND (t.date_time BETWEEN start_date AND end_date)
    GROUP BY recipient_account
    ORDER BY transactions_count DESC
    LIMIT 1;
    
    -- Название любимого предприятия
    SELECT commercial_entities.name INTO favourite_commercial_entity_name 
    FROM commercial_entities
    WHERE commercial_entities.id = (SELECT bank_accounts.commercial_entity_id FROM bank_accounts WHERE bank_accounts.id = favourite_commercial_entity_account_id);
               
    -- Вывод результатов
    SELECT 
        citizen_id,
        avg_spent, 
               
        favourite_internet_shop_name,
        favourite_internet_shop_count_transactions,
               
        favourite_commercial_entity_name,
        favourite_commercial_entity_transactions;
END;             
             
''')




# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()
