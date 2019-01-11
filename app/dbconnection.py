import mysql.connector
import os
from hashlib import blake2b
import hashlib
import random
import sys


def urandom_from_random(rng, length):
    '''generate Return a string of size random bytes suitable for cryptographic use.  

    Keyword arguments:
    nrg -- random number
    length -- byte length
    '''

    if length == 0:
        return b''
    integer = rng.getrandbits(length * 8)
    result = integer.to_bytes(length, sys.byteorder)
    return result

def hashWord(word):
    '''generate a salted hash for db's id' - column  

    Keyword arguments:
    word -- string 
    '''

    random.seed(word)
    rng = random.Random(len(word))
    salt = urandom_from_random(rng, blake2b.SALT_SIZE)
    h = blake2b(salt=salt, digest_size=16)
    h.update(word.encode('utf-8'))

    return h.digest()

def connectdb():
    '''connect to mysql db and return handle 

    '''
    mydb = mysql.connector.connect(
      host="db",
      user="root",
      passwd="mypwd",
      port=3306,
      # auth_plugin='mysql_native_password',
      database="wordydb"
    )

    return mydb

def closedb(mydb):
    ''' close the db connection

    '''

    mydb.close()

    return 1

def existsTable(mydb, table):
    '''check if particular db table exists 

    Keyword arguments:
    mydb -- database handle 
    table -- string 
    '''

    cur = mydb.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(table.replace('\'', '\'\'')))
    if cur.fetchone()[0] == 1:
        cur.close()
        return True

    cur.close()
    return False

def createTable(mydb):
    '''create a db table exists 

    Keyword arguments:
    mydb -- database handle 
    '''

    cur = mydb.cursor()
    cur.execute("CREATE  TABLE wordy ( id VARBINARY(255) PRIMARY KEY, word VARBINARY(255), count SMALLINT(255))")
    mydb.commit()


def writeData(mydb, data):
    '''write data to the table  

    Keyword arguments:
    mydb -- database handle 
    data -- data dict()
    '''

    cur = mydb.cursor()
    dataStr=str()
    i = int()
    for key, value in data.items():
        sqlStr = "INSERT INTO wordy (id, word, count) VALUES (%s, AES_ENCRYPT(%s, 'foobar'), %s ) ON DUPLICATE KEY UPDATE word=%s, count=%s"
        wordHash = hashWord(key)
        dataStr = (wordHash, key, value, key, value,)
        cur.execute(sqlStr, dataStr)
        mydb.commit()
        i+=1

    return i

def readData(mydb):
    '''read data from the table  

    Keyword arguments:
    mydb -- database handle 
    '''

    cur = mydb.cursor()

    sqlStr = "SELECT AES_DECRYPT(word, 'foobar'), count FROM wordy"
    cur.execute(sqlStr)
    result={}
    result = cur.fetchall()

    return result
    

