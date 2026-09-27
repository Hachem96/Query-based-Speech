
import psycopg2
import pandas as pd
import os
import numpy as np
def connectTodatabase():
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT"))
        )
    connection.autocommit = True
    cursor = connection.cursor()
    return connection, cursor

def getVideoInfo(cursor,videoName):
    """
    function returns the information of a video from the Video table in database
    """
  

    query = 'SELECT * FROM "Video" WHERE name = %s LIMIT 1;'
    cursor.execute(query, (videoName,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))
        return row_dict
    else:
        print(f"{videoName} does not exist in database")


def compute_similarities(cursor,queryVector,video_id=-1):
    """
    Compute cosine similarity between a query embedding and
    embeddings stored in PostgreSQL/pgvector.

    Parameters
    ----------
    cursor : psycopg cursor
        PostgreSQL database cursor.
    queryVector : np.ndarray
        Query embedding vector.
    embeddingColumn : str, default="Qwen_3_7_512"
        Name of the embedding column in the "Embeddings" table.
    video_id : int, default=-1
        If video_id != -1, only chunks belonging to this video
        are returned.
        If video_id == -1, chunks from all videos are returned.

    Returns
    -------
    pd.DataFrame
            videoId
            mergedChunkId
            <embeddingColumn>
    """
    embedding_models = {
        "Qwen_3_7_1024": 1024,
        # "Qwen_3_7_1536": 1536,
        # "Qwen_3_7_2560": 2560,
    }
    embeddingColumn="Qwen_3_7_1024"
    if embeddingColumn not in embedding_models:
        raise ValueError(f"Unknown embedding model: {embeddingColumn}")

    python_vector = np.asarray(queryVector, dtype=np.float32).tolist()

    query = f'''
        SELECT
            "videoId",
            "mergedChunkId",

            -("{embeddingColumn}" <#> %s::vector)
                AS "{embeddingColumn}"

        FROM "Embeddings"
    '''

    params = [python_vector]

   
    if video_id != -1:
        query += '''WHERE "videoId" = %s'''
        params.append(video_id)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    return pd.DataFrame(rows, columns=columns)

def get_table_from_db(cursor,Table_Name, list_columns, filter_conditions=None):
    """
    Fetch data from a database table based on a list of columns and optional filter conditions.

    Parameters:
    - cursor: Database cursor connected to a PostgreSQL database.
    - Table_Name: Name of the table in the database.
    - list_columns: List of columns to extract from the table.
    - filter_conditions: Dictionary where keys are column names and values are lists of IDs/values to filter by.

    Returns:
    - Pandas DataFrame containing the requested data.
    """
    # Convert the list of columns into a properly formatted SQL string
    if(cursor ==None):
        connection, cursor = connectTodatabase()
        
    columns_str = ', '.join(f'"{col}"' for col in list_columns)

    # Base query
    query = f'SELECT {columns_str} FROM "{Table_Name}"'

    # Add filter conditions if provided
    values = []
    if filter_conditions:
        # Build WHERE clause for multiple columns and values
        conditions = []
        values = []
        for column, ids in filter_conditions.items():
            placeholders = ', '.join(['%s'] * len(ids))
            conditions.append(f'"{column}" IN ({placeholders})')
            #ids = [int(item) for item in ids]
            values.extend(ids)
        where_clause = ' AND '.join(conditions)
        query += f' WHERE {where_clause}'
    
    if values:
        cursor.execute(query, tuple(values))  # Use parameterized query for safety
    else:
        query = f'SELECT {columns_str} FROM "{Table_Name}"'
        cursor.execute(query)
    columns_data = cursor.fetchall()

    # Convert the result into a DataFrame
    table_data = pd.DataFrame(columns_data, columns=list_columns)

    return table_data