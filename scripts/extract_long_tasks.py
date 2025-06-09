from perfetto.trace_processor import TraceProcessor
import pandas as pd
import sys

if len(sys.argv) != 6:
    print("Usage: python extract_long_tasks.py <trace_file_path> <process_name> <thread_name> <duration_threshold_ns> <output_csv_path>")
    sys.exit(1)

trace_file = sys.argv[1]
process_name_filter = sys.argv[2]
thread_name_filter = sys.argv[3]
duration_threshold_ns = int(sys.argv[4])
output_csv = sys.argv[5]

try:
    tp = TraceProcessor(trace=trace_file)

    # Construct the query parts
    query_select = "SELECT slice.name AS slice_name, thread.name AS thread_name, process.name AS process_name, slice.ts, slice.dur, thread.utid, process.upid"
    query_from_join = """
    FROM slice
    JOIN thread_track ON slice.track_id = thread_track.id
    JOIN thread ON thread_track.utid = thread.utid
    JOIN process ON thread.upid = process.upid
    """
    
    conditions = []
    conditions.append(f"process.name = '{process_name_filter}'")   
    if thread_name_filter.lower() != 'all':
        conditions.append(f"thread.name = \'{thread_name_filter}\'")
    
    conditions.append(f"slice.dur > {duration_threshold_ns}")
    
    query_where = "WHERE " + " AND ".join(conditions)
    query_order_by = "ORDER BY slice.dur DESC"
    
    final_query = f"{query_select}\n{query_from_join}\n{query_where}\n{query_order_by};"
    
    # print(f"Executing query: {final_query}") # For debugging

    long_tasks_df = tp.query(final_query).as_pandas_dataframe()
    long_tasks_df.to_csv(output_csv, index=False)
    print(f"Long-running task data for process \'{process_name_filter}\' (thread: \'{thread_name_filter}\") saved to {output_csv}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("Long-running task extraction complete.")
