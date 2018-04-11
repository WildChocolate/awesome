import asyncio
import aiomysql
import logging
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base


def log(sql, args=()):
    logging.info('SQL: %s' % sql)



async def create_pool(loop, **kw):
    logging.info("create database connection pool...")
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['database'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


# class test(object):
#     def __init__(self):
#         print("i am test class")

#     def __enter__(self):
#         print("enter")

#     def __exit__(self, exc_type, exc_value, exc_tb):
#         print("exit")

#     def close(self):
#         print("i will be closed!!!")



async def Select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (await __pool.get()) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace("?", "%s"), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info("rows returned : %s", len(rs))
        return rs



async def execute(sql, args, autocommit=True):
    log(sql, args)
    #global __pool
    async with __pool.get() as conn:
        if not autocommit:
            await __pool.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace("?", "%s"),args)
                affected = cur.cowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await cur.rollback()
            raise
        return effected

async def Insert(sql, args):
    args = list(map(self.getValueOrDefault, self.__fields__))
    args.append(self.getValueOrDefault(self.__primary_key__))
    rows = await execute(self.__insert__, args)
    if rows != 1:
        logging.warn('failed to insert record: affected rows: %s' % rows)


async def Update(sql, args):
    args = list(map(self.getValue, self.__fields__))
    args.append(self.getValue(self.__primary_key__))
    rows = await execute(self.__update__, args)
    if rows != 1:
        logging.warn('failed to update by primary key: affected rows: %s' % rows)

async def Delete(sql, args):
    args = [self.getValue(self.__primary_key__)]
    rows = await execute(self.__delete__, args)
    if rows != 1:
        logging.warn('failed to remove by primary key: affected rows: %s' % rows)

def ParamCount(sql):
    count = sql.count("?")
    return count


# from orm import Model, StringField, IntegerField
# class User(Model):
#     __table__ = "users"
#     id = Column(Integer, primary_key=True)
#     name = Column(String)

