from dataclasses import asdict
from collections import OrderedDict
import pandas as pd
from loguru import logger
from sniffRTU.analyze import Traffic

if __name__ == '__main__':
    import argparse
    import sys
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # Create an argparse argument parser
    parser = argparse.ArgumentParser(description="Filter DataFrame rows by timestamp range")

    # Add optional arguments for start and end timestamps
    parser.add_argument("--start", help="Start timestamp in 'YYYY-MM-DD HH:MM:SS' format")
    parser.add_argument("--end", help="End timestamp in 'YYYY-MM-DD HH:MM:SS' format")
    parser.add_argument("--table", help="Table name")
    parser.add_argument("--output", help="Output filename")

    args = parser.parse_args()

    tablename = '20231002_avalonoffgrid'
    traffic = Traffic(tablename=tablename).between(start=args.start, end=args.end)
    print(traffic.df)
    hexl = traffic.as_hexl()
    logger.debug(hexl)

    messages = traffic.to_messages(hexl=hexl)

    # Prepare the output file
    output_filename = args.output

    records = []

    for msg in messages:
        record = {'ts': msg.ts()}
        record.update(asdict(msg))
        record['msg'] = str(msg.__class__.__name__)
        records.append(record)

    df = pd.DataFrame.from_records(records)
    if output_filename:
        df.to_csv(output_filename)

    else:
        print(df)

