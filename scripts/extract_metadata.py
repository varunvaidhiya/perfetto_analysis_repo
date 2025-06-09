from perfetto.trace_processor import TraceProcessor
import pandas as pd
import sys

if len(sys.argv) != 5:
    print("Usage: python extract_metadata.py <trace_file_path> <system_info_output_path> <process_info_output_path> <thread_info_output_path>")
    sys.exit(1)

trace_file = sys.argv[1]
system_info_output = sys.argv[2]
process_info_output = sys.argv[3]
thread_info_output = sys.argv[4]

try:
    # Initialize TraceProcessor with the trace file
    tp = TraceProcessor(trace=trace_file)

    # Query for system information (metadata)
    system_info_df = tp.query("SELECT name, str_value, int_value FROM metadata").as_pandas_dataframe()
    system_info_df.to_csv(system_info_output, index=False)
    print(f"System information saved to {system_info_output}")

    # Query for process information
    process_info_df = tp.query("SELECT upid, name, start_ts, end_ts, parent_upid FROM process").as_pandas_dataframe()
    process_info_df.to_csv(process_info_output, index=False)
    print(f"Process information saved to {process_info_output}")

    # Query for thread information
    thread_info_df = tp.query("SELECT utid, tid, name, upid, start_ts, end_ts FROM thread").as_pandas_dataframe()
    thread_info_df.to_csv(thread_info_output, index=False)
    print(f"Thread information saved to {thread_info_output}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("Metadata extraction complete.")
