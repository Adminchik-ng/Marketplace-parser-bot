from calendar import c
from . import activity_table
from . import users_table
from . import products_table
from . import connection    

class DBInterface:
    users = users_table
    activity = activity_table
    products = products_table
    connection = connection

db = DBInterface()