import psycopg2


class ConnectDB:
    def __init__(self):
        self.info_db = {
            'user': 'postgres',
            'password': '8961',
            'host': '127.0.0.1',
            'database': 'wildberries'
        }
        self.conn = psycopg2.connect(** self.info_db)
        self.cursor = self.conn.cursor()


    async def query_select(self, request):
        self.cursor.execute(request)


    async def query_select_param(self, request, value):
        self.cursor.execute(request, value)


    async def query_param(self, request, value):
        self.cursor.execute(request, value)
        self.conn.commit()


    def sync_query_param(self, request, value):
        self.cursor.execute(request, value)
        self.conn.commit()


    async def insert_many(self, request, values):
        try:
            self.cursor.executemany(request, values)
            self.conn.commit()
        except Exception as _ex:
            print(_ex)

    async def query(self, request):
        self.cursor.execute(request)
        self.conn.commit()


    async def fetch_many(self):
        res = self.cursor.fetchall()
        return res


    async def fetch_one(self):
        res = self.cursor.fetchone()
        return res

    def sync_fetch_one(self):
        res = self.cursor.fetchone()
        return res


    async def query_other(self, request):
        self.cursor.execute(request)
        self.conn.commit()

    async def close(self):
        self.cursor.close()
        self.conn.close()

    def sync_close(self):
        self.cursor.close()
        self.conn.close()



class Use:
    def __init__(self):
        self.cursor = ConnectDB()

    async def create_good_prod(self):
        crt_tbl = '''CREATE TABLE good_prod (
                                                id SERIAL PRIMARY KEY,
                                                category TEXT,
                                                prod_id	TEXT UNIQUE,
                                                price	TEXT,
                                                link	TEXT,
                                                image	TEXT,
                                                date	TEXT
                                            );'''
        await self.cursor.query(crt_tbl)


    async def close(self):
        await self.cursor.close()


    def sync_close(self):
        self.cursor.sync_close()


    async def create_old_prod(self):
        crt_tbl = '''CREATE TABLE old_prod (
                                                id SERIAL PRIMARY KEY,
                                                category TEXT,
                                                prod_id	TEXT UNIQUE,
                                                price	TEXT,
                                                link	TEXT,
                                                image	TEXT,
                                                date	TEXT
                                            );'''
        await self.cursor.query(crt_tbl)


    async def create_new_prod(self):
        crt_tbl = '''CREATE TABLE new_prod (
                                                id SERIAL PRIMARY KEY,
                                                category TEXT,
                                                prod_id	TEXT UNIQUE,
                                                price	TEXT,
                                                link	TEXT,
                                                image	TEXT,
                                                date	TEXT
                                            );'''
        await self.cursor.query(crt_tbl)


    async def add_new_prods(self, product):
        query = f'''INSERT INTO new_prod(
                                        prod_id,
                                        price,
                                        link,
                                        image,
                                        category,
                                        color,
                                        size,
                                        name
                                        ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;'''

        await self.cursor.insert_many(query, product)


    async def get_new_ids(self):
        query = 'SELECT prod_id FROM new_prod'
        await self.cursor.query_select(query)
        return await self.cursor.fetch_many()


    async def get_new_prod(self, prod_id):
        query = 'SELECT * FROM new_prod WHERE prod_id=%s'
        await self.cursor.query_select_param(query, (prod_id, ))
        return await self.cursor.fetch_one()


    async def get_old_prod(self, prod_id):
        query = 'SELECT * FROM old_prod WHERE prod_id=%s'
        await self.cursor.query_select_param(query, (prod_id, ))
        return await self.cursor.fetch_one()


    async def add_good_prods(self, product):
        query = '''INSERT INTO good_prod(
                                        category,
                                        prod_id,
                                        price,
                                        link,
                                        image,
                                        date) VALUES(%s, %s, %s, %s, %s, %s);'''
        await self.cursor.query_param(query, product)


    async def clear_old_prod(self):
        query = 'DELETE FROM old_prod'
        await self.cursor.query_other(query)


    async def migration(self):
        query = 'INSERT INTO old_prod SELECT * FROM new_prod'
        await self.cursor.query_other(query)


    async def clear_new_prod(self):
        query = 'DELETE FROM new_prod'
        await self.cursor.query_other(query)


    async def clear_good_prod(self):
        query = 'DELETE FROM good_prod'
        await self.cursor.query_other(query)


    async def get_quantity_prod(self):
        query = 'SELECT id FROM old_prod'
        await self.cursor.query_select(query)
        res = await self.cursor.fetch_many()
        return len(res)


    async def get_quantity_good_prod(self):
        query = 'SELECT id FROM good_prod'
        await self.cursor.query_select(query)
        res = await self.cursor.fetch_many()
        return len(res)


    async def get_all_old_prod(self):
        query = 'SELECT * FROM old_prod'
        await self.cursor.query_select(query)
        return await self.cursor.fetch_many()


    async def get_all_new_prod(self):
        query = 'SELECT * FROM new_prod'
        await self.cursor.query_select(query)
        return await self.cursor.fetch_many()


    async def compare(self):
        query = '''INSERT INTO good_prod (prod_id, old_price, new_price, link, image, category, color, size, name)
                SELECT new_prod.prod_id, new_prod.price, old_prod.price, new_prod.link, new_prod.image, new_prod.category, new_prod.color, new_prod.size, new_prod.name
                FROM new_prod
                JOIN old_prod USING (prod_id)
                WHERE new_prod.price <= old_prod.price * 0.8 ON CONFLICT DO NOTHING'''
        await self.cursor.query_other(query)


    async def get_users_categories(self):
        query = '''SELECT category FROM user_categories'''

        await self.cursor.query_select(query)
        return await self.cursor.fetch_many()


    async def get_categories_and_ids(self):
        query = '''SELECT tgid, category FROM user_categories'''

        await self.cursor.query_select(query)
        return await self.cursor.fetch_many()


    async def get_good_prod(self, category):
        queue = 'SELECT * FROM good_prod WHERE category=%s'

        await self.cursor.query_select_param(queue, (category, ))
        return await self.cursor.fetch_many()


    async def exists_good_prods(self):
        queue = '''SELECT * FROM good_prod'''

        await self.cursor.query(queue)
        res = await self.cursor.fetch_many()
        if not res:
            return False
        else:
            return True


    async def get_good_link(self, prod_id):
        queue = 'SELECT link FROM shipped_items WHERE prod_id=%s'
        await self.cursor.query_select_param(queue, (str(prod_id), ))
        return await self.cursor.fetch_one()


    async def get_good_sizes(self, prod_id):
        queue = 'SELECT size FROM shipped_items WHERE prod_id=%s'
        await self.cursor.query_select_param(queue, (str(prod_id), ))
        return await self.cursor.fetch_one()


    async def get_user_categories(self, user_id):
        queue = 'SELECT category FROM user_categories WHERE tgid=%s'

        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_many()
        if not res:
            return False
        else:
            return res


    async def add_user_category(self, user_id, category):
        queue = """INSERT INTO user_categories (tgid, category)
                        VALUES(%s, %s) ON CONFLICT DO NOTHING
                        ;"""

        await self.cursor.query_param(queue, (str(user_id), category, ))


    async def delete_user_category(self, user_id, category):
        queue = 'DELETE FROM user_categories WHERE tgid=%s and category=%s'

        await self.cursor.query_param(queue, (str(user_id), str(category), ))

    # При старте
    async def add_user(self, user_id, user_name, date):
        queue = """INSERT INTO users (tgid, username, date)
                        VALUES(%s, %s, %s) ON CONFLICT DO NOTHING
                        ;"""

        await self.cursor.query_param(queue, (str(user_id), user_name, str(date), ))



    # Реферальная система
    async def exist_user(self, user_id):
        queue = '''SELECT * FROM users WHERE tgid=%s'''

        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_one()
        if res:
            return True
        else:
            return False


    async def exist_referral(self, user_id):
        queue = 'SELECT * FROM referrals WHERE referral=%s'
        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_one()
        if res:
            return True
        else:
            return False


    async def add_referral(self, referrer_id, referral_id):
        queue = """INSERT INTO referrals (referrer, referral)
                        VALUES(%s, %s) ON CONFLICT DO NOTHING
                        ;"""
        await self.cursor.query_param(queue, (str(referrer_id), str(referral_id), ))


    async def get_fullname(self, user_id):
        queue = 'SELECT username FROM users WHERE tgid=%s'

        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_one()
        return res[0]


    async def get_count_referrals(self, user_id):
        queue = 'SELECT COUNT(id) FROM referrals WHERE referrer=%s'

        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_one()
        if res:
            return res[0]
        else:
            return 0

    # Парсер
    async def add_shipped_item(self, user_id, prod_id, link=None, size=None):
        queue = 'INSERT INTO shipped_items(tgid, prod_id, link, size) VALUES(%s, %s, %s, %s) ON CONFLICT DO NOTHING'

        await self.cursor.query_param(queue, (user_id, prod_id, link, size))


    async def exist_in_shipped_items(self, user_id, prod_id):
        queue = 'SELECT * FROM shipped_items WHERE tgid=%s and prod_id=%s'

        await self.cursor.query_select_param(queue, (user_id, prod_id, ))
        res = await self.cursor.fetch_many()
        if res:
            return True
        else:
            return False



    # Админ
    async def get_quantity_users(self):
        queue = 'SELECT COUNT(id) FROM users'
        await self.cursor.query_select(queue)
        res = await self.cursor.fetch_one()
        if res:
            return res[0]
        else:
            return 0


    async def get_quantity_sub_users(self):
        queue = 'SELECT COUNT(id) FROM user_status WHERE status=%s'
        await self.cursor.query_select_param(queue, ('active', ))
        res = await self.cursor.fetch_one()
        if res:
            return res[0]
        else:
            return 0


    async def get_user_ids(self):
        queue = 'SELECT tgid FROM users'

        await self.cursor.query_select(queue)
        res = await self.cursor.fetch_many()
        if res:
            return res
        else:
            return False


    async def exist_msg(self, category):
        queue = 'SELECT * FROM messages WHERE category=%s'

        await self.cursor.query_select_param(queue, (category, ))
        res = await self.cursor.fetch_one()

        if res:
            return True
        else:
            return False


    async def update_message(self, category, msg):
        queue = 'UPDATE messages SET message=%s WHERE category=%s'

        await self.cursor.query_param(queue, (msg, category, ))


    async def add_message(self, category, msg):
        queue = 'INSERT INTO messages (category, message) VALUES(%s, %s) ON CONFLICT DO NOTHING'

        await self.cursor.query_param(queue, (category, msg, ))



    # Оплата
    async def add_status_user(self, user_id, status):
        queue = 'INSERT INTO user_status(tgid, status) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (user_id, status, ))

    async def get_status_user(self, user_id):
        queue = 'SELECT status FROM user_status WHERE tgid=%s'
        await self.cursor.query_select_param(queue, (str(user_id), ))
        return await self.cursor.fetch_one()

    async def update_user_status(self, user_id, status):
        queue = 'UPDATE user_status SET status=%s WHERE tgid=%s'
        await self.cursor.query_param(queue, (status, user_id, ))

    async def add_sub_day(self, user_id):
        queue = 'INSERT INTO sub_days(tgid, days) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (user_id, 0))


    # Скриптовые сообщения
    async def get_msg(self, category):
        queue = 'SELECT message FROM messages WHERE category=%s'

        if category == '/start':
            category = 'Стартовое сообщение'
        await self.cursor.query_select_param(queue, (category, ))
        res = await self.cursor.fetch_one()

        if res:
            return res[0]
        else:
            return '...'


    # Создание профиля Firefox
    def add_user_code(self, user_id, code):
        queue = 'INSERT INTO user_codes (tgid, code) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        self.cursor.sync_query_param(queue, (str(user_id), str(code), ))


    def get_user_code(self, user_id):
        queue = 'SELECT code FROM user_codes WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id), ))
        return self.cursor.sync_fetch_one()


    def del_user_code(self, user_id):
        queue = 'DELETE FROM user_codes WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id), ))


    async def async_add_user_code(self, user_id, code):
        queue = 'INSERT INTO user_codes (tgid, code) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (str(user_id), str(code), ))


    async def async_get_user_code(self, user_id):
        queue = 'SELECT code FROM user_codes WHERE tgid=%s'
        await self.cursor.query_param(queue, (str(user_id), ))
        return await self.cursor.fetch_one()


    # CAPTCHA
    def add_user_captcha(self, user_id, captcha):
        queue = 'INSERT INTO user_captchas (tgid, captcha) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        self.cursor.sync_query_param(queue, (str(user_id), str(captcha), ))

    def get_user_captcha(self, user_id):
        queue = 'SELECT captcha FROM user_captchas WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id), ))
        return self.cursor.sync_fetch_one()

    def del_user_captcha(self, user_id):
        queue = 'DELETE FROM user_captchas WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id), ))

    async def async_add_user_captcha(self, user_id, captcha):
        queue = 'INSERT INTO user_captchas (tgid, captcha) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (str(user_id), str(captcha), ))

    async def async_get_user_captcha(self, user_id):
        queue = 'SELECT captcha FROM user_captchas WHERE tgid=%s'
        await self.cursor.query_param(queue, (str(user_id), ))
        return await self.cursor.fetch_one()


    # STATUS LINK
    async def set_link_status(self, user_id, status):
        queue = 'INSERT INTO link_status (tgid, status) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (str(user_id), str(status), ))

    def update_link_status(self, user_id, status):
        queue = 'UPDATE link_status SET status=%s WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(status), str(user_id), ))

    def sync_select_link_status(self, user_id):
        queue = 'SELECT status FROM link_status WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id), ))
        return self.cursor.sync_fetch_one()

    async def select_link_status(self, user_id):
        queue = 'SELECT status FROM link_status WHERE tgid=%s'
        await self.cursor.query_select_param(queue, (str(user_id), ))
        return await self.cursor.fetch_one()



    # EXIST PROFILE
    async def set_profile_status(self, user_id, status):
        queue = 'INSERT INTO exist_profile (tgid, status) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (str(user_id), str(status),))

    def update_profile_status(self, user_id, status):
        queue = 'UPDATE exist_profile SET status=%s WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(status), str(user_id),))

    def sync_select_profile_status(self, user_id):
        queue = 'SELECT status FROM exist_profile WHERE tgid=%s'
        self.cursor.sync_query_param(queue, (str(user_id),))
        return self.cursor.sync_fetch_one()

    async def select_profile_status(self, user_id):
        queue = 'SELECT status FROM exist_profile WHERE tgid=%s'
        await self.cursor.query_select_param(queue, (str(user_id),))
        return await self.cursor.fetch_one()



    # STATUS PARS
    async def get_status_pars(self):
        queue = 'SELECT status FROM pars_status'
        await self.cursor.query_select(queue)
        return await self.cursor.fetch_one()


    async def update_status_pars(self, status):
        queue = 'UPDATE pars_status SET status=%s'
        await self.cursor.query_param(queue, (str(status), ))



    # Browser status
    def set_browser_status(self, user_id):
        queue = 'INSERT INTO browser_status (tgid) VALUES (%s)'
        self.cursor.sync_query_param(queue, (user_id, ))


    def del_browser_status(self, user_id):
        queue = 'DELETE FROM browser_status WHERE ctid in (SELECT ctid FROM browser_status WHERE tgid=%s LIMIT 1)'
        self.cursor.sync_query_param(queue, (user_id, ))


    async def get_count_browsers(self):
        queue = 'SELECT COUNT(*) FROM browser_status'
        await self.cursor.query(queue)
        res = await self.cursor.fetch_one()
        return int(res[0])


    async def exist_count_browser(self):
        queue = 'SELECT * FROM browser_status'
        await self.cursor.query_select(queue)
        res = await self.cursor.fetch_one()
        if res:
            return True
        else:
            return False


    # PAYMENTS
    async def delete_pay_inf(self):
        queue = 'DELETE FROM payments_data'
        await self.cursor.query(queue)


    async def add_pay_inf(self, data):
        queue = 'INSERT INTO payments_data (image, price, title, description) VALUES (%s, %s, %s, %s)'
        await self.cursor.query_param(queue, data)


    async def get_pay_inf(self):
        queue = 'SELECT * FROM payments_data'
        await self.cursor.query_select(queue)
        res = await self.cursor.fetch_one()
        if res:
            return res
        else:
            return False



    # Count send
    async def add_count_send(self, user_id, count):
        queue = 'INSERT INTO count_send (tgid, count) VALUES(%s, %s) ON CONFLICT DO NOTHING'
        await self.cursor.query_param(queue, (user_id, count))


    async def get_count_send(self, user_id):
        queue = 'SELECT count FROM count_send WHERE tgid=%s'
        await self.cursor.query_select_param(queue, (user_id, ))
        res = await self.cursor.fetch_one()
        return res[0]


    async def update_count_send(self, user_id, count):
        queue = 'UPDATE count_send SET count=%s WHERE tgid=%s'
        await self.cursor.query_param(queue, (count, user_id, ))


    async def get_id_count_send(self):
        queue = 'SELECT tgid FROM count_send'
        await self.cursor.query(queue)
        return await self.cursor.fetch_many()



    # Update sub days
    async def get_sub_ids(self):
        queue = 'SELECT tgid FROM user_status WHERE status=%s'
        await self.cursor.query_select_param(queue, ('active', ))
        return await self.cursor.fetch_many()


    async def get_sub_days(self, user_id):
        queue = 'SELECT days FROM sub_days WHERE tgid=%s'
        await self.cursor.query_select_param(queue, (str(user_id), ))
        res = await self.cursor.fetch_one()
        return res[0]


    async def update_sub_days(self, user_id, days):
        queue = 'UPDATE sub_days SET days=%s WHERE tgid=%s'
        await self.cursor.query_param(queue, (int(days), str(user_id)))














