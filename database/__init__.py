from . import activity_table
from . import users_table
from . import products_table   

class DBInterface:
    users = users_table
    activity = activity_table
    products = products_table

db = DBInterface()