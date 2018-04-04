import asyncio
import aiomysql
import logging
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base


def log(sql, args=()):
    logging.info('SQL: %s' % sql)


@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info("create database connection pool...")
    global __pool
    __pool = yield from aiomysql.create_pool(
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


class test(object):
    def __init__(self):
        print("i am test class")

    def __enter__(self):
        print("enter")

    def __exit__(self, exc_type, exc_value, exc_tb):
        print("exit")

    def close(self):
        print("i will be closed!!!")


@asyncio.coroutine
def Select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (yield from __pool.get()) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace("?", "%s"), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
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


# @asyncio.coroutine
# def Insert(sql, args):
#     sql = sql.upper()
#     if sql.startswith("SELECT"):
#         if ParamCount(sql) != len(args):
#             raise Exception("parameters count not right")
#         execute(sql, args)
#     else:
#         raise Exception("not select sql")

@asyncio.coroutine
def Update(sql, args):
    sql = sql.upper()
    if sql.startswith("UPDATE"):
        yield from execute(sql, args)
    else:
        raise Exception("not update sql")

@asyncio.coroutine
def Delete(sql, args):
    sql = sql.upper()
    if sql.startswith("DELETE"):
        yield from execute(sql, args)
    else:
        raise Exception("not delete sql")

def ParamCount(sql):
    count = sql.count("?")
    return count


# from orm import Model, StringField, IntegerField
# class User(Model):
#     __table__ = "users"
#     id = Column(Integer, primary_key=True)
#     name = Column(String)

