import psycopg2
from db.utils import PGSQLUtil


class DB(PGSQLUtil):
    # def insert():
    #     self.execute("insert into blocks values (%s, %s, %s, %s,%s, %s, %s, %s,%s)", (
    #         block.block_number, block.hash, block.miner, block.validator, block.gas_used, block.gas_limit,
    #         block.timestamp,
    #         block.base_fee, block.extra_data))
    pass


if __name__ == "__main__":
    pgsqlUtil = PGSQLUtil(host="127.0.0.1", user="yhliu", password="yhliu", database="mevtest")
    pgsqlUtil.get_version()
    conn = pgsqlUtil.get_conn()
    ## 查询所有数据库
    databases = pgsqlUtil.list_databases()
    print(type(databases), databases)
