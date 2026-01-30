import tkinter as tk
from tkinter import messagebox, Toplevel
import math


class NFAEngine:
    def __init__(self):
        self.alphabet = set()
        self.transitions = {}
        self.start_states = set()
        self.final_states = set()
        self.states_count = 0

    def add_transition(self, u, sym, v):
        key = (u, sym)
        if key not in self.transitions:
            self.transitions[key] = set()
        self.transitions[key].add(v)

    def get_epsilon_closure(self, states):
        stack = list(states)
        closure = set(states)
        while stack:
            u = stack.pop()
            if (u, '#') in self.transitions:
                for v in self.transitions[(u, '#')]:
                    if v not in closure:
                        closure.add(v)
                        stack.append(v)
        return closure

    def reset_simulation(self, start_nodes, input_str):
        self.start_states = start_nodes
        self.input_string = input_str
        self.current_states = self.get_epsilon_closure(self.start_states)


# --- Trace Window ---
class TraceWindow(Toplevel):
    def __init__(self, master, engine, input_string):
        super().__init__(master)
        self.title("Trace Input (Computation Tree)")
        self.geometry("1100x800")
        self.engine = engine
        self.input_string = input_string

        self.levels = []
        self.node_id_counter = 0
        self.current_level_index = 0

        self.prepare_trace_data()

        ctrl_frame = tk.Frame(self, bg="#eee", pady=5)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_next = tk.Button(ctrl_frame, text="Show Next Step", command=self.draw_next_level, bg="#2196F3",
                                  fg="white", font=("Arial", 11, "bold"))
        self.btn_next.pack()

        self.canvas = tk.Canvas(self, bg="white", scrollregion=(0, 0, 3000, 5000))
        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas.create_text(60, 40, text="Start", font=("Arial", 14, "bold"), fill="black")
        self.draw_next_level()

    def get_id(self):
        self.node_id_counter += 1
        return self.node_id_counter

    def prepare_trace_data(self):
        level0_nodes = []
        for s in sorted(list(self.engine.start_states)):
            level0_nodes.append({'id': self.get_id(), 'state': s, 'parent_ids': [], 'link_type': None})

        queue = list(level0_nodes)
        processed_pairs = set()
        idx = 0

        while idx < len(queue):
            curr_node = queue[idx]
            idx += 1
            state = curr_node['state']
            if (state, '#') in self.engine.transitions:
                targets = self.engine.transitions[(state, '#')]
                for t in targets:
                    if (curr_node['id'], t) not in processed_pairs:
                        processed_pairs.add((curr_node['id'], t))
                        new_node = {'id': self.get_id(), 'state': t, 'parent_ids': [curr_node['id']],
                                    'link_type': 'horizontal'}
                        level0_nodes.append(new_node)
                        queue.append(new_node)

        self.levels.append({'nodes': level0_nodes, 'char': 'Start'})
        current_level_nodes = level0_nodes

        total_chars = len(self.input_string)
        for i, char in enumerate(self.input_string):
            next_level_nodes = []
            is_last_step = (i == total_chars - 1)
            merged_states_map = {}

            for parent in current_level_nodes:
                p_state = parent['state']
                if (p_state, char) in self.engine.transitions:
                    targets = self.engine.transitions[(p_state, char)]
                    for t in targets:
                        if is_last_step:
                            if t in merged_states_map:
                                existing_node = merged_states_map[t]
                                existing_node['parent_ids'].append(parent['id'])
                                continue
                        new_node = {'id': self.get_id(), 'state': t, 'parent_ids': [parent['id']],
                                    'link_type': 'vertical'}
                        next_level_nodes.append(new_node)
                        if is_last_step: merged_states_map[t] = new_node

            queue = list(next_level_nodes)
            idx = 0
            processed_pairs = set()
            while idx < len(queue):
                curr_node = queue[idx]
                idx += 1
                state = curr_node['state']
                if (state, '#') in self.engine.transitions:
                    targets = self.engine.transitions[(state, '#')]
                    for t in targets:
                        if (curr_node['id'], t) not in processed_pairs:
                            processed_pairs.add((curr_node['id'], t))
                            new_node = {'id': self.get_id(), 'state': t, 'parent_ids': [curr_node['id']],
                                        'link_type': 'horizontal'}
                            next_level_nodes.append(new_node)
                            queue.append(new_node)

            self.levels.append({'nodes': next_level_nodes, 'char': char})
            current_level_nodes = next_level_nodes

    def draw_next_level(self):
        if self.current_level_index >= len(self.levels): return
        i = self.current_level_index
        data = self.levels[i]

        row_height = 120
        top_margin = 80
        line_y = top_margin + (i * row_height)
        r = 20
        self.canvas.create_line(20, line_y, 2900, line_y, fill="#90caf9", width=2)

        if i < len(self.levels) - 1:
            next_char = self.levels[i + 1]['char']
            self.canvas.create_text(60, line_y + (row_height / 2), text=next_char, font=("Arial", 16, "bold"),
                                    fill="#1565c0")

        nodes = data['nodes']
        count = len(nodes)
        if not hasattr(self, 'all_coords'): self.all_coords = {}
        if i not in self.all_coords: self.all_coords[i] = {}

        if count > 0:
            nodes.sort(key=lambda x: x['parent_ids'][0] if x['parent_ids'] else -1)
            width_span = max(600, count * 100)
            spacing = width_span / (count + 1)
            offset_x = (1000 - width_span) / 2 if width_span < 1000 else 50

            for j, node in enumerate(nodes):
                x = offset_x + spacing * (j + 1)
                self.all_coords[i][node['id']] = (x, line_y)

                for pid in node['parent_ids']:
                    parent_coords = None
                    if node['link_type'] == 'vertical':
                        if (i - 1) in self.all_coords: parent_coords = self.all_coords[i - 1].get(pid)
                    else:
                        parent_coords = self.all_coords[i].get(pid)

                    if parent_coords:
                        px, py = parent_coords
                        if node['link_type'] == 'vertical':
                            self.canvas.create_line(px, py + r, x, line_y - r, arrow=tk.LAST, arrowshape=(14, 16, 6),
                                                    fill="black", width=2)
                        else:
                            if x > px:
                                sx, ex = px + r, x - r
                            else:
                                sx, ex = px - r, x + r
                            mid_x = (sx + ex) / 2
                            mid_y = line_y - 45
                            self.canvas.create_line(sx, py - r / 2, mid_x, mid_y, ex, line_y - r / 2, smooth=True,
                                                    arrow=tk.LAST, arrowshape=(14, 16, 6), fill="red", width=2,
                                                    dash=(4, 2))
                            self.canvas.create_text(mid_x, mid_y - 10, text="λ", fill="red", font=("Times", 14, "bold"))

        for node in nodes:
            x, y = self.all_coords[i][node['id']]
            state_name = node['state']
            fill = "white"
            outline = "black"
            width = 1
            if i == len(self.levels) - 1:
                if state_name in self.engine.final_states:
                    fill = "#c8e6c9"
                    outline = "#2e7d32"
                    width = 2

            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=outline, width=width)
            if state_name in self.engine.final_states:
                inner_col = "#2e7d32" if (i == len(self.levels) - 1) else "black"
                self.canvas.create_oval(x - (r - 5), y - (r - 5), x + (r - 5), y + (r - 5), fill=None,
                                        outline=inner_col, width=1)
            self.canvas.create_text(x, y, text=str(state_name), font=("Arial", 11, "bold"))

        self.current_level_index += 1
        if self.current_level_index >= len(self.levels):
            self.btn_next.config(state=tk.DISABLED, text="End of Trace")
            accepted = any(n['state'] in self.engine.final_states for n in self.levels[-1]['nodes'])

            if accepted:
                messagebox.showinfo("Result", "Input ACCEPTED")
            else:
                messagebox.showwarning("Result", "Input REJECTED")


# --- Main GUI ---
class NFAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSC339 - NFA Simulator & Tracer")
        self.root.geometry("1200x900")

        self.bg_color = "#f4f4f4"
        root.configure(bg=self.bg_color)

        self.engine = NFAEngine()
        self.node_coords = {}
        self.node_radius = 25
        self.arrow_style = (20, 25, 8)
        self.drag_data = {"item": None, "x": 0, "y": 0}

        # --- REORGANIZED LAYOUT ---
        # 1. Visualization (TOP)
        visualization_frame = tk.Frame(root, bg="white", relief=tk.SUNKEN, bd=1)
        visualization_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 2. Controls / Menu (BOTTOM)
        menu_frame = tk.Frame(root, bg=self.bg_color, padx=10, pady=10)
        menu_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Visualization Content ---
        tk.Label(visualization_frame, text="State Diagram (Interactive: Drag nodes to arrange)", bg="white",
                 fg="#888").pack(side=tk.TOP, fill=tk.X)
        self.canvas = tk.Canvas(visualization_frame, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        # --- Menu Content (Input Groups) ---

        # Group 1: Definition
        grp_def = tk.LabelFrame(menu_frame, text="1. NFA Definition", bg=self.bg_color, font=("Segoe UI", 10, "bold"),
                                padx=10, pady=10)
        grp_def.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        def add_field(parent, label, default):
            tk.Label(parent, text=label, bg=self.bg_color, anchor="w").pack(fill=tk.X)
            entry = tk.Entry(parent, font=("Consolas", 10))
            entry.pack(fill=tk.X, pady=(0, 5))
            entry.insert(0, default)
            m = tk.Menu(root, tearoff=0)
            m.add_command(label="Paste", command=lambda: entry.event_generate("<<Paste>>"))
            entry.bind("<Button-3>", lambda e: m.tk_popup(e.x_root, e.y_root))
            return entry

        # Empty defaults passed directly
        self.e_alphabet = add_field(grp_def, "Alphabet (e.g., a,b):", "")
        self.e_states = add_field(grp_def, "Number of States:", "")
        self.e_start = add_field(grp_def, "Start State(s):", "")
        self.e_final = add_field(grp_def, "Final State(s):", "")

        tk.Label(grp_def, text="Transitions (from,sym,to) [# for Lambda]:", bg=self.bg_color, anchor="w").pack(
            fill=tk.X)
        self.t_trans = tk.Text(grp_def, height=6, width=30, font=("Consolas", 10))
        self.t_trans.pack(fill=tk.X, pady=(0, 5))
        # No default text insertion for transitions
        m_txt = tk.Menu(root, tearoff=0)
        m_txt.add_command(label="Paste", command=lambda: self.t_trans.event_generate("<<Paste>>"))
        self.t_trans.bind("<Button-3>", lambda e: m_txt.tk_popup(e.x_root, e.y_root))

        tk.Button(grp_def, text="Load NFA & Draw Diagram", command=self.load_nfa,
                  bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), height=2, cursor="hand2").pack(fill=tk.X,
                                                                                                          pady=10)

        # Group 2: Simulation (Right side of the bottom menu)
        right_menu_subframe = tk.Frame(menu_frame, bg=self.bg_color)
        right_menu_subframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        grp_sim = tk.LabelFrame(right_menu_subframe, text="2. Simulation", bg=self.bg_color,
                                font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        grp_sim.pack(fill=tk.X)

        self.e_string = add_field(grp_sim, "Input String:", "")

        tk.Button(grp_sim, text="Trace Input (Tree View)", command=self.open_trace,
                  bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"), height=2, cursor="hand2").pack(fill=tk.X,
                                                                                                          pady=10)

        # Result Label
        self.lbl_res = tk.Label(right_menu_subframe, text="Ready", bg="#e0e0e0", fg="#333",
                                font=("Segoe UI", 12, "bold"), pady=10, relief=tk.RIDGE)
        self.lbl_res.pack(fill=tk.X, pady=(10, 0))

    # --- Logic ---
    def on_press(self, event):
        closest, min_dist = None, float('inf')
        for sid, (x, y) in self.node_coords.items():
            dist = math.hypot(event.x - x, event.y - y)
            if dist < self.node_radius + 10 and dist < min_dist: min_dist, closest = dist, sid
        if closest: self.drag_data["item"] = closest

    def on_drag(self, event):
        if self.drag_data["item"]:
            self.node_coords[self.drag_data["item"]] = (event.x, event.y)
            self.draw_nfa(False)

    def load_nfa(self):
        try:
            self.engine = NFAEngine()

            # Alphabet
            raw_alpha = self.e_alphabet.get().split(',')
            self.engine.alphabet = set(x.strip() for x in raw_alpha if x.strip())

            if not self.engine.alphabet: raise ValueError("Alphabet cannot be empty!")

            # States - Enhanced Error
            states_val = self.e_states.get().strip()
            if not states_val.isdigit():
                raise ValueError(
                    f"Error in 'Number of States':\nExpected an integer (e.g., 4), but you entered '{states_val}'.")

            self.engine.states_count = int(states_val)

            if self.engine.states_count > 10:
                messagebox.showwarning("Warning",
                                       f"You have {self.engine.states_count} states, which exceeds the recommended limit of 10.\n\nThe diagram might be cluttered.")


            raw_starts = self.e_start.get().split(',')
            for s in raw_starts:
                if not s.strip().isdigit():
                    raise ValueError(f"Error in 'Start State(s)':\nExpected integer state IDs, but you entered '{s}'.")
            self.engine.start_states = set(x.strip() for x in raw_starts if x.strip())


            raw_finals = self.e_final.get().split(',')
            for f in raw_finals:
                if f.strip() and not f.strip().isdigit():
                    raise ValueError(f"Error in 'Final State(s)':\nExpected integer state IDs, but you entered '{f}'.")
            self.engine.final_states = set(x.strip() for x in raw_finals if x.strip())


            raw = self.t_trans.get("1.0", tk.END).strip().split('\n')
            for i, line in enumerate(raw):
                line = line.strip()
                if not line: continue
                parts = line.split(',')

                if len(parts) != 3:
                    raise ValueError(
                        f"Error in Line {i + 1}:\nInvalid format '{line}'.\nExpected format: from,symbol,to (e.g., 1,a,2)")
                u, sym, v = parts[0].strip(), parts[1].strip(), parts[2].strip()

                if not u.isdigit() or not v.isdigit():
                    raise ValueError(
                        f"Error in Line {i + 1}:\nState IDs must be integers.\nYou entered: from '{u}' to '{v}'")

                if sym != '#' and sym not in self.engine.alphabet:
                    raise ValueError(
                        f"Error in Line {i + 1}:\nSymbol '{sym}' is not in your defined Alphabet: {self.engine.alphabet}")

                self.engine.add_transition(u, sym, v)

            self.draw_nfa(True)
            self.lbl_res.config(text="NFA Loaded Successfully", fg="green", bg="#e8f5e9")
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            self.lbl_res.config(text="Error Loading NFA", fg="red", bg="#ffebee")

    def open_trace(self):
        if self.engine.states_count == 0: self.load_nfa()
        if self.engine.states_count > 0:
            inp = self.e_string.get().strip()

            if not inp:
                messagebox.showerror("Input Error", "Please enter an input string.\nUse '#' for Empty String.")
                return
            if inp == '#': inp = ""

            for char in inp:
                if char not in self.engine.alphabet:
                    messagebox.showerror("Input Error", f"Invalid character: '{char}'\nNot in Alphabet.")
                    return

            TraceWindow(self.root, self.engine, inp)

            self.engine.reset_simulation(self.engine.start_states, inp)
            curr = self.engine.current_states
            for char in inp:
                nxt = set()
                for s in curr:
                    if (s, char) in self.engine.transitions: nxt.update(self.engine.transitions[(s, char)])
                curr = self.engine.get_epsilon_closure(nxt)

            if not curr.isdisjoint(self.engine.final_states):
                self.lbl_res.config(text="Result: ACCEPTED", fg="white", bg="#2e7d32")
            else:
                self.lbl_res.config(text="Result: REJECTED", fg="white", bg="#c62828")

    def draw_nfa(self, initial=True):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 100: w, h = 800, 600
        if initial:
            cx, cy, r = w // 2, h // 2, min(w, h) // 3
            try:
                cnt = max(1, self.engine.states_count)
            except:
                cnt = 1
            self.node_coords = {}
            for i in range(1, cnt + 1):
                ang = (2 * math.pi / cnt) * i - math.pi / 2
                self.node_coords[str(i)] = (cx + r * math.cos(ang), cy + r * math.sin(ang))

        grouped = {}
        for (u, sym), v_list in self.engine.transitions.items():
            for v in v_list:
                if (u, v) not in grouped: grouped[(u, v)] = []
                grouped[(u, v)].append(sym)

        for (u, v), syms in grouped.items():
            lbl = ",".join(sorted(syms))
            if u in self.node_coords and v in self.node_coords:
                x1, y1 = self.node_coords[u]
                x2, y2 = self.node_coords[v]
                if u == v:
                    ang = math.atan2(y1 - h // 2, x1 - w // 2)
                    off = 0.5 if u in self.engine.start_states else 0
                    fang = ang + off
                    dist = 60
                    ctx = x1 + (self.node_radius + dist) * math.cos(fang)
                    cty = y1 + (self.node_radius + dist) * math.sin(fang)
                    sx = x1 + self.node_radius * math.cos(fang - 0.5)
                    sy = y1 + self.node_radius * math.sin(fang - 0.5)
                    ex = x1 + self.node_radius * math.cos(fang + 0.5)
                    ey = y1 + self.node_radius * math.sin(fang + 0.5)
                    self.canvas.create_line(sx, sy, ctx, cty, ex, ey, smooth=True, arrow=tk.LAST,
                                            arrowshape=self.arrow_style, width=2, fill="#444")
                    self.canvas.create_text(ctx, cty - 10, text=lbl, fill="blue", font="Arial 10 bold")
                else:
                    is_bidirectional = (v, u) in grouped
                    angle = math.atan2(y2 - y1, x2 - x1)
                    if is_bidirectional:
                        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                        dx, dy = x2 - x1, y2 - y1
                        dist = math.hypot(dx, dy)
                        nx, ny = -dy / dist, dx / dist
                        offset = 40
                        ctrl_x = mid_x + nx * offset
                        ctrl_y = mid_y + ny * offset
                        sx = x1 + self.node_radius * math.cos(angle + 0.2)
                        sy = y1 + self.node_radius * math.sin(angle + 0.2)
                        ex = x2 - self.node_radius * math.cos(angle - 0.2)
                        ey = y2 - self.node_radius * math.sin(angle - 0.2)
                        self.canvas.create_line(sx, sy, ctrl_x, ctrl_y, ex, ey, arrow=tk.LAST,
                                                arrowshape=self.arrow_style, smooth=True, fill="#444", width=2)
                        self.canvas.create_text(ctrl_x, ctrl_y, text=lbl, fill="blue", font="Arial 10 bold")
                    else:
                        sx = x1 + self.node_radius * math.cos(angle)
                        sy = y1 + self.node_radius * math.sin(angle)
                        ex = x2 - self.node_radius * math.cos(angle)
                        ey = y2 - self.node_radius * math.sin(angle)
                        self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, arrowshape=self.arrow_style, fill="#444",
                                                width=2)
                        mid_x, mid_y = (sx + ex) / 2, (sy + ey) / 2
                        nx, ny = -math.sin(angle), math.cos(angle)
                        tx = mid_x + nx * 15
                        ty = mid_y + ny * 15
                        self.canvas.create_text(tx, ty, text=lbl, fill="blue", font="Arial 10 bold")

        for n, (x, y) in self.node_coords.items():
            w_line = 3 if n in self.engine.final_states else 1
            self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25, fill="white", outline="black", width=w_line)
            if n in self.engine.final_states:
                self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill=None, outline="black", width=1)
            self.canvas.create_text(x, y, text=n, font="Arial 12 bold")
            if n in self.engine.start_states:
                ang = math.atan2(y - h // 2, x - w // 2)
                sx = x + 80 * math.cos(ang)
                sy = y + 80 * math.sin(ang)
                ex = x + 25 * math.cos(ang)
                ey = y + 25 * math.sin(ang)
                self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, arrowshape=self.arrow_style, width=3,
                                        fill="black")
                self.canvas.create_text(sx, sy - 10, text="Start", font="Arial 11 bold")


if __name__ == "__main__":
    root = tk.Tk()
    app = NFAGUI(root)
    root.mainloop()