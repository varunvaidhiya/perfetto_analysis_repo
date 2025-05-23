

# Perfetto Trace Analysis 

This repository contains the analysis of a Perfetto trace file, focusing on identifying performance anomalies and understanding system behavior. The project was undertaken as part of a recruitment task and demonstrates a methodical approach to trace analysis using Python scripts for data extraction and processing, culminating in a presentation of the findings.

The primary goal of this analysis is to dissect the provided Perfetto trace to uncover insights into CPU usage, thread states, long-running tasks, and specific application behavior, particularly concerning YouTube application threads. By leveraging various Python scripts, I

extract meaningful data from the trace, process it into human-readable formats (like CSVs and markdown reports), and visualize key metrics. This detailed examination helps in pinpointing potential performance bottlenecks and understanding the interactions between different system components during the traced period. The findings are consolidated into a comprehensive presentation, offering a clear overview of the analysis process, key observations, and actionable insights derived from the trace data. This README provides a guide to the repository structure, the data used, the scripts developed for analysis, the results obtained, and instructions on how to replicate the analysis.


## Data

The core data for this analysis is a Perfetto trace file named `PerfettoTraceForRecruitment`. This file is located in the `data` subdirectory of this repository. Perfetto is an open-source tracing tool for Android, Linux, and Chrome, designed to collect performance information from these systems. The trace file captures a wide array of system events over a period, including CPU scheduling, thread activity, system calls, and application-specific events. For this project, the trace file was provided as part of the recruitment task and is assumed to be representative of a system undergoing various workloads, including interactions with the YouTube application. The analysis scripts in this repository are designed to parse this specific trace file format to extract relevant performance metrics. Understanding the nature of the data captured within this trace is crucial for interpreting the analysis results accurately. The trace provides a low-level view of system operations, allowing for a granular investigation of performance characteristics and potential issues.


## Scripts

All Python scripts used for this analysis are located in the `scripts` subdirectory. These scripts are designed to parse the Perfetto trace file, extract specific performance data, and generate reports or visualizations. Below is a description of each script and its role in the analysis pipeline. It is assumed that Python 3 is installed on the system, along with necessary libraries which are detailed in the "How to Replicate" section.

### `extract_metadata.py`
This script is responsible for extracting general metadata from the Perfetto trace file. This metadata typically includes information about the device, the duration of the trace, and other high-level details that provide context for the analysis. To run this script, navigate to the `scripts` directory and execute `python3 extract_metadata.py ../data/PerfettoTraceForRecruitment ../results/system_info.csv`. The script takes the path to the trace file as the first argument and the desired output path for the CSV file containing the metadata as the second argument.

### `extract_cpu_usage.py`
This script focuses on analyzing CPU scheduling data within the trace. It extracts information about CPU slice events, which detail when and for how long each process and thread ran on each CPU core. The output is a CSV file that can be used for further analysis of CPU utilization patterns, identifying CPU-bound processes, and understanding core affinity. To execute this script, use the command: `python3 extract_cpu_usage.py ../data/PerfettoTraceForRecruitment ../results/cpu_sched_slices.csv`. The first argument is the trace file, and the second is the output CSV file path.

### `extract_thread_states.py`
This script processes thread state events from the Perfetto trace. It captures the various states a thread goes through during its lifecycle (e.g., Running, Runnable, Sleeping, Blocked) and the duration spent in each state. This information is crucial for understanding thread behavior, identifying bottlenecks caused by threads waiting for resources, and debugging performance issues related to thread synchronization. The script outputs a CSV file. Run it using: `python3 extract_thread_states.py ../data/PerfettoTraceForRecruitment ../results/thread_states.csv`.

### `extract_long_tasks.py`
This script is designed to identify long-running tasks specifically within the main thread of the YouTube application (`com.google.android.youtube`). Long tasks on the main thread can lead to application unresponsiveness (ANR) and a poor user experience. The script filters events for the specified thread and identifies tasks exceeding a certain duration threshold. The output is a CSV file listing these long tasks. Execute it with: `python3 extract_long_tasks.py ../data/PerfettoTraceForRecruitment com.google.android.youtube ../results/long_running_tasks_youtube_main.csv`.

### `extract_youtube_thread_cpu_states.py`
This script specifically analyzes the CPU states of threads belonging to the YouTube application. It helps in understanding how much CPU time YouTube threads are consuming and in what states they are spending their time. This can be useful for optimizing the application's performance. The output is a CSV file. Run the script using: `python3 extract_youtube_thread_cpu_states.py ../data/PerfettoTraceForRecruitment com.google.android.youtube ../results/youtube_thread_cpu_states.csv`.

### `identify_performance_anomalies.py`
This script takes the processed data from previous extraction scripts (like CPU usage and thread states) and attempts to identify potential performance anomalies. It might look for patterns such as high CPU usage by unexpected processes, long periods of thread blocking, or other indicators of performance issues. The output is a markdown report summarizing these anomalies. To run it: `python3 identify_performance_anomalies.py ../results/cpu_sched_slices.csv ../results/thread_states.csv ../results/long_running_tasks_youtube_main.csv ../results/performance_anomalies_report.md`. This script takes multiple CSV files as input and outputs a markdown file.

### `visualize_top_processes_cpu.py`
This script generates a visualization of CPU usage by the top consuming processes. It takes the CPU scheduling slice data as input and creates a bar chart or a similar plot to represent the CPU time consumed by different processes. This visual representation makes it easier to quickly identify the most CPU-intensive processes in the trace. The output is an image file (e.g., PNG). Execute with: `python3 visualize_top_processes_cpu.py ../results/cpu_sched_slices.csv ../results/top_processes_cpu_usage.png`.




## Results

The analysis performed using the scripts described above yields a collection of insightful results, which are stored in the `results` subdirectory. These results provide a multifaceted view of the system's performance characteristics as captured in the Perfetto trace. Key outputs include detailed CSV files, markdown reports, visualizations, and a final consolidated presentation.

Specifically, the `results` directory contains:

*   **`system_info.csv`**: This file, generated by `extract_metadata.py`, provides an overview of the system on which the trace was captured, including device specifications and trace duration. This contextual information is vital for understanding the environment of the performance data.
*   **`cpu_sched_slices.csv`**: Produced by `extract_cpu_usage.py`, this CSV contains granular data on CPU scheduling events. It allows for in-depth analysis of which processes and threads were running on which CPU cores and for how long, forming the basis for CPU utilization studies.
*   **`thread_states.csv`**: Generated by `extract_thread_states.py`, this file details the various states (e.g., Running, Runnable, Sleeping) of threads throughout the trace. This is crucial for identifying thread-related bottlenecks, such as excessive blocking or waiting times.
*   **`long_running_tasks_youtube_main.csv`**: This CSV, from `extract_long_tasks.py`, lists any tasks on the YouTube application's main thread that exceeded a predefined duration threshold. Such tasks are prime suspects for causing application unresponsiveness.
*   **`youtube_thread_cpu_states.csv`**: Created by `extract_youtube_thread_cpu_states.py`, this file offers a focused look at the CPU activity and states of threads specifically belonging to the YouTube application, helping to understand its resource consumption.
*   **`performance_anomalies_report.md`**: This markdown document, generated by `identify_performance_anomalies.py`, synthesizes information from the various CSV files to highlight potential performance issues. It serves as a narrative summary of anomalies detected through the automated analysis.
*   **`top_processes_cpu_usage.png`**: This image file, created by `visualize_top_processes_cpu.py`, provides a graphical representation (likely a bar chart) of the CPU time consumed by the most active processes. This visualization aids in quickly identifying CPU-heavy applications or services.




## How to Replicate

To replicate the analysis presented in this repository, you will need to have Python 3 installed on your system, along with several Python libraries. The original trace file, `PerfettoTraceForRecruitment`, is provided in the `data` directory. The scripts for analysis are located in the `scripts` directory, and the results will be generated in the `results` directory (though pre-generated results are already included for reference).

**1. Environment Setup:**

First, ensure you have Python 3. I recommend using Python 3.11 or newer. You can check your Python version by running `python3 --version` in your terminal.

Next, you will need to install the required Python libraries. These libraries are used by the various analysis scripts. You can install them using pip, Python's package installer. It is highly recommended to use a virtual environment to manage dependencies for this project. If you have `venv` (usually included with Python 3), you can create and activate a virtual environment as follows:

```bash
# Navigate to the root of the cloned repository
cd /path/to/perfetto_analysis_repo

# Create a virtual environment (e.g., named 'venv')
python3 -m venv venv

# Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

Once your virtual environment is activated, install the necessary libraries. The primary libraries used are `pandas` for data manipulation, `matplotlib` for plotting (used by `visualize_top_processes_cpu.py`). The Perfetto trace parsing itself is handled by custom logic within the scripts, which typically involves reading and processing text-based or JSON-like structures if the trace was converted, or directly interacting with Perfetto's own tools if available (though these scripts are self-contained Python). For this project, the scripts directly parse the trace file.





**2. Running the Analysis Scripts:**

All scripts should be run from the `scripts` directory. The commands below assume you are in the `scripts` directory. If not, navigate there first (`cd /path/to/perfetto_analysis_repo/scripts`). The trace file is expected to be in `../data/` and outputs will be directed to `../results/` relative to the `scripts` directory.

*   **Extract Metadata:**
    ```bash
    python3 extract_metadata.py ../data/PerfettoTraceForRecruitment ../results/system_info.csv
    ```

*   **Extract CPU Usage:**
    ```bash
    python3 extract_cpu_usage.py ../data/PerfettoTraceForRecruitment ../results/cpu_sched_slices.csv
    ```

*   **Extract Thread States:**
    ```bash
    python3 extract_thread_states.py ../data/PerfettoTraceForRecruitment ../results/thread_states.csv
    ```

*   **Extract Long Tasks from YouTube Main Thread:**
    ```bash
    python3 extract_long_tasks.py ../data/PerfettoTraceForRecruitment com.google.android.youtube ../results/long_running_tasks_youtube_main.csv
    ```

*   **Extract YouTube Thread CPU States:**
    ```bash
    python3 extract_youtube_thread_cpu_states.py ../data/PerfettoTraceForRecruitment com.google.android.youtube ../results/youtube_thread_cpu_states.csv
    ```

*   **Identify Performance Anomalies:**
    This script depends on the outputs of `extract_cpu_usage.py`, `extract_thread_states.py`, and `extract_long_tasks.py`.
    ```bash
    python3 identify_performance_anomalies.py ../results/cpu_sched_slices.csv ../results/thread_states.csv ../results/long_running_tasks_youtube_main.csv ../results/performance_anomalies_report.md
    ```

*   **Visualize Top Processes CPU Usage:**
    This script depends on the output of `extract_cpu_usage.py`.
    ```bash
    python3 visualize_top_processes_cpu.py ../results/cpu_sched_slices.csv ../results/top_processes_cpu_usage.png
    ```






