import pandas as pd
import matplotlib.pyplot as plt
import sys

if len(sys.argv) != 3:
    print("Usage: python visualize_top_processes_cpu.py <cpu_sched_csv_path> <output_image_path>")
    sys.exit(1)

cpu_sched_csv = sys.argv[1]
output_image = sys.argv[2]

try:
    df = pd.read_csv(cpu_sched_csv)
except FileNotFoundError:
    print(f"Error: The file {cpu_sched_csv} was not found.")
    sys.exit(1)
except pd.errors.EmptyDataError:
    print(f"Error: The file {cpu_sched_csv} is empty.")
    # Create a blank image with a message if file is empty, then exit
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "CPU scheduling data file is empty.", ha='center', va='center')
    ax.axis('off')
    plt.savefig(output_image)
    print(f"Empty data visualization saved to {output_image}")
    sys.exit(0)

if df.empty:
    print("The CPU scheduling data is empty. Cannot generate visualization.")
    # Create a blank image with a message
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "No CPU scheduling data available for visualization", ha='center', va='center')
    ax.axis('off')
    plt.savefig(output_image)
    print(f"Empty data visualization saved to {output_image}")
    sys.exit(0)

# Calculate total CPU time per process
# Assuming 'dur' is the column for duration in nanoseconds
process_cpu_time = df.groupby('process_name')['dur'].sum().sort_values(ascending=False) / 1_000_000 # Convert to ms

# Get top N processes (e.g., top 10)
top_n = 10
top_processes = process_cpu_time.head(top_n)

if top_processes.empty:
    print("No process CPU time data to visualize after grouping.")
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "No process CPU time data to visualize", ha='center', va='center')
    ax.axis('off')
    plt.savefig(output_image)
    print(f"Empty data visualization saved to {output_image}")
    sys.exit(0)

# Create the bar chart
plt.figure(figsize=(12, 8))
ax = top_processes.plot(kind='bar')
plt.title(f'Top {top_n} CPU Consuming Processes')
plt.xlabel('Process Name')
plt.ylabel('Total CPU Time (ms)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Add labels to bars
for i, v in enumerate(top_processes):
    ax.text(i, v + (top_processes.max() * 0.01), f"{v:.2f}", color='blue', ha='center', fontweight='bold')

try:
    plt.savefig(output_image)
    print(f"CPU usage visualization saved to {output_image}")
except Exception as e:
    print(f"Error saving visualization: {e}")
    sys.exit(1)

