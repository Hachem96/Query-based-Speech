
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import Json
from pgvector.psycopg2 import register_vector
from pgvector import Vector

load_dotenv()

def create_database():
    """
    function to create a database and add the pgvector extenstion to the database
    configuration: dictionary contains connection info (database name, port, password and host)
    """
    print("Create a New PostgreSQL Database")
    #db_name = input("Enter the name of the new database: ").strip()
    #password = input("Enter your PostgreSQL password: ").strip()

    try:
    # Connect to the *default* database first
        connection = psycopg2.connect(
            dbname="postgres",   # <-- connect to existing database
            user="postgres",
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        connection.autocommit = True
        cursor = connection.cursor()
        db_name = os.getenv("DB_NAME")
        # Create the new database
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"Database '{db_name}' was created successfully!")
        cursor.close()
        connection.close()

        # ---- Connect to the newly created database and enable pgvector ----

        new_conn = psycopg2.connect(
            dbname=db_name,
            user="postgres",
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        new_conn.autocommit = True
        new_cursor = new_conn.cursor()

        # Create the vector extension
        new_cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        new_cursor.close()
        new_conn.close()
    except Exception as e:
        print("An error occurred while creating the database:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
  
            connection.close()

def connectTodatabase():
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
        )
    connection.autocommit = True
    cursor = connection.cursor()
    return connection, cursor


def create_table(table_name,columnsInfo):
    """
    function to create a table in database
    configuration: connection info to the database
    table_name
    columnsInfo: a dictionary:
                keys: columns names
                values: columns types
    """
    print(f"Create {table_name} Table in an Existing Database")

    

    # Split and clean column names
    #columns = [col.strip() for col in columns_input.split(",") if col.strip()]
    
    try:
        connection, cursor = connectTodatabase()

        column_defs =  [sql.SQL("{} SERIAL PRIMARY KEY").format(sql.Identifier("id"))]

        # Add user-defined columns
        for col, col_info in columnsInfo.items():
             # when len=3 --> ("INTEGER", "Video", "id"): column is a reference to a column in another table
             if isinstance(col_info, tuple) and len(col_info) == 3:
                col_type, ref_table, ref_col = col_info
                column_defs.append(
                    sql.SQL("{} {} REFERENCES {}({})").format(
                        sql.Identifier(col),
                        sql.SQL(col_type),
                        sql.Identifier(ref_table),
                        sql.Identifier(ref_col)
                    )
                )
             else:
                # regular column without reference
                column_defs.append(
                    sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(col_info))
                )

        query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(column_defs)
        )

        # Execute and close
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Table '{table_name}' created successfully.")

    except Exception as e:
            print("Error while creating the table:", e)

def videoIsExist(videoName):
    connection, cursor = connectTodatabase()
    check_query = 'SELECT 1 FROM "Video" WHERE name = %s LIMIT 1;'
    cursor.execute(check_query, (videoName,))
    exists = cursor.fetchone()

    if exists:
        return True
    else:
        return False
   

def add_row(table_name,columnValues):
    """
    function to add a row to a database
    Input
        configuration: connection info to the database
        table_name
        columnValues: dictionary (keys: columns names, values: values of columns to be added)
    Output
        id of the new added row
    """
    
    print(f"Add a Row to  {table_name} Table")

   
    try:
        connection, cursor = connectTodatabase()

        register_vector(connection)

        # Process column values
        for k, v in columnValues.items():
            if isinstance(v, dict):
                columnValues[k] = Json(v)

            elif isinstance(v, list):
                # Treat list as a vector
                columnValues[k] = Vector(v)

            # Otherwise keep as-is (str, int, float, etc.)

        columns = list(columnValues.keys())
        values = list(columnValues.values())

        # NOTE: the caller (processVideo/addNewVideo.add_new_video) already checks
        # for a duplicate video name via videoIsExist() before reaching here.

        # Build the INSERT query dynamically
        insert_query = sql.SQL(
                            "INSERT INTO {} ({}) VALUES ({}) RETURNING id"
                        ).format(
                            sql.Identifier(table_name),
                            sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                            sql.SQL(", ").join(sql.Placeholder() for _ in columns)
                        )

        cursor.execute(insert_query, values)
        
        new_id = cursor.fetchone()[0] 
        connection.commit()
        print(f"Row added successfully to table '{table_name}'")
        return new_id
    except Exception as e:
        print("Error while adding row:", e)

    
        
def delete_row(table_name,columnCondition):
    """
    function to deete a row to a database
    Input
        configuration: connection info to the database
        table_name
        columnCondition: dictionary 
                            key: columns name, 
                            value: values of column to be used to select the row to be deleted)
   
    """

    print("Delete a Row from a Table")

    column_name = columnCondition["columnName"]
    value = columnCondition["value"]

    try:
        connection, cursor = connectTodatabase()

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

def update_value(table_name,filterColumn,targetColumn):
    """
    function to change the value of a column in a given row 
    Input
        configuration: connection info to the database
        table_name
        filterColumn: key: column name to be used to select the row
                      value: value of column
        targetColumn: key: column name that we want to change its value
                      value: new value 
    """
    print("Update a Column Value")

  
    search_col = filterColumn["columnName"]
    search_val = filterColumn["value"]
    target_col = targetColumn["columnName"]
    new_val = targetColumn["value"]

    try:
        connection, cursor = connectTodatabase()

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

def add_column(table_name,column_name,column_type):
    """
    function to add a column to a table in datatabase
    """
    print(f"Add a New Column {column_name} to {table_name} Table")

   

    try:
        connection, cursor = connectTodatabase()

        add_column_query = sql.SQL("ALTER TABLE {} ADD COLUMN {} TEXT").format(
        sql.Identifier(table_name),
        sql.Identifier(column_name),
        sql.SQL(column_type)
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

def delete_column(table_name,columnName):

    print(f"Delete {columnName} Column from {table_name} Table")

   

    try:
        connection, cursor = connectTodatabase()

        query = sql.SQL("ALTER TABLE {} DROP COLUMN IF EXISTS {}").format(
            sql.Identifier(table_name), sql.Identifier(columnName)
        )
        cursor.execute(query)
        print(f"Column '{columnName}' deleted successfully!")

    except Exception as e:
        print("Error while deleting column:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def creat_db_tables():
    """
    function to create the four tables in the database of project
        confiuration: conneciton info to the database
    the four tables are: video, initialChunks, mergedChunks, embeddings
    column names and types of each table are defined inside the function

    """
    # create video table
    videoColumnsInfo = {
    "name": "TEXT",
    "year": "INTEGER",
    "caption": "TEXT",
    "subject": "TEXT",
    "linkToCover": "TEXT",
    "linkToMP4": "TEXT",
    "linkToMP3": "TEXT",
    "fullTranscriptionPath": "TEXT",
    "linkToPdf": "TEXT",
    "linkToSummaryPdf": "TEXT",
    "correctedTranscriptionPath": "TEXT",
    "linkToTranslation": "TEXT"
}
   
    table_name = "Video"
    create_table(table_name,videoColumnsInfo)

    # create initial chunk table
    chunkColumnsInfo = {
    "videoId": ("INTEGER", "Video", "id"),   # adjust table name if needed
    "number": "INTEGER",
    "text": "TEXT",
    "startTimeStamp": "DOUBLE PRECISION",
    "endTimeStamp": "DOUBLE PRECISION",
    "duration": "DOUBLE PRECISION",
    "speaker": "TEXT"
}

    table_name = "InitialChunks"
    create_table(table_name,chunkColumnsInfo)

    # create merged chunk table
    mergedChunkColumnsInfo = {
    "videoId": ("INTEGER", "Video", "id"),   # adjust parent table name if needed
    "number": "INTEGER",
    "InitialChunkNumber": "vector",                # list of integer IDs
    "text": "TEXT",
    "startTimeStamp": "DOUBLE PRECISION",
    "endTimeStamp": "DOUBLE PRECISION",
    "speaker": "TEXT"
}
    table_name = "MergedChunks"
    create_table(table_name,mergedChunkColumnsInfo)

    # 
    embeddingTableInfo = {
        "mergedChunkId": ("INTEGER", "MergedChunks", "id"),
        "videoId": ("INTEGER", "Video", "id"),
        "Qwen-0.6B": "vector(1024)" 
    }
    table_name = "Embeddings"
    create_table(table_name,embeddingTableInfo)
    # 
    # add book table
    bookTableInfo = {
        "Title": "TEXT",
        "linkToPdf": "TEXT",
        "linkToCover": "TEXT",
        "caption": "TEXT",
        "Author": "TEXT",
        "Year": "INTEGER"
    }
    table_name = "Book"
    create_table(table_name,bookTableInfo)
    return
if __name__ == "__main__":
    #create_database()
    
    create_database()
    creat_db_tables()
   
    table_name = "Video"
    column_name = "Summary"
    column_type = "TEXT"
    #delete_column(db_name,password,table_name,column_name,host="172.22.112.1")
    #add_column(db_name,password,table_name,column_name,column_type,host="172.22.112.1")
    # filterColumn = {"columnName":"id",
    #                 "value": 1}
    # targetColumn = {"columnName":"linkToMP3",
    #                 "value": "text"}
    # update_value(db_name,password,table_name,filterColumn,targetColumn,host="172.22.112.1")