import sys
import os
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

# Add beta to sys.path so we can import from db
sys.path.append(os.path.dirname(__file__))

from db.models import Base

# Open the migration file passed as an argument
migration_file = sys.argv[1]

with open(migration_file, 'w', encoding='utf-8') as f:
    f.write("-- Generated SQLAlchemy Schema for PostgreSQL\n\n")
    
    # Iterate through all tables defined in models.py
    for table_name, table in Base.metadata.tables.items():
        # Compile CreateTable statement for postgresql
        create_stmt = CreateTable(table).compile(dialect=postgresql.dialect())
        f.write(f"{create_stmt};\n\n")
        
    f.write("-- End of generated schema\n")

print(f"Schema dumped successfully to {migration_file}")
