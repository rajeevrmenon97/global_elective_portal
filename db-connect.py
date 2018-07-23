import psycopg2
import sys

def main():
    try:
        conn = psycopg2.connect("dbname='global_elective_portal' user='devika' host=gep_db password='devika123'")
        conn.close()
    except psycopg2.OperationalError as ex:
        print("Connection failed: {0}".format(ex))
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
