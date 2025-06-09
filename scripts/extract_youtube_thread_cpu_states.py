from perfetto.trace_processor import TraceProcessor
import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: python extract_youtube_thread_cpu_states.py <trace_file_path> <output_csv_path>")
    sys.exit(1)

trace_file = sys.argv[1]
output_csv = sys.argv[2]
process_name_filter = "com.google.android.youtube"

try:
    tp = TraceProcessor(trace=trace_file)

    # Get upid for the process name
    upid_query_result = tp.query(f"SELECT upid FROM process WHERE name = \'{process_name_filter}\' LIMIT 1").as_pandas_dataframe()
    if upid_query_result.empty:
        print(f"Process \'{process_name_filter}\' not found in the trace.")
        sys.exit(1)
    target_upid = upid_query_result["upid"][0]

    query = f"""
    WITH YoutubeThreads AS (
        SELECT utid, name AS thread_name
        FROM thread
        WHERE upid = {target_upid}
    ),
    RunningTimes AS (
        SELECT
            utid,
            SUM(dur) AS running_ns
        FROM sched_slice
        WHERE utid IN (SELECT utid FROM YoutubeThreads)
        GROUP BY utid
    ),
    StateTimes AS (
        SELECT
            utid,
            state,
            SUM(dur) AS state_ns
        FROM thread_state
        WHERE utid IN (SELECT utid FROM YoutubeThreads)
        GROUP BY utid, state
    )
    SELECT
        yt.thread_name,
        COALESCE(rt.running_ns, 0) AS total_running_ns,
        COALESCE(st_runnable.state_ns, 0) AS total_runnable_ns, /* R */
        COALESCE(st_sleeping.state_ns, 0) AS total_sleeping_ns, /* S */
        COALESCE(st_interruptible_sleep.state_ns, 0) AS total_interruptible_sleep_ns, /* D */
        COALESCE(st_uninterruptible_sleep.state_ns, 0) AS total_uninterruptible_sleep_ns, /* DK */
        COALESCE(st_stopped.state_ns, 0) AS total_stopped_ns, /* T */
        COALESCE(st_parked.state_ns, 0) AS total_parked_ns /* P */
    FROM YoutubeThreads yt
    LEFT JOIN RunningTimes rt ON yt.utid = rt.utid
    LEFT JOIN StateTimes st_runnable ON yt.utid = st_runnable.utid AND st_runnable.state = 'R'
    LEFT JOIN StateTimes st_sleeping ON yt.utid = st_sleeping.utid AND st_sleeping.state = 'S'
    LEFT JOIN StateTimes st_interruptible_sleep ON yt.utid = st_interruptible_sleep.utid AND st_interruptible_sleep.state = 'D'
    LEFT JOIN StateTimes st_uninterruptible_sleep ON yt.utid = st_uninterruptible_sleep.utid AND st_uninterruptible_sleep.state = 'DK'
    LEFT JOIN StateTimes st_stopped ON yt.utid = st_stopped.utid AND st_stopped.state = 'T'
    LEFT JOIN StateTimes st_parked ON yt.utid = st_parked.utid AND st_parked.state = 'P'
    ORDER BY total_running_ns DESC, yt.thread_name;
    """

    youtube_thread_states_df = tp.query(query).as_pandas_dataframe()
    youtube_thread_states_df.to_csv(output_csv, index=False)
    print(f"YouTube thread CPU and state times saved to {output_csv}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("YouTube thread CPU and state time extraction complete.")

