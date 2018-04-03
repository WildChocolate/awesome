import orm
import SqlHelper
from models import User, Blog, Comment
import asyncio

def test():
    loop = asyncio.get_event_loop()
    yield from SqlHelper.create_pool(loop, user="www-data", password="www-data", database="awesome")
    u = User(name="test", email="test@example.com", password="123456", image="about:blank")
    yield from u.save()


for x in test():
    pass