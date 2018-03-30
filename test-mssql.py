__author__ = 'ekko'
import pymysql


# 打开数据库连接
conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="123456", db="test")

cursor = conn.cursor()
sql = "create table user (id int primary key,name varchar(20));"
cursor.execute(sql)
sql = ("insert into user (id, name) values (%s,%s)")
cursor.execute(sql, ['1', 'Michael'])
print("cursor.excute:", cursor.rowcount)
conn.commit()
cursor.close()
cursor = conn.cursor()
cursor.execute("select * from user where id = %s", ("1",))
values = cursor.fetchall()
print(values)
cursor.close()
conn.close()
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User (Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))


class Book(Base):
    __tablename__ = 'book'

    id = Column(String(20), primary_key=True)
    name = Column(String(20))
    # “多”的一方的book表是通过外键关联到user表的:
    user_id = Column(String(20), ForeignKey('user.id'))


engine = create_engine('mysql+pymysql://root:123456@localhost:3306/test')
DBSession = sessionmaker(bind=engine)

session = DBSession()
new_user = User()
new_user.id = 2
new_user.name = 'jakey'
#session.add(new_user)

users = session.query(User).filter(User.id > 0).all()
for u in users:
    print("type:", type(u))
    print("name:", u.name)

session.commit()
session.close()