import orm
import SqlHelper
from models import User, Blog, Comment

def test():
    yield from SqlHelper.create_pool(None,user="www-data", password="www-data", database="awesome")
    u = User(name="test", email="test@example.com", password="123456", image="about:blank")
    yield from u.save()


for x in test():
    pass