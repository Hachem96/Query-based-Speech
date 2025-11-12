
import psycopg2
from psycopg2 import sql

def create_database():
    
    print("Create a New PostgreSQL Database")
    db_name = input("Enter the name of the new database: ").strip()
    password = input("Enter your PostgreSQL password: ").strip()

    try:
    # Connect to the *default* database first
        connection = psycopg2.connect(
            dbname="postgres",   # <-- connect to existing database
            user="postgres",
            password=password,
            host="localhost",
            port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        # Create the new database
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"Database '{db_name}' was created successfully!")

    except Exception as e:
        print("An error occurred while creating the database:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def create_table():

    print("Create a Table in an Existing Database")

    db_name = input("Enter database name: ").strip()
    password = input("Enter PostgreSQL password: ").strip()
    table_name = input("Enter new table name: ").strip()
    columns_input = input("Enter column names (comma separated): ").strip()

    # Split and clean column names
    columns = [col.strip() for col in columns_input.split(",") if col.strip()]

    try:
        connection = psycopg2.connect(
        dbname=db_name,
        user="postgres",
        password=password,
        host="localhost",
        port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        # Build the CREATE TABLE query
        all_columns = ["id SERIAL PRIMARY KEY"] + [f"{col} TEXT" for col in columns]
        create_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.SQL(c) for c in all_columns))

        cursor.execute(create_query)
        print(f"Table '{table_name}' created successfully in database '{db_name}'!")

    except Exception as e:
        print("Error while creating the table:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def add_row():
    
    print("Add a Row to a Table")

    db_name = input("Enter the database name: ").strip()
    password = input("Enter your PostgreSQL password: ").strip()
    table_name = input("Enter the table name: ").strip()

    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user="postgres",
            password=password,
            host="localhost",
            port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name <> 'id'
            ORDER BY ordinal_position;
        """, (table_name,))
        columns = [r[0] for r in cursor.fetchall()]

        if not columns:
            print(f"Table '{table_name}' not found or has no columns.")
            return

        # ask user for a value for each column
        print("\nEnter values for each column:")
        values = [input(f"{col}: ").strip() for col in columns]

        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() * len(columns))
        )
        cursor.execute(insert_query, values)

        print(f"Row added successfully to table '{table_name}' in database '{db_name}'!")

    except Exception as e:
        print("Error while adding row:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        
def delete_row():

    print("Delete a Row from a Table")

    db_name = input("Enter the database name: ").strip()
    password = input("Enter your PostgreSQL password: ").strip()
    table_name = input("Enter the table name: ").strip()
    column_name = input("Enter the column name for the condition: ").strip()
    value = input("Enter the value to match for deletion: ").strip()

    try:
        connection = psycopg2.connect(
        dbname=db_name,
        user="postgres",
        password=password,
        host="localhost",
        port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        delete_query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
        sql.Identifier(table_name),
        sql.Identifier(column_name)
        )

        cursor.execute(delete_query, (value,))
        deleted_count = cursor.rowcount  # how many rows were deleted

        if deleted_count > 0:
            print(f"Deleted {deleted_count} row(s) from '{table_name}' where {column_name} = '{value}'.")
        else:
            print(f"No rows found in '{table_name}' with {column_name} = '{value}'.")

    except Exception as e:
        print("Error while deleting row:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def update_value():

    print("Update a Column Value")

    db_name = input("Enter database name: ").strip()
    password = input("Enter PostgreSQL password: ").strip()
    table_name = input("Enter table name: ").strip()
    search_col = input("Enter column to search by (id or name): ").strip()
    search_val = input(f"Enter value for '{search_col}': ").strip()
    target_col = input("Enter column to update: ").strip()
    new_val = input(f"Enter new value for '{target_col}': ").strip()

    try:
        connection = psycopg2.connect(
        dbname=db_name,
        user="postgres",
        password=password,
        host="localhost",
        port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        update_query = sql.SQL("UPDATE {} SET {} = %s WHERE {} = %s").format(
        sql.Identifier(table_name),
        sql.Identifier(target_col),
        sql.Identifier(search_col)
        )

        cursor.execute(update_query, (new_val, search_val))
        updated_rows = cursor.rowcount

        if updated_rows > 0:
            print(f"Successfully updated {updated_rows} row(s) in '{table_name}'.")
        else:
            print(f"No matching row found where {search_col} = '{search_val}'.")

    except Exception as e:
        print("Error while updating value:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def add_column():

    print("Add a New Column to a Table")

    db_name = input("Enter the database name: ").strip()
    password = input("Enter your PostgreSQL password: ").strip()
    table_name = input("Enter the table name: ").strip()
    column_name = input("Enter the new column name to add: ").strip()

    try:
        connection = psycopg2.connect(
        dbname=db_name,
        user="postgres",
        password=password,
        host="localhost",
        port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        add_column_query = sql.SQL("ALTER TABLE {} ADD COLUMN {} TEXT").format(
        sql.Identifier(table_name),
        sql.Identifier(column_name)
        )

        cursor.execute(add_column_query)
        print(f"Column '{column_name}' added successfully to table '{table_name}' in database '{db_name}'!")
        print("All existing rows now have empty (NULL) values for this column.")

    except psycopg2.errors.DuplicateColumn:
        print(f"Column '{column_name}' already exists in table '{table_name}'. No changes made.")

    except Exception as e:
        print("Error while adding the column:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def delete_column():

    print("Delete a Column from a Table")

    db_name = input("Enter database name: ").strip()
    password = input("Enter PostgreSQL password: ").strip()
    table_name = input("Enter table name: ").strip()
    column = input("Enter column name to delete: ").strip()

    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user="postgres",
            password=password,
            host="localhost",
            port=5432
        )
        connection.autocommit = True
        cursor = connection.cursor()

        query = sql.SQL("ALTER TABLE {} DROP COLUMN IF EXISTS {}").format(
            sql.Identifier(table_name), sql.Identifier(column)
        )
        cursor.execute(query)
        print(f"Column '{column}' deleted successfully!")

    except Exception as e:
        print("Error while deleting column:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    # create_database()
    create_table()
    # add_row()
    # add_row()
    # add_row()
    # add_column()
    # delete_column()
    # update_value()
    # delete_row()
    
