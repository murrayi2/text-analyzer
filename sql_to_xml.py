import sqlite3
from sqlite3 import Error
import xml.etree.ElementTree as xml

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def attach_contacts(conn):
    cur = conn.cursor()
    attachDatabaseSQL = "ATTACH DATABASE ? AS contacts_db"
    dbSpec  = ("contacts.db",)
    cur.execute(attachDatabaseSQL,dbSpec)

def select_all(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("DROP TABLE if exists all_contacts")
    cur.execute("CREATE TABLE all_contacts as SELECT first, last, organization, replace(replace(replace(replace(replace(replace(value,'+1', ''), '(', ''), ')', ''), '-', ''), char(32), ''), char(160), '') as number from contacts_db.ABMultiValue mv join contacts_db.ABPerson p on mv.record_id=p.ROWID")
    cur.execute("SELECT datetime(substr(date, 1, 9) + 978307200, 'unixepoch', 'localtime') as date, h.id as number, c.first, c.last, c.organization, is_from_me as type, text FROM handle h left join all_contacts c ON c.number = replace(h.id, '+1', '') join message m on m.handle_id = h.ROWID ORDER BY m.rowid DESC")
    rows = cur.fetchall()
    l = []
    for row in rows:
        d = {}
        if row[2] or row[3]:
            d["contact_name"] = row[2] + " " + row[3]
        else:
            d["contact_name"] = row[1]

        d["body"] = row[6]
        d["readable_date"] = row[0]
        d["address"] = row[1]
        if row[5] == 1:
            d["type"] = 1
        elif row[5] == 0:
            d["type"] = 2
        else:
            d["type"] = -1

        l.append(d)

    return l

def dict_to_xml(dicts):
    root = xml.Element("smses")
    for d in dicts:
        sms = xml.SubElement(root, "sms")
        for k,v in d.items():
            sms.set(k,str(v))

    tree = xml.ElementTree(root)
    tree.write(open('texts.xml', 'w'), encoding='unicode')

def main():
    database = r"messages.db"

    # create a database connection
    conn = create_connection(database)
    attach_contacts(conn)

    with conn:
        messages = select_all(conn)
        dict_to_xml(messages)
    conn.close()

if __name__ == '__main__':
    main()
