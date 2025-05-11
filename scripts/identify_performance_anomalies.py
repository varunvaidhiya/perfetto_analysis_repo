import pandas as pd
import sys

# Thresholds (can be adjusted)
LONG_TASK_THRESHOLD_MS = 16
HIGH_RUNNABLE_RATIO_THRESHOLD = 0.2 # Runnable time is 20% of (runnable + running)
CPU_SPIKE_WINDOW_MS = 100 # Time window in ms to check for CPU spikes
CPU_SPIKE_PROCESS_THRESHOLD_MS = 50 # If a process uses more than this in a window, it might be a spike contributor
SHORT_RUN_THRESHOLD_NS = 5_000_000 # 5ms for a run to be considered short
FREQUENT_SHORT_RUN_COUNT_THRESHOLD = 100 # If a thread has more than this many short runs

# Assumed CPU core configuration (example: 0-3 LITTLE, 4-7 big/Gold). Update if metadata provides specifics.
# This is a placeholder; actual core types should be determined from device specs or trace metadata if possible.
ASSUMED_LITTLE_CORES = list(range(4))
ASSUMED_BIG_CORES = list(range(4, 8))

def analyze_perf_samples_skipped(system_info_df):
    report = []
    report.append("## Perf Samples Skipped Analysis")
    skipped_samples_row = system_info_df[system_info_df["name"] == "perf_samples_skipped"]
    if not skipped_samples_row.empty:
        # Corrected f-string
        report.append(f"- Perfetto reported **{skipped_samples_row['int_value'].iloc[0]} skipped perf samples**. This indicates some CPU profiling data might be missing, which could affect the completeness of CPU-bound analysis.")
    else:
        report.append("- No explicit \"perf_samples_skipped\" metadata found. This doesn\'t guarantee no samples were skipped, but the specific counter is absent.")
    report.append("\n")
    return "\n".join(report)

def analyze_long_main_thread_tasks(long_tasks_df, process_name, thread_name):
    report = []
    report.append(f"## Long Tasks on {process_name} - {thread_name} Analysis")
    if long_tasks_df.empty:
        report.append(f"- No long tasks (>{LONG_TASK_THRESHOLD_MS}ms) recorded in the provided CSV for {thread_name}.")
    else:
        count_long_tasks = len(long_tasks_df)
        max_duration_ms = long_tasks_df["dur"].max() / 1_000_000
        avg_duration_ms = long_tasks_df["dur"].mean() / 1_000_000
        report.append(f"- Found **{count_long_tasks} tasks longer than {LONG_TASK_THRESHOLD_MS}ms** on {thread_name}.")
        report.append(f"  - Maximum duration observed: {max_duration_ms:.2f} ms.")
        report.append(f"  - Average duration of these long tasks: {avg_duration_ms:.2f} ms.")
        report.append(f"  - These tasks are prime suspects for causing UI unresponsiveness or jank.")
    report.append("\n")
    return "\n".join(report)

def analyze_high_runnable_time(youtube_thread_states_df):
    report = []
    report.append("## High Runnable Time for YouTube Threads Analysis")
    if youtube_thread_states_df.empty:
        report.append("- YouTube thread CPU/state data is empty. Cannot analyze runnable times.")
    else:
        youtube_thread_states_df["runnable_plus_running_ns"] = youtube_thread_states_df["total_runnable_ns"] + youtube_thread_states_df["total_running_ns"]
        youtube_thread_states_df["runnable_ratio"] = youtube_thread_states_df["total_runnable_ns"] / youtube_thread_states_df["runnable_plus_running_ns"].replace(0, pd.NA)
        
        high_runnable_threads = youtube_thread_states_df[youtube_thread_states_df["runnable_ratio"] > HIGH_RUNNABLE_RATIO_THRESHOLD]
        
        if high_runnable_threads.empty:
            report.append(f"- No YouTube threads found with a runnable time ratio greater than {HIGH_RUNNABLE_RATIO_THRESHOLD*100}% of their active (runnable + running) time.")
        else:
            report.append(f"- Identified YouTube threads spending a significant portion of active time in a runnable state (waiting for CPU, ratio > {HIGH_RUNNABLE_RATIO_THRESHOLD*100}%):")
            for _, row in high_runnable_threads.iterrows():
                # Corrected f-strings
                report.append(f"  - **Thread: {row['thread_name']}**")
                report.append(f"    - Total Running Time: {row['total_running_ns'] / 1_000_000:.2f} ms")
                report.append(f"    - Total Runnable Time: {row['total_runnable_ns'] / 1_000_000:.2f} ms")
                report.append(f"    - Runnable Ratio (Runnable / (Runnable+Running)): {row['runnable_ratio']*100:.2f}%")
                report.append(f"    - High runnable time suggests CPU contention and can lead to performance bottlenecks and jank.")
    report.append("\n")
    return "\n".join(report)

def analyze_youtube_thread_core_placement(cpu_sched_df, system_info_df):
    report = []
    report.append("## YouTube Thread CPU Core Placement Analysis")
    
    cpu_info = system_info_df[system_info_df["name"].str.contains("cpu[0-9]+_max_freq_khz", case=False, na=False)]
    
    report.append(f"- Assuming LITTLE cores: {ASSUMED_LITTLE_CORES}, BIG cores: {ASSUMED_BIG_CORES} for this analysis. (This should be verified with device specs or detailed trace metadata if possible).")

    youtube_sched_df = cpu_sched_df[cpu_sched_df["process_name"] == "com.google.android.youtube"].copy()
    if youtube_sched_df.empty:
        report.append("- No CPU scheduling slices found for 'com.google.android.youtube'. Cannot analyze core placement.")
    else:
        youtube_sched_df["core_type"] = youtube_sched_df["cpu"].apply(lambda x: "LITTLE" if x in ASSUMED_LITTLE_CORES else ("BIG" if x in ASSUMED_BIG_CORES else "UNKNOWN"))
        
        critical_threads = ["com.google.android.youtube:main", "RenderThread", "GPU completion"]
        youtube_critical_sched = youtube_sched_df[youtube_sched_df["thread_name"].isin(critical_threads)]
        
        if youtube_critical_sched.empty:
            report.append("- No scheduling data found for critical YouTube threads (main, RenderThread, GPU completion).")
        else:
            little_core_usage = youtube_critical_sched[youtube_critical_sched["core_type"] == "LITTLE"]
            if not little_core_usage.empty:
                total_dur_on_little = little_core_usage["dur"].sum()
                total_dur_critical = youtube_critical_sched["dur"].sum()
                percentage_on_little = (total_dur_on_little / total_dur_critical) * 100 if total_dur_critical > 0 else 0
                report.append(f"- Critical YouTube threads spent **{percentage_on_little:.2f}%** of their CPU time on assumed LITTLE cores ({total_dur_on_little / 1_000_000:.2f} ms out of {total_dur_critical / 1_000_000:.2f} ms).")
                report.append("  - Running critical tasks on LITTLE cores can lead to slower performance and jank, especially if BIG cores were available.")
                
                main_thread_on_little = little_core_usage[little_core_usage["thread_name"] == "com.google.android.youtube:main"]
                if not main_thread_on_little.empty:
                    # Corrected f-string (already correct in original, but good to double check)
                    report.append(f"    - Specifically, 'com.google.android.youtube:main' ran on LITTLE cores for {main_thread_on_little['dur'].sum() / 1_000_000:.2f} ms.")
            else:
                report.append("- Critical YouTube threads did not appear to run on assumed LITTLE cores.")
    report.append("\n")
    return "\n".join(report)

def analyze_cpu_spikes(cpu_sched_df):
    report = []
    report.append("## CPU Spikes Analysis")
    if cpu_sched_df.empty:
        report.append("- CPU scheduling data is empty. Cannot analyze CPU spikes.")
    else:
        total_cpu_time_per_process = cpu_sched_df.groupby("process_name")["dur"].sum().sort_values(ascending=False)
        # Ensure 'ts' and 'dur' columns exist before using them for total_trace_duration_ns calculation
        if 'ts' in cpu_sched_df.columns and 'dur' in cpu_sched_df.columns and not cpu_sched_df.empty:
            total_trace_duration_ns = cpu_sched_df["ts"].max() + cpu_sched_df.loc[cpu_sched_df["ts"].idxmax()]["dur"] - cpu_sched_df["ts"].min()
            total_trace_duration_ms = total_trace_duration_ns / 1_000_000
            report.append(f"- Overall trace duration considered for CPU usage: {total_trace_duration_ms:.2f} ms.")
        else:
            report.append("- Could not determine total trace duration from sched_slice data (missing 'ts' or 'dur' columns, or data is empty).")
            total_trace_duration_ns = 0 # Avoid further errors

        report.append("- Top 5 CPU consuming processes (total duration):")
        for process, dur_ns in total_cpu_time_per_process.head(5).items():
            report.append(f"  - **{process}**: {dur_ns / 1_000_000:.2f} ms")
        
        youtube_cpu_time_ns = total_cpu_time_per_process.get("com.google.android.youtube", 0)
        if youtube_cpu_time_ns > 0:
            report.append(f"- 'com.google.android.youtube' consumed {youtube_cpu_time_ns / 1_000_000:.2f} ms of CPU time in total.")
        else:
            report.append("- 'com.google.android.youtube' process not found or had no CPU time in sched_slice data.")
        report.append("- Note: A more detailed spike analysis would involve windowing and looking for sudden bursts of activity.")
    report.append("\n")
    return "\n".join(report)

def analyze_short_runs_sleeps(cpu_sched_df, thread_states_df):
    report = []
    report.append("## Frequent Short Runs Followed by Sleep Analysis (Potential I/O or Lock Contention)")
    if cpu_sched_df.empty or thread_states_df.empty:
        report.append("- CPU scheduling or thread state data is empty. Cannot perform this analysis.")
    else:
        short_runs = cpu_sched_df[cpu_sched_df["dur"] < SHORT_RUN_THRESHOLD_NS]
        frequent_short_runners = short_runs.groupby(["process_name", "thread_name"])["utid"].count().reset_index(name="short_run_count")
        frequent_short_runners = frequent_short_runners[frequent_short_runners["short_run_count"] > FREQUENT_SHORT_RUN_COUNT_THRESHOLD]
        
        if frequent_short_runners.empty:
            report.append(f"- No threads found with more than {FREQUENT_SHORT_RUN_COUNT_THRESHOLD} short CPU runs (less than {SHORT_RUN_THRESHOLD_NS / 1_000_000}ms each).")
        else:
            report.append(f"- Identified threads with frequent short CPU runs (>{FREQUENT_SHORT_RUN_COUNT_THRESHOLD} instances, each <{SHORT_RUN_THRESHOLD_NS / 1_000_000}ms), which *might* indicate I/O waits or lock contention if followed by sleep states:")
            for _, row in frequent_short_runners.iterrows():
                # Corrected f-string (already correct in original, but good to double check)
                report.append(f"  - Process: **{row['process_name']}**, Thread: **{row['thread_name']}** - Short Run Count: {row['short_run_count']}")
            report.append("  - Deeper analysis is needed to confirm if these short runs are consistently followed by sleep states indicative of I/O or lock waits.")
    report.append("\n")
    return "\n".join(report)

def main(system_info_path, cpu_sched_path, long_tasks_path, yt_thread_states_path, thread_states_path, output_report_path):
    try:
        system_info_df = pd.read_csv(system_info_path)
        cpu_sched_df = pd.read_csv(cpu_sched_path)
        long_tasks_df = pd.read_csv(long_tasks_path)
        yt_thread_states_df = pd.read_csv(yt_thread_states_path)
        thread_states_df = pd.read_csv(thread_states_path)
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e.filename}")
        sys.exit(1)
    except pd.errors.EmptyDataError as e:
        print(f"Error: Input file is empty: {e.filename if hasattr(e, 'filename') else 'Unknown file'}")
        # Initialize empty DataFrames with expected columns if any are empty, to prevent downstream errors
        if 'system_info_df' not in locals() or system_info_df.empty: system_info_df = pd.DataFrame(columns=['name', 'int_value', 'str_value'])
        if 'cpu_sched_df' not in locals() or cpu_sched_df.empty: cpu_sched_df = pd.DataFrame(columns=['process_name', 'thread_name', 'cpu', 'ts', 'dur', 'utid'])
        if 'long_tasks_df' not in locals() or long_tasks_df.empty: long_tasks_df = pd.DataFrame(columns=['slice_name', 'thread_name', 'process_name', 'ts', 'dur', 'utid', 'upid'])
        if 'yt_thread_states_df' not in locals() or yt_thread_states_df.empty: yt_thread_states_df = pd.DataFrame(columns=['thread_name', 'total_running_ns', 'total_runnable_ns', 'total_sleeping_ns', 'total_interruptible_sleep_ns', 'total_uninterruptible_sleep_ns', 'total_stopped_ns', 'total_parked_ns', 'runnable_plus_running_ns', 'runnable_ratio'])
        if 'thread_states_df' not in locals() or thread_states_df.empty: thread_states_df = pd.DataFrame(columns=['utid', 'thread_name', 'process_name', 'ts', 'dur', 'state', 'blocked_function'])
        # pass # Or initialize empty DFs: e.g., if 'long_tasks_path' is empty, long_tasks_df = pd.DataFrame()

    # Ensure DataFrames are initialized even if some files were empty and caught by EmptyDataError
    if 'system_info_df' not in locals(): system_info_df = pd.DataFrame(columns=['name', 'int_value', 'str_value'])
    if 'cpu_sched_df' not in locals(): cpu_sched_df = pd.DataFrame(columns=['process_name', 'thread_name', 'cpu', 'ts', 'dur', 'utid'])
    if 'long_tasks_df' not in locals(): long_tasks_df = pd.DataFrame(columns=['slice_name', 'thread_name', 'process_name', 'ts', 'dur', 'utid', 'upid'])
    if 'yt_thread_states_df' not in locals(): yt_thread_states_df = pd.DataFrame(columns=['thread_name', 'total_running_ns', 'total_runnable_ns', 'total_sleeping_ns', 'total_interruptible_sleep_ns', 'total_uninterruptible_sleep_ns', 'total_stopped_ns', 'total_parked_ns', 'runnable_plus_running_ns', 'runnable_ratio'])
    if 'thread_states_df' not in locals(): thread_states_df = pd.DataFrame(columns=['utid', 'thread_name', 'process_name', 'ts', 'dur', 'state', 'blocked_function'])

    full_report = "# Performance Anomalies Report\n\n"
    full_report += "This report summarizes potential performance anomalies identified from the extracted Perfetto trace data.\n\n"

    full_report += analyze_perf_samples_skipped(system_info_df)
    full_report += analyze_long_main_thread_tasks(long_tasks_df, "com.google.android.youtube", "com.google.android.youtube:main")
    full_report += analyze_high_runnable_time(yt_thread_states_df)
    full_report += analyze_youtube_thread_core_placement(cpu_sched_df, system_info_df)
    full_report += analyze_cpu_spikes(cpu_sched_df)
    full_report += analyze_short_runs_sleeps(cpu_sched_df, thread_states_df)

    try:
        with open(output_report_path, "w") as f:
            f.write(full_report)
        print(f"Performance anomalies report saved to {output_report_path}")
    except IOError as e:
        print(f"Error writing report to file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python identify_performance_anomalies.py <system_info_csv> <cpu_sched_csv> <long_tasks_csv> <yt_thread_states_csv> <thread_states_csv> <output_report_md>")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])

