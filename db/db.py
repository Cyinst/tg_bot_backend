from datetime import datetime
from db.utils import PGSQLUtil
from datetime import datetime


class DB(PGSQLUtil):
    def insert_user(self, user_id: int, passwd_d: str, reg_date=None):
        if not reg_date:
            reg_date = datetime.now().strftime('%Y-%m-%d')
        self.execute("insert into user_info values (%s, %s, %s)", (user_id, passwd_d, reg_date))
    
    def insert_wallet(self, user_id: int, private_key_e: str, address: str, nonce: str, create_date=None, wallet_id: int = None):
        if not create_date:
            create_date = datetime.now().strftime('%Y-%m-%d')
        self.execute("insert into wallet values (%s, %s, %s, %s,%s, %s)", (address, private_key_e, nonce, create_date, wallet_id, user_id))

    def insert_predict(self, poll_id: str, chat_id: int, user_id: int, answer: int, predict_time: datetime = None):
        self.execute("insert into predict (poll_id, chat_id, user_id, answer) values (%s, %s, %s, %s)", (poll_id, chat_id, user_id, answer))
    
    def insert_poll(self, poll_id: str, chat_id: int, message_id: int, start_price: float, coin: str, chain: str, settle_poll_time, expire_poll_time, create_time: datetime = None):
        self.execute("insert into poll (poll_id, chat_id, message_id, start_price, coin, chain, settle_poll_time, expire_poll_time) values (%s, %s, %s, %s, %s, %s, %s, %s)", (poll_id, chat_id, message_id, start_price, coin, chain, settle_poll_time, expire_poll_time))

    def fetch_from_poll_by_settle_time(self):
        results = self.query(f"select poll_id, chat_id, message_id, coin, chain, start_price from poll where current_time >= settle_poll_time")
        return results
    
    def fetch_from_poll(self):
        results = self.query(f"select poll_id, chat_id, message_id, coin, chain, start_price from poll")
        return results
    
    def fetch_all_address_from_user_id(self, user_id: int):
        results = self.query(f"select address from wallet where user_id={user_id} and status=True")
        return results
    
    def fetch_all_address_and_key_from_user_id(self, user_id: int):
        results = self.query(f"select address,private_key_e,nonce from wallet where user_id={user_id} and status=True")
        return results
    
    def fetch_passwd_from_user_id(self, user_id: int):
        results = self.query(f"select * from user_info where user_id={user_id}")
        return results
    
    def delete_address_from_wallet(self, address: str):
        self.execute(f"update wallet set status=False where address='{address}'")
        return None


if __name__ == "__main__":
    pgsqlUtil = DB(host="signalswap-bot-test.cunk2uzuy88s.ap-northeast-1.rds.amazonaws.com", user="postgres", password="m8iaSUrhBLcsLpLaCmHY", database="users")
    print(pgsqlUtil.get_version())
    conn = pgsqlUtil.get_conn()
    ## 查询所有数据库
    databases = pgsqlUtil.list_databases()
    print(type(databases), databases)

    # pgsqlUtil.insert_user(0, b"\x00")
    print(pgsqlUtil.fetch_passwd_from_user_id(0)[0])

    pgsqlUtil.insert_wallet(user_id=0, address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", private_key_e=b'\x95\xbfs\xc2\xd3E\xc6\xf7\x0e\xa2m\x85Q_\xd5\x9f4\xb4*\x11+\x14V1&g\xab-\xbb&\xfcr'.hex(), nonce=b'\xec\x83;x\xf0O|\x94\x98E\x9ej\xc4\xcfBm'.hex())
    print(pgsqlUtil.fetch_all_address_and_key_from_user_id(0))

    pgsqlUtil.get_conn().commit()