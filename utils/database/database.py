import sqlite3
import logging
from sqlite3 import Error
import sys
import os
from pathlib import Path
from moviepy.editor import VideoFileClip
sys.path.append(str(Path(__file__).parent.parent))
PATH = str(Path(__file__).parent)
def main():
    # insert_data_into_role_table()
    # insert_data_into_users_table(id=123,username="viet",role_id=2)
    # insert_data_into_media_table(user_id=123, type = "video",input_image_path="./input",input_video_path= "./input/video",input_voice_path="/input/voice", output_video_path='/output/video',size='6.54 MB',time="00:00:31")
    # data_users = select_data_table(table='users')
    # # print("data type ",data)
    # # print("data = ",data)
    # data_media = select_data_table(table='media')
    # print(data_users)
    # print(data_media)
    data = get_url_from_media_table_by_id(1)
    print(data)
    data = select_data_table('users')
    print(data)
    a= ['abc',"456"]
    a= str(a)
    print(a,type(a))
def check_user_exists(user_id):
    # Connect to the database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Execute a query to check if the user_id exists
    c.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()

    # Close the connection
    conn.close()

    # If result is not None, the user exists
    return result is not None

def get_file_size_and_duration( filepath ):
    """Gets the size and modification time of a file.

    Args:
        filepath: The path to the file (as a pathlib.Path object).

    Returns:
        A tuple containing the size (in bytes) and modification time (in seconds since epoch) of the file.
    """
    size = os.path.getsize(filepath)
    file_size_mb = size/(1024 * 1024)
    clip = VideoFileClip(filepath )
    seconds = round(clip.duration)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 3600) % 60
    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f'{round(file_size_mb,2)} MB' , duration

def create_table(database:str):
    try:
        conn = sqlite3.connect(os.path.join(PATH,"database.db"))
        logging.info("Successfully Connected to SQLite")
        c = conn.cursor()
        # Create the role table
        c.execute('''
            CREATE TABLE IF NOT EXISTS role (
                id INTEGER PRIMARY KEY,
                role TEXT
            )
        ''')
        # Create the users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                role_id INTEGER,
                FOREIGN KEY (role_id) REFERENCES role (id)
            )
        ''')

        # Create the media table
        c.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                type TEXT,
                input_image_path TEXT,
                input_video_path TEXT,
                input_voice_path TEXT,
                output_video_path TEXT,
                size TEXT,
                time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
        logging.info("SQLite table created")
        conn.close()
    except sqlite3.Error as error:
        logging.error("Error while creating a sqlite table", error)
    finally:
        if conn:
            conn.close()
            logging.info("sqlite connection is closed")
            

def insert_data_into_role_table():
    try:
        conn = sqlite3.connect(os.path.join(PATH,"database.db"))
        c = conn.cursor() 
        # Insert data into the role table
        c.execute('INSERT INTO role (role) VALUES (?)', ('admin',))
        c.execute('INSERT INTO role (role) VALUES (?)', ('user',))
        conn.commit()
        print("[INFO] : insert data into table role of database.")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
        else:
            print("something is wrong here.")      
            
def insert_data_into_users_table(id:int, username:str, role_id:int):
    try:
        conn = sqlite3.connect(os.path.join(PATH,"database.db"))
        c = conn.cursor() 
        # Insert data into the role table
        c.execute('INSERT INTO users (id, username, role_id) VALUES (?,?, ?)', (id, username,role_id))
        conn.commit()
        print("[INFO] : insert data into table role of database.")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
        else:
            print("something is wrong here.")  
            
def insert_data_into_media_table(user_id:int, type:str, input_image_path:str, input_video_path:str, input_voice_path:str, output_video_path:str, size:str, time:str):
    try:
        conn = sqlite3.connect(os.path.join(PATH,"database.db"))
        c = conn.cursor() 
        # Insert data into the role table
        c.execute('INSERT INTO media (user_id, type, input_image_path, input_video_path, input_voice_path, output_video_path, size, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', \
            (user_id, type, input_image_path, input_video_path, input_voice_path, output_video_path,size,time))
        # (1, 'video', '/path/to/image', '/path/to/video', '/path/to/voice', '/path/to/output', '500MB', '12:00:00'))
        conn.commit()
        print("[INFO] : insert data into table role of database.")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
        else:
            print("something is wrong here.")  
            
def select_data_table(table:str):
    conn = sqlite3.connect(os.path.join(PATH,"database.db"))
    c = conn.cursor()
    sql_fetch_blob_query = f"SELECT * from {table}"
    c.execute(sql_fetch_blob_query)
    record = c.fetchall()
    conn.commit()
    conn.close()
    return record
def get_url_from_media_table_by_id(id: int):
    conn = sqlite3.connect(os.path.join(PATH,"database.db"))
    c = conn.cursor()
    sql_fetch_blob_query = "SELECT * from media where id = ?"
    c.execute(sql_fetch_blob_query,(id,))
    record = c.fetchone()
    conn.commit()
    conn.close()
    return record[6]
if __name__ == "__main__":
    main()