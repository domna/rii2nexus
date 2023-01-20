"""Convert the refractiveindex.info database to nexus"""
import elli

database = elli.db.RII()

print(database.catalog.columns.values)
