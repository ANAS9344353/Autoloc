# Permet d'utiliser PyMySQL (Python pur) comme driver MySQL
# au lieu de mysqlclient qui necessite des outils de compilation.
import pymysql

pymysql.install_as_MySQLdb()
