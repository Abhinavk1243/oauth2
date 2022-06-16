import configparser
import os
import mysql.connector as msc
from mysql.connector import pooling
import logging as lg 


def get_config(section,key,file):
    """Method use to read the value of key in congfig file i.e .cfg extension file

    Args:
        section (string): section name in cfg file whose value want to read
        key (string): key identification of section whose value want to read

    Returns:
        string: value of corresonding section key
    """
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.expanduser("~"),f'config/{file}'))
    return parser.get(section,key)



# def getconfig(section,key,filename):
#     """Method use to read the value of key in congfig file i.e .cfg extension file

#     Args:
#         section (string): section name in cfg file whose value want to read
#         key (string): key identification of section whose value want to read

#     Returns:
#         string: value of corresonding section key
#     """
#     parser = configparser.ConfigParser()
#     parser.read(os.path.join(os.path.expanduser("~"),'config/sqlcred.cfg'))
#     return parser.get(section,key)  

def mysql_pool_connection(section):
    """Metod is use to connect database with python 

    Returns:
        connection : mysqlconnection
    """
    dbconfig={ 
              'host' : get_config(section,"host","sqlcred.cfg"),
              'user' : get_config(section,"user","sqlcred.cfg"),
              'database' : get_config(section,"database","sqlcred.cfg"),
              'password' : get_config(section,"password","sqlcred.cfg"),  
              'auth_plugin': 'mysql_native_password'
            }
    
    cnxn = pooling.MySQLConnectionPool(pool_name = "student",**dbconfig)
    pool_cnxn=cnxn.get_connection()
    return pool_cnxn

def logger():
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)
    formatter = lg.Formatter('%(asctime)s : %(name)s : %(filename)s : %(levelname)s\
                             :%(funcName)s :%(lineno)d : %(message)s ')
    file_handler =lg.FileHandler("logsfile.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
