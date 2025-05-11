from perfetto.trace_processor import TraceProcessor
import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: python extract_cpu_usage.py <trace_file_path> <cpu_usage_output_path>")
    sys.exit(1)

trace_file = sys.argv[1]
cpu_usage_output = sys.argv[2]

try:
    # Initialize TraceProcessor with the trace file
    tp = TraceProcessor(trace=trace_file)

    # Query for CPU scheduling slices (CPU time per thread)
    # This query provides duration each thread ran on each CPU
    cpu_sched_df = tp.query("""
        SELECT
            thread.name AS thread_name,
            process.name AS process_name,
            process.upid,
            thread.utid,
            sched_slice.cpu,
            sched_slice.ts,
            sched_slice.dur,
            sched_slice.end_state
        FROM sched_slice
        JOIN thread ON sched_slice.utid = thread.utid
        JOIN process ON thread.upid = process.upid
        ORDER BY sched_slice.ts;
    """).as_pandas_dataframe()
    cpu_sched_df.to_csv(cpu_usage_output, index=False)
    print(f"CPU scheduling slice data saved to {cpu_usage_output}")

    # Example: Query for CPU frequency (if available and relevant)
    # cpu_freq_df = tp.query("SELECT ts, value, cpu FROM counter WHERE name = 'cpufreq'").as_pandas_dataframe()
    # cpu_freq_df.to_csv(cpu_freq_output, index=False)
    # print(f"CPU frequency data saved to {cpu_freq_output}")

    # Example: Query for Android CPU metrics (this returns a protobuf, not directly a dataframe)
    # try:
    #     android_cpu_metric = tp.metric([\'android_cpu\'])
    #     with open(f"{cpu_usage_output}_android_cpu_metric.txt", "w") as f:
    #         f.write(str(android_cpu_metric))
    #     print(f"Android CPU metric saved to {cpu_usage_output}_android_cpu_metric.txt")
    # except Exception as e_metric:
    #     print(f"Could not retrieve android_cpu metric: {e_metric}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("CPU usage data extraction complete.")
