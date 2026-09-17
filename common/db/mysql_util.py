# common/db/mysql_util.py

import pymysql
import logging
import allure
from contextlib import contextmanager
from typing import Optional, List, Any, Dict

from common.config.config_loader import config

logger = logging.getLogger(__name__)

class MysqlUtil:

    def __init__(self):
        self.db_config = config.get('database', {})
        self._connection = None

    def _get_connection(self):
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 3306),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', ''),
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=10
            )
        return self._connection

    def _get_cursor(self):
        conn = self._get_connection()
        return conn.cursor(pymysql.cursors.DictCursor)

    @contextmanager
    def get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f'Database error: {e}')
            raise
        finally:
            cursor.close()

    @allure.step("执行SQL查询")
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            logger.debug(f'Query SQL: {sql}')
            if params:
                logger.debug(f'Params: {params}')
            cursor.execute(sql, params)
            result = cursor.fetchall()
            logger.debug(f'Query result count: {len(result)}')

            if not result:
                logger.warning(f"查询结果为空：{sql}， params:{params}")

            return result
        except Exception as e:
            logger.error(f'Query failed: {e}')
            raise
        finally:
            cursor.close()

    @allure.step("执行SQL")
    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            logger.debug(f'Execute SQL: {sql}')
            if params:
                logger.debug(f'Params: {params}')
            affected = cursor.execute(sql, params)
            conn.commit()
            logger.debug(f"Affected rows: {affected}")
        except Exception as e:
            conn.rollback()
            logger.error(f'Execute failed: {e}')
            raise
        finally:
            cursor.close()

    @allure.step("执行多条SQL")
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            logger.debug(f'Execute many SQL: {sql}')
            affected = cursor.executemany(sql, params_list)
            conn.commit()
            return affected
        except Exception as e:
            conn.rollback()
            logger.error(f'Execute failed: {e}')
            raise
        finally:
            cursor.close()

    def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict]:
        result = self.query(sql, params)
        return result[0] if result else None

    def fetch_value(self, sql: str, params: Optional[tuple] = None) -> Any:
        result = self.query(sql, params)
        if result and len(result) > 0:
            return list(result[0].values())[0]
        return None

    def get_id_by_field(self, table: str, field: str, value: Any,
                        id_field: str = 'id'):
        sql = f"select {id_field} from {table} where {field} = %s limit 1"
        result = self.query(sql, (value,))
        if result:
            return result[0].get(id_field)
        return None

    def insert(self, table: str, data: Dict) -> int:
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ','.join(['%s'] * len(fields))
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
        self.execute(sql, tuple(values))
        conn = self._get_connection()
        return conn.insert_id()

    def update(self, table: str, data: Dict, condiction: str, condiction_params: tuple = None) -> int:
        fields = [f"{k} = %s" for k in data.keys()]
        values = list(data.values())
        if condiction_params:
            values.extend(condiction_params)
        sql = f"UPDATE {table} SET {', '.join(fields)} WHERE {condiction}"
        return self.execute(sql, tuple(values))

    def delete(self, table: str, condiction: str, params: Optional[tuple] = None) -> int:
        sql = f"DELETE FROM {table} WHERE {condiction}"
        return self.execute(sql, params)

    def close(self):
        if self._connection and self._connection.open:
            self._connection.close()
            logger.info("Database connection closed")

mysql = MysqlUtil()