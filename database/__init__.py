from . import activity_table
from . import users_table
from . import products_table   
from . import join_query

class DBInterface:
    users = users_table
    activity = activity_table
    products = products_table
    join_query = join_query

db = DBInterface()