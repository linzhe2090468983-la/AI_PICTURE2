import pymysql
from config import MYSQL_CONFIG

try:
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # 修改image_url字段类型为LONGTEXT
    alter_sql = """
    ALTER TABLE generation_records
    MODIFY COLUMN image_url LONGTEXT NOT NULL
    """

    cursor.execute(alter_sql)
    conn.commit()

    print('✅ generation_records表的image_url字段已修改为LONGTEXT')

    # 再次检查表结构
    cursor.execute('DESCRIBE generation_records')
    columns = cursor.fetchall()

    print('\n修改后的表结构:')
    for col in columns:
        print(f'  {col[0]}: {col[1]} (允许NULL: {col[2]})')

    conn.close()

except Exception as e:
    print(f'修改表结构失败: {e}')

