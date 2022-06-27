#! /usr/bin/python

tables = ['shopping', 'pharmacy', 'fridge', 'log', 'todo']
workspaces = ['cha', 'estele']


def drop_table(conn, ws='cha'):
    conn.commit()
    cur = conn.cursor()
    for each in tables:
        cur.execute('DROP TABLE IF EXISTS %s_%s' % (ws, each))


def create_table(conn, ws='cha'):
    conn.commit()
    cur = conn.cursor()
    for each in tables:
        cmd = '''CREATE TABLE %s_%s(
        id serial PRIMARY KEY,
        text TEXT NOT NULL);''' % (ws, each)
        cur.execute(cmd)
        conn.commit()


def retrieve_json(conn, ws='cha'):
    j = {}
    for table in tables:
        rows = select_table(conn, table, ws)
        print(table, rows)
        if table == 'log':
            j[table] = [e[1].split('|') for e in rows]
        else:
            j[table] = [e[1] for e in rows]
    return j


def select_table(conn, table, ws='cha'):
    conn.commit()
    cur = conn.cursor()
    cmd = 'SELECT * from %s_%s;' % (ws, table)
    cur.execute(cmd)
    rows = cur.fetchall()
    return rows


def insert_tables(conn, j, ws='cha'):
    conn.commit()
    cur = conn.cursor()
    print(j)
    for table in tables:
        if table == 'log':
            for i, each in enumerate(j[table]):
                cmd = 'INSERT INTO %s_%s (id, text)'\
                      'VALUES (%s, \'%s\')' % (ws, table, i, '|'.join(each))
                cur.execute(cmd)
                conn.commit()

        else:
            for i, each in enumerate(j[table]):
                cmd = 'INSERT INTO %s_%s (id, text)'\
                      'VALUES (%s, \'%s\')' % (ws, table, i, each)
                cur.execute(cmd)
                conn.commit()


def create_connection():
    import psycopg2
    import os
    from urllib.parse import urlparse
    url = os.environ['DATABASE_URL']

    result = urlparse(url)
    conn = psycopg2.connect(database=result.path[1:],
                            user=result.username,
                            password=result.password,
                            host=result.hostname,
                            port=result.port)
    conn.commit()
    return conn


def dump_to_db(j, ws='cha'):
    conn = create_connection()
    drop_table(conn, ws)
    create_table(conn, ws)
    insert_tables(conn, j, ws)


def dump_to_json(ws='cha'):
    conn = create_connection()
    if ws != '*':
        j = retrieve_json(conn, ws)
    else:
        j = {}
        for e in workspaces:
            j[e] = retrieve_json(conn, e)
    return j
