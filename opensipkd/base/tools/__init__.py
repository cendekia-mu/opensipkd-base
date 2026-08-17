import colander
from datetime import datetime, date
from decimal import Decimal

def obj2json(values):
        for key, val in values.items():
            if isinstance(val, datetime):
                values[key] = val.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(val, date):
                values[key] = val.strftime('%Y-%m-%d')
            elif isinstance(val, Decimal):
                values[key] = float(val)
            elif isinstance(val, colander._null):
                values[key] = ""
            elif isinstance(val, dict):
                # if 'fp' in val:
                #     values[key] = val.get('preview_url') or "FILEBLOB"
                # else:
                values[key] = obj2json(val)
        return values
