import tkinter as tk
from tkinter import messagebox
from collections import defaultdict
import time
  
# ---------------- GUI SETUP ---------------- #
root = tk.Tk()
root.title("Deadlock Simulator with All Strategies")

frame = tk.Frame(root)
frame.pack(pady=10)

log_box = tk.Text(root, height=12, width=70)
log_box.pack(pady=10)

def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.yview(tk.END)

# ---------------- STATE ---------------- #
processes = ['P1', 'P2', 'P3']
resources = ['R1', 'R2']
resource_order = {'R1': 1, 'R2': 2}

allocation = defaultdict(lambda: None)
held_resources = defaultdict(set)
waiting = defaultdict(list)
wait_for_graph = defaultdict(set)

current_strategy = tk.StringVar()
current_strategy.set("resource_ordering")  # Default

def reset_state():
    allocation.clear()
    held_resources.clear()
    waiting.clear()
    wait_for_graph.clear()
    log("🔄 State reset.")

# ---------------- PREVENTION METHODS ---------------- #
def resource_ordering_request(process, resource):
    for held in held_resources[process]:
        if resource_order[held] > resource_order[resource]:
            log(f"❌ {process} violates resource ordering by requesting {resource} after {held}")
            return False
    if allocation[resource] is None:
        allocation[resource] = process
        held_resources[process].add(resource)
        log(f"✅ {resource} allocated to {process}")
    else:
        waiting[process].append(resource)
        wait_for_graph[process].add(allocation[resource])
        log(f"⏳ {process} is waiting for {resource} (held by {allocation[resource]})")
    return True

def hold_and_wait_denial_request(process, resource):
    if held_resources[process]:
        log(f"❌ {process} cannot request {resource} while holding {held_resources[process]}")
        return False
    if allocation[resource] is None:
        allocation[resource] = process
        held_resources[process].add(resource)
        log(f"✅ {resource} allocated to {process}")
    else:
        waiting[process].append(resource)
        wait_for_graph[process].add(allocation[resource])
        log(f"⏳ {process} is waiting for {resource} (held by {allocation[resource]})")
    return True

# ---------------- DETECTION METHODS ---------------- #
def detect_by_wait_for_graph():
    visited = set()
    stack = set()

    def has_cycle(p):
        if p not in visited:
            visited.add(p)
            stack.add(p)
            for neighbor in wait_for_graph[p]:
                if neighbor not in visited and has_cycle(neighbor):
                    return True
                elif neighbor in stack:
                    return True
            stack.remove(p)
        return False

    for p in processes:
        if has_cycle(p):
            return True
    return False

def detect_by_simplified_bankers():
    available = {r for r in resources if allocation[r] is None}
    temp_held = {p: held_resources[p].copy() for p in processes}
    temp_waiting = {p: waiting[p][:] for p in processes}

    safe = set()
    while len(safe) < len(processes):
        progress = False
        for p in processes:
            if p in safe:
                continue
            if all(res in available for res in temp_waiting[p]):
                safe.add(p)
                available.update(temp_held[p])
                progress = True
        if not progress:
            return True  # unsafe state, deadlock possible
    return False

# ---------------- DISPATCHERS ---------------- #
def request_resource(process, resource):
    start = time.time()

    strategy = current_strategy.get()
    if strategy == "resource_ordering":
        success = resource_ordering_request(process, resource)
    elif strategy == "hold_and_wait":
        success = hold_and_wait_denial_request(process, resource)
    else:
        log("⚠ Prevention strategy not implemented.")
        success = False

    duration = round((time.time() - start) * 1000, 2)
    if success:
        log(f"⏱ Time taken: {duration} ms")

def release_resource(process, resource):
    if allocation[resource] == process:
        allocation[resource] = None
        held_resources[process].discard(resource)
        log(f"🔓 {process} released {resource}")

def detect_deadlock():
    start = time.time()
    strategy = current_strategy.get()

    if strategy == "wait_for_graph":
        result = detect_by_wait_for_graph()
    elif strategy == "bankers":
        result = detect_by_simplified_bankers()
    else:
        log("⚠ Detection strategy not active.")
        return

    duration = round((time.time() - start) * 1000, 2)
    if result:
        messagebox.showerror("Deadlock Detected", "💥 Deadlock has occurred!")
        log("💥 Deadlock detected.")
    else:
        messagebox.showinfo("No Deadlock", "✅ No deadlock detected.")
        log("✅ No deadlock found.")
    log(f"⏱ Detection Time: {duration} ms")

# ---------------- GUI CONTROLS ---------------- #
def make_buttons():
    for p in processes:
        for r in resources:
            tk.Button(frame, text=f"{p} requests {r}", width=20,
                      command=lambda p=p, r=r: request_resource(p, r)).pack(pady=2)

    for p in processes:
        for r in resources:
            tk.Button(frame, text=f"{p} releases {r}", width=20,
                      command=lambda p=p, r=r: release_resource(p, r)).pack(pady=2)

    tk.Button(root, text="Detect Deadlock", bg='red', fg='white',
              command=detect_deadlock).pack(pady=10)

    tk.Button(root, text="Reset State", bg='blue', fg='white',
              command=reset_state).pack(pady=5)

def strategy_menu():
    tk.Label(root, text="Select Strategy:").pack()
    options = {
        "Resource Ordering": "resource_ordering",
        "Hold and Wait Denial": "hold_and_wait",
        "Wait-for Graph Detection": "wait_for_graph",
        "Banker's Algorithm": "bankers"
    }
    for label, value in options.items():
        tk.Radiobutton(root, text=label, variable=current_strategy,
                       value=value).pack(anchor="w")

# ---------------- MAIN ---------------- #
strategy_menu()
make_buttons()
reset_state()
root.mainloop()