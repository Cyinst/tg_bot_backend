from datetime import datetime
from db.utils import PGSQLUtil
from datetime import datetime


class DB(PGSQLUtil):
    def insert_user(self, user_id: int, passwd_d: str = None, reg_date=None):
        if not reg_date:
            reg_date = datetime.now().strftime('%Y-%m-%d')
        if not passwd_d:
            passwd_d = 'null'
        self.execute(f"INSERT INTO user_info(user_id, passwd_d, reg_date) SELECT {user_id}, {passwd_d}, '{reg_date}' WHERE NOT EXISTS (SELECT user_id FROM user_info WHERE user_id = {user_id})")
    
    def insert_wallet(self, user_id: int, private_key_e: str, address: str, nonce: str, create_date=None, wallet_id: int = None):
        if not create_date:
            create_date = datetime.now().strftime('%Y-%m-%d')
        if not wallet_id:
            wallet_id = 'null'
        self.execute(f"insert into wallet(address, private_key_e, nonce, create_date, wallet_id, user_id) SELECT '{address}', '{private_key_e}', '{nonce}', '{create_date}', {wallet_id}, {user_id} WHERE NOT EXISTS (SELECT address FROM wallet WHERE address = '{address}')")

    def insert_predict(self, poll_id: str, chat_id: int, user_id: int, first_name: str, answer: int, predict_time: datetime = None):
        self.execute("insert into predict (poll_id, chat_id, user_id, first_name, answer) values (%s, %s, %s, %s, %s)", (poll_id, chat_id, user_id, first_name, answer))
    
    def insert_balance(self, user_id: int, address: str, balance: float, eth_balance: float, btc_balance: float, usdc_balance: float, usdt_balance: float, date = None):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        self.execute("insert into balance (user_id, address, balance, eth_balance, btc_balance, usdc_balance, usdt_balance, date) values (%s, %s, %s, %s, %s, %s, %s, %s)", (user_id, address, balance, eth_balance, btc_balance, usdc_balance, usdt_balance, date))
    
    def insert_poll(self, poll_id: str, chat_id: int, message_id: int, start_price: float, coin: str, chain: str, settle_poll_time, expire_poll_time, create_time: datetime = None):
        self.execute("insert into poll (poll_id, chat_id, message_id, start_price, coin, chain, settle_poll_time, expire_poll_time) values (%s, %s, %s, %s, %s, %s, %s, %s)", (poll_id, chat_id, message_id, start_price, coin, chain, settle_poll_time, expire_poll_time))

    def insert_group(self, chat_id: int, kol_id: int, ticket: int, wake_date: datetime = None):
        if not wake_date:
            wake_date = datetime.now().strftime('%Y-%m-%d')
        self.execute(f"INSERT INTO groups(chat_id, kol_id, ticket, wake_date) SELECT {chat_id}, {kol_id}, {ticket}, '{wake_date}' WHERE NOT EXISTS (SELECT chat_id FROM groups WHERE chat_id = {chat_id})")
    
    def insert_user_to_top_groups_user(self, user_id: int, chat_id: int, reg_date=None):
        if not reg_date:
            reg_date = datetime.now().strftime('%Y-%m-%d')
        self.execute(f"INSERT INTO top_groups_user(user_id, chat_id, reg_date) SELECT {user_id}, {chat_id}, '{reg_date}' WHERE NOT EXISTS (SELECT user_id FROM top_groups_user WHERE user_id = {user_id})")
    
    def fetch_all_user_from_top_groups_user(self):
        results = self.query(f"select user_id,chat_id from top_groups_user")
        return results
    
    def fetch_user_from_top_groups_user(self, user_id: int):
        results = self.query(f"select user_id from top_groups_user where user_id = {user_id} and status = True")
        return results

    def fetch_from_poll_by_settle_time(self):
        results = self.query(f"select poll_id, chat_id, message_id, coin, chain, start_price from poll where current_time >= settle_poll_time")
        return results
    
    def fetch_from_poll_by_poll_id_and_chat_id(self, poll_id, chat_id):
        results = self.query(f"select expire_poll_time from poll where poll_id='{poll_id}' and chat_id={chat_id}")
        return results
    
    def fetch_expire_and_chat_from_poll_by_poll_id(self, poll_id):
        results = self.query(f"select expire_poll_time,chat_id from poll where poll_id='{poll_id}'")
        return results
    
    def fetch_expire_and_chat_and_mag_from_poll_by_poll_id(self, poll_id):
        results = self.query(f"select expire_poll_time,chat_id,message_id from poll where poll_id='{poll_id}'")
        return results

    def fetch_from_poll(self):
        results = self.query(f"select poll_id, chat_id, message_id, coin, chain, start_price from poll")
        return results
    
    def fetch_user_from_predict_by_poll_id_and_chat_id_and_answer(self, poll_id: str, chat_id: int, answer: int):
        results = self.query(f"select user_id, first_name from predict where poll_id='{poll_id}' and chat_id={chat_id} and answer={answer}")
        return results
    
    def fetch_groups_tickets_by_user_id(self, user_id: int):
        results = self.query(f"select chat_id, ticket, kol_id from group_member where user_id={user_id}")
        return results
    
    def fetch_point_by_user_id(self, user_id: int):
        results = self.query(f"select point,point_type from point where user_id={user_id}")
        return results
    
    def fetch_all_address_from_user_id(self, user_id: int):
        results = self.query(f"select address from wallet where user_id={user_id} and status=True")
        return results
    
    def fetch_all_address(self):
        results = self.query(f"select address,user_id from wallet where status=True")
        return results
    
    def fetch_unused_address_from_user_id(self, user_id: int):
        results = self.query(f"select address from wallet where user_id={user_id} and used = False")
        return results
    
    def fetch_group_user_point(self, chat_id: int):
        results = self.query(f"select point.point, point.user_id from point where group_member.chat_id = {chat_id} inner join group_member on point.user_id = group_member.user_id")
        return results
    
    def set_used_address(self,user_id:int,address:str,joined_strategy_id:int):
        self.execute(f"update wallet set used = true,joined_strategy_id={joined_strategy_id} where user_id={user_id} and address='{address}'")
        
    def set_unused_address(self,user_id:int,address:str):
        self.execute(f"update wallet set used = false,joined_strategy_id=NULL where user_id={user_id} and address='{address}'")
    
    def fetch_all_address_and_key_from_user_id(self, user_id: int):
        results = self.query(f"select address,private_key_e,nonce from wallet where user_id={user_id} and status=True")
        return results
    
    def fetch_key_by_address(self, address: str):
        results = self.query(f"select private_key_e,nonce from wallet where address='{address}' and status=True")
        return results
    
    def fetch_balance_by_address(self, address: str):
        results = self.query(f"select balance from balance where address='{address}'")
        return results
    
    def fetch_passwd_from_user_id(self, user_id: int):
        results = self.query(f"select * from user_info where user_id={user_id}")
        return results
    
    def fetch_address_from_user_by_id(self, user_id: int):
        results = self.query(f"select address from user_info where user_id={user_id}")
        return results
    
    def delete_address_from_wallet(self, address: str):
        self.execute(f"update wallet set status=False where address='{address}'")
        return None

    def delete_user_from_top_groups_user(self, user_id: int):
        self.execute(f"delete from top_groups_user where user_id = {user_id}")
        return None
    
    def delete_from_poll_by_poll_id_and_chat_id(self, poll_id: str, chat_id: int):
        self.execute(f"delete from poll where poll_id='{poll_id}' and chat_id={chat_id}")
        return None
    
    def delete_from_predict_by_poll_id_and_chat_id(self, poll_id: str, chat_id: int):
        self.execute(f"delete from predict where poll_id='{poll_id}' and chat_id={chat_id}")
        return None
    
    def set_address_from_user_by_user_id(self, user_id: int, address: str):
        self.execute(f"update user_info set address='{address}' where user_id={user_id}")
        return None
    
    def create_strategy(self,kol_user_id:int,kol_wallet_id:int):
        # CREATE TABLE STRATEGY(
        #   STRATEGY_ID SERIAL PRIMARY KEY  NOT NULL ,
        #   DEX char(20),
        #   CHAIN char(20),
        #   DEX_ADDRESS char(40),
        #   COIN CHAR(20), 
        #   COIN_ADDRESS(40),
        #   BASE_COIN_CHAR(20),
        #   BASE_ADDRESS(40)
        #   RATE INT,
        #   KOL_USER_ID INT NOT NULL,
        #   KOL_WALLET_ADDRESS CHAR(40) NOT NULL,
        #   JOINED_WALLETS TEXT  NOT NULL
        # );
        # JOINED_WALLETS = [{"wallet_id":235,"address":"0xAD1...."，"user_id":134}]
        #    
        #   
        # INSERT INTO STRATEGY (...) VALUES (...);
        # INSERT INTO STRATEGY(KOL_USER_ID,KOL_WALLET_ADDRESS,JOINED_WALLETS) VALUES (5705864725,'875ccF02e082b985979d1Ef2e3b82d36338e0C9A','[]')
        # insert into predict (poll_id, chat_id, user_id, first_name, answer) values (%s, %s, %s, %s, %s)", (poll_id, chat_id, user_id, first_name, answer)
        self.execute(f"INSERT INTO STRATEGY (KOL_USER_ID,KOL_WALLET_ADDRESS,JOINED_WALLETS) VALUES({kol_user_id},{kol_wallet_id},'[]')")
        return None
    
    def fetch_all_strategy(self):
        results = self.query(f"select * from strategy")
        return results
    
    def lock_strategy(self):
        result = self.query(f"select * from strategy for UPDATE")
        return result
    
    def create_wallet_equity_snapshot(self,date:int,address:str,equity:float):
        # CREATE TABLE EQUITY_SNAPSHOT(
        #   SNAP_SHOT_ID SERIAL PRIMARY KEY  NOT NULL ,
        #   WALLET_ADDRESS char(40),
        #   DATE_TIMESTAMP BIGINT,
        #   EQUITY decimal,
        #   COINS TEXT
        # );
        self.execute(f"INSERT INTO EQUITY_SNAPSHOT(WALLET_ADDRESS,DATE_TIMESTAMP,EQUITY,COINS) VALUES('{address}',{date},{equity},'[]')")
        return None


    def get_wallet_equity_snapshot(self,date:int,address:str):
        # CREATE TABLE EQUITY_SNAPSHOT(
        #   SNAP_SHOT_ID SERIAL PRIMARY KEY  NOT NULL ,
        #   WALLET_ADDRESS char(40),
        #   DATE_TIMESTAMP BIGINT,
        #   EQUITY decimal,
        #   COINS TEXT
        # );
        results = self.query(f"select SNAP_SHOT_ID,WALLET_ADDRESS,DATE_TIMESTAMP,EQUITY,COINS from EQUITY_SNAPSHOT where wallet_address = '{address}'")
        return results

if __name__ == "__main__":
    pgsqlUtil = DB(host="signalswap-bot-test.cunk2uzuy88s.ap-northeast-1.rds.amazonaws.com", user="postgres", password="m8iaSUrhBLcsLpLaCmHY", database="users")
    print(pgsqlUtil.get_version())
    conn = pgsqlUtil.get_conn()
    ## 查询所有数据库
    databases = pgsqlUtil.list_databases()
    print(type(databases), databases)

    # pgsqlUtil.insert_user(0, b"\x00")
    # print(pgsqlUtil.fetch_address_from_user_by_id(0)[0][0])

    # pgsqlUtil.insert_wallet(user_id=0, address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", private_key_e=b'\x95\xbfs\xc2\xd3E\xc6\xf7\x0e\xa2m\x85Q_\xd5\x9f4\xb4*\x11+\x14V1&g\xab-\xbb&\xfcr'.hex(), nonce=b'\xec\x83;x\xf0O|\x94\x98E\x9ej\xc4\xcfBm'.hex())
    # print(pgsqlUtil.fetch_all_address_and_key_from_user_id(0))
    
    pgsqlUtil.get_conn().commit()