import psycopg2


conn = psycopg2.connect(dbname='blog_db', user='postgres', 
                        password='12345', host='localhost')

cursor = conn.cursor()

a = cursor.execute('SELECT *FROM users;')

cursor.close()
conn.close()