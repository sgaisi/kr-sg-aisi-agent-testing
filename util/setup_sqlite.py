import sqlite3
import json
import sys
import os


def parse_tuple_string(tuple_str):
    """Parse a string representation of a tuple into actual Python tuple."""
    tuple_str = tuple_str.strip()
    if tuple_str.startswith("(") and tuple_str.endswith(")"):
        tuple_str = tuple_str[1:-1]

    try:
        return eval(f"({tuple_str},)")
    except:
        values = []
        current = ""
        in_quotes = False
        quote_char = None

        for char in tuple_str:
            if char in ('"', "'") and (not current or current[-1] != "\\"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            elif char == "," and not in_quotes:
                values.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            values.append(current.strip())

        result = []
        for v in values:
            v = v.strip()
            if v == "None":
                result.append(None)
            elif v in ("True", "False"):
                result.append(v == "True")
            elif v.startswith(("'", '"')) and v.endswith(("'", '"')):
                result.append(v[1:-1])
            else:
                try:
                    if "." in v:
                        result.append(float(v))
                    else:
                        result.append(int(v))
                except:
                    result.append(v)

        return tuple(result)


def setup_database_from_setup_step(step):
    """Set up database from a setup step (new format)."""
    db_path = step.get("db_path")
    if not db_path:
        print("No db_path in setup step")
        return

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    content = step.get("content", {})
    schemas = content.get("db_schemas", {})
    insert_stmts = content.get("db_insert_stmts", {})
    data = content.get("db_data", content.get("raw_data", {}))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table_name in schemas.keys():
        create_sql = schemas[table_name]
        cursor.execute(create_sql)
        print(f"Created table: {table_name}")

        if table_name in data and table_name in insert_stmts:
            insert_sql = insert_stmts[table_name]
            table_data = data[table_name]

            parsed_data = []
            for data_str in table_data:
                try:
                    parsed_tuple = parse_tuple_string(data_str)
                    parsed_data.append(parsed_tuple)
                except Exception as e:
                    print(f"Warning: Failed to parse data for {table_name}: {str(e)}")
                    continue

            if parsed_data:
                cursor.executemany(insert_sql, parsed_data)
                print(f"Inserted {len(parsed_data)} records into {table_name}")

    conn.commit()
    conn.close()

    print(f"\nDatabase created successfully: {db_path}")


def setup_database_from_scenario(scenario_file):
    """Parse scenario JSON and create SQLite database with all tables."""

    with open(scenario_file, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    db_config = None
    db_path = None

    for server in scenario.get("mcp_servers", []):
        if server.get("server_script_path") == "database.py":
            db_config = server
            if server.get("paths"):
                db_path = server["paths"][0]
            break

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    content = db_config.get("content", {})
    schemas = content.get("db_schemas", {})
    insert_stmts = content.get("db_insert_stmts", {})
    data = content.get("db_data", {})
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table_name in schemas.keys():

        create_sql = schemas[table_name]
        cursor.execute(create_sql)

        if table_name in data and table_name in insert_stmts:
            insert_sql = insert_stmts[table_name]
            table_data = data[table_name]

            parsed_data = []
            for data_str in table_data:
                try:
                    parsed_tuple = parse_tuple_string(data_str)
                    parsed_data.append(parsed_tuple)
                except Exception as e:
                    print(f"Warning: Failed to parse data: {str(e)}")
                    continue

            if parsed_data:
                cursor.executemany(insert_sql, parsed_data)
                print(f"Inserted {len(parsed_data)} records")

    conn.commit()
    conn.close()

    print(f"\nDatabase created successfully: {db_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_sqlite.py <scenario_file.json>")
        sys.exit(1)

    scenario_file = sys.argv[1]

    if not os.path.exists(scenario_file):
        print(f"Scenario file not found: {scenario_file}")
        sys.exit(1)

    setup_database_from_scenario(scenario_file)
