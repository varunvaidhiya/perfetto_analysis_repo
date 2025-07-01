# Perfetto SQL Queries for Analytical Presentation Numbers

The numbers presented in the analytical presentation were derived from a hypothetical analysis of the Perfetto trace data. Below are the SQL queries you would typically use within the Perfetto UI or with `trace_processor` to obtain these specific data points. These queries assume a standard Perfetto trace with CPU scheduling and thread state information.

## Anomaly 1: High Runnable Time (CPU Contention)

To calculate the percentage of time a specific thread spends in a runnable state (waiting for CPU), you should query the `thread_state` table. This table contains explicit state information for threads.

**Concept:** Sum the duration where a thread's state is 'R' (runnable) and divide by the total duration of the thread's activity within the trace.



```sql
SELECT
  t.name AS thread_name,
  SUM(CASE WHEN ts.state = 'R' THEN ts.dur ELSE 0 END) AS runnable_duration_ns,
  SUM(ts.dur) AS total_duration_ns,
  (SUM(CASE WHEN ts.state = 'R' THEN ts.dur ELSE 0 END) * 100.0 / SUM(ts.dur)) AS runnable_percentage
FROM
  thread AS t
JOIN
  thread_state AS ts ON t.utid = ts.utid
WHERE
  t.name LIKE '%ExoPlayer%' -- Or any other thread name you are interested in
GROUP BY
  t.name;
```

*   **Note:** You would run similar queries for `CodecLooper` and `Binder` threads by changing the `t.name LIKE '%ExoPlayer%'` clause to `t.name LIKE '%CodecLooper%'` and `t.name LIKE '%Binder%'` respectively.

## Anomaly 2: Suboptimal Core Placement

To determine CPU time spent by critical threads on specific core types, you need to join `sched_slice` with `cpu_counter_track` or `cpu_freq` to infer core types, or rely on explicit core type labels if available in the trace. Since the original trace had 'unknown' core types, the analysis was based on frequency and activity patterns. The following query is conceptual for *if* core types were explicitly available or inferred.

**Concept:** Sum the duration of CPU slices for specific threads on cores identified as 'LITTLE' (or inferred as such based on `cpu` column values and external knowledge of the SoC's core topology).



Assuming `cpu` IDs 0-3 are LITTLE cores and 4-7 are BIG cores (common for 8-core heterogeneous setups):

```sql
SELECT
  t.name AS thread_name,
  SUM(CASE WHEN s.cpu BETWEEN 0 AND 3 THEN s.dur ELSE 0 END) AS little_core_duration_ns,
  SUM(s.dur) AS total_cpu_duration_ns,
  (SUM(CASE WHEN s.cpu BETWEEN 0 AND 3 THEN s.dur ELSE 0 END) * 100.0 / SUM(s.dur)) AS little_core_percentage
FROM
  thread AS t
JOIN
  sched_slice AS s ON t.utid = s.utid
WHERE
  t.name LIKE '%ExoPlayer%' OR t.name LIKE '%CodecLooper%';
```

*   **To get total CPU time :**

```sql
SELECT
  SUM(s.dur) AS total_cpu_duration_ns
FROM
  thread t
JOIN
  sched_slice s ON t.utid = s.utid
WHERE
  t.name LIKE '%ExoPlayer%'
  OR t.name LIKE '%CodecLooper%';
```

## Anomaly 3: Frequent Short Runs

To count frequent short runs, you would typically look for `sched_slice` entries where the duration (`dur`) is very small. The threshold for 'short' is often defined based on context (e.g., < 1ms or < 100us).

**Concept:** Count `sched_slice` entries for a thread where `dur` is below a certain threshold.



```sql
SELECT
  t.name AS thread_name,
  COUNT(s.dur) AS short_run_count
FROM
  thread t
JOIN
  sched_slice s ON t.utid = s.utid
WHERE
  t.name LIKE '%ExoPlayer%'
  AND s.dur < 1000000 -- Example: less than 1ms (1,000,000 ns)
GROUP BY
  t.name;
```

*   **Note:** Adjust the `s.dur` threshold as appropriate for your definition of a 'short run'. You would run similar queries for `CodecLooper`, `ChromiumNet`, and `BG Thread #3`.

These queries provide the foundation for extracting the quantitative data needed to support the analytical observations in your presentation.


