import logging
import asyncio
from SqlHelper import Select, Update, Delete, execute, create_pool


class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return "<%s, %s:%s>" % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    def __init__(self, name = None, primary_key=False, default=None, ddl="varchar(100)"):
        super().__init__(name, ddl, primary_key, default)


class IntegerField(Field):
    def __init__(self, name = None, primary_key=False, default=0, ddl="bigint"):
        super().__init__(name, ddl, primary_key, 0)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False, ddl="bool"):
        super().__init__(name, ddl, primary_key, default)


class DatetimeField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl="Datetime"):
        super().__init__(name, ddl, primary_key, default)

        
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0, ddl="real"):
        super().__init__(name, ddl, primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

def create_args_string(num):
        return ",".join(["?" for i in range(num)])


class ModelMetaClass(type):
    def __new__(cls, name, bases, attrs):
        if name == "Model":
            return type.__new__(cls, name, bases, attrs)

        tableName = attrs.get("__table__", None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))

        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            if isinstance(v, Field):
                logging.info("   found mapping:%s ==> %s" % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError("Primary key not found")
        for k in mappings.keys():
            attrs.pop(k)
        escape_field = list(map(lambda f: "`%s`" % f, fields))
        attrs["__mappings__"] = mappings
        attrs["__table__"] = tableName
        attrs["__primary_key__"] = primaryKey
        attrs["__fields__"] = fields

        attrs["__select__"] = "select `%s`, `%s` from `%s` " % (primaryKey, ','.join(escape_field), tableName)
        attrs['__insert__'] = "insert into `%s` (%s, `%s`) values (%s)" % (tableName, ', '.join(escape_field), primaryKey, create_args_string(len(escape_field) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


    


class Model(dict, metaclass=ModelMetaClass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)


    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)


    def __setattr__(self, key, value):
        self[key] = value


    def getValue(self, key):
        return getattr(self, key, None)
    
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value


    
    
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows!=1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

        
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        'find object by where clause'
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderby = kw.get("orderBy", None)
        if orderby:
            sql.append("order by")
            sql.append(orderby)
        limit = kw.get("limit", None)
        if limit is not None:
            if limit is not None:
                sql.append("limit")
                if isinstance(limit, int):
                    sql.append("?")
                    args.append(limit)
                elif isinstance(limit, tuple) and len(limit) ==  2:
                    sql.append("?, ?")
                    args.append(limit)
                else:
                    raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await Select(" ".join(sql), args)
        return [cls(**r) for r in rs]


    @classmethod
    async def find(cls, pk):
        'find object by primary key'
        rs = await Select("%s where `%s`=?" % (cls.__select__, cls.__primary_key__), pk, 1)
        if len(rs) == 0 :
            return None
        else:
            cls(**rs[0])

    
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        'find number by where .'
        sql = ["select %s _num_ from `%s`" % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)
        rs = await Select(" ".join(sql), args, 1)
        if len(rs) ==0:
            return None
        else:
            return rs[0]["__num__"]
        

    # async def Update(self):
    #     args = list(map(self.getValueOrDefault, self.__fields__))   
    #     args.append(self.getValueOrDefault(self.__primary_key__))
    #     rows = await execute(self.__insert__, args)
    #     if rows != 1:
    #         logging.warn("failed to update by primary key: affected rows:%s" % rows)


    # async def remove(self):
    #     args = [self.getValue(self.__primay_key__)]
    #     rows = await execute(self.__delete__, args)
    #     if row != 1:
    #         logging.log("failed to remvote by primary key: affected rows:%s" % rows)
