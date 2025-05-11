from perfetto.trace_processor import TraceProcessor
import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: python extract_thread_states.py <trace_file_path> <thread_states_output_path>")
    sys.exit(1)

trace_file = sys.argv[1]
thread_states_output = sys.argv[2]

try:
    # Initialize TraceProcessor with the trace file
    tp = TraceProcessor(trace=trace_file)

    # Query for thread states
    thread_states_df = tp.query("""
        SELECT
            thread_state.utid,
            thread.name AS thread_name,
            process.name AS process_name,
            thread_state.ts,
            thread_state.dur,
            thread_state.state,
            thread_state.blocked_function
        FROM thread_state
        JOIN thread ON thread_state.utid = thread.utid
        JOIN process ON thread.upid = process.upid
        ORDER BY thread_state.ts;
    """).as_pandas_dataframe()
    thread_states_df.to_csv(thread_states_output, index=False)
    print(f"Thread state data saved to {thread_states_output}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("Thread state data extraction complete.")
