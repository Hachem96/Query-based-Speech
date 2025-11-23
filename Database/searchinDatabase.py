
from Database.DataBaseFunctions import connectTodatabase
import pandas as pd

def getVideoInfo(videoName,configuration):
    """
    function returns the information of a video from the Video table in database
    """
    connction, cursor = connectTodatabase(configuration)

    query = 'SELECT * FROM "Video" WHERE name = %s LIMIT 1;'
    cursor.execute(query, (videoName,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))
        return row_dict
    else:
        print(f"{videoName} does not exist in database")


def compute_similarities(cursor,video_id, queryVectors):
    """
    function computes similarities vectors beween the embedding of chunk
    and the embeddings of the chunks of one video 
    we have three embedding models
    Input
        cursor
        video_id
        queryVectors(3): list of three vectors
                        the embeddings of query obtained by three models
    Output:
        df: dataframe (mergedChunkId, 3 similarites vectors)
    """

    query = '''
            SELECT
                "mergedChunkId",
                ("jinaV3" <#> %s::vector) AS "jinaV3",
                (omarelshehy <#> %s::vector) AS omarelshehy,
                ("Qwen-0.6B" <#> %s::vector) AS "Qwen-0.6B"
            FROM "Embeddings"
            WHERE "videoId" = %s;
        '''

    # pass the same vector 3 times + video_id
    cursor.execute(query, (queryVectors[0], queryVectors[1], queryVectors[2], video_id))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=columns)
    return df

def get_table_from_db(cursor, Table_Name, list_columns, filter_conditions=None):
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