import streamlit as st
import plotly.graph_objs as go
import random
import time

# Page configuration
st.set_page_config(
    page_title="Traffix Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

directions = ["North", "South", "East", "West"]

# Constants
yellow_time = 5
max_time = 50
max_green = max_time - yellow_time

# Initialize session state variables
if 'start_green' not in st.session_state:
    st.session_state.start_green = time.time()
if 'green_dir' not in st.session_state:
    st.session_state.green_dir = random.choice(directions)
if 'gr_duration' not in st.session_state:
    st.session_state.gr_duration = 10
if 'signal_start' not in st.session_state:
    st.session_state.signal_start = {d: time.time() for d in directions}
if 'Q_len' not in st.session_state:
    st.session_state.Q_len = {d: random.randint(0, 5) for d in directions}
if 'red_st' not in st.session_state:
    st.session_state.red_st = {d: None for d in directions}
if 'prev_state' not in st.session_state:
    st.session_state.prev_state = {d: "RED" for d in directions}
if 'manual_override' not in st.session_state:
    st.session_state.manual_override = None

default_gr = 10
default_yl = yellow_time
default_red = max_time - (default_gr + default_yl)

def green_time(direction):
    return min((st.session_state.Q_len[direction]/2) - 2, max_green)

def update_Q_len(signal_status):
    current_time = time.time()
    for dir in directions:
        phase = signal_status[dir]
        time_in_phase = current_time - st.session_state.signal_start[dir]

        if phase == "GREEN":
            if time_in_phase >= 1:
                st.session_state.Q_len[dir] = max(0, st.session_state.Q_len[dir] - 3)
                st.session_state.signal_start[dir] = current_time

        elif phase == "RED":
            if time_in_phase < 2:
                continue  
            else:
                if time_in_phase >= 3:
                    st.session_state.Q_len[dir] += 2
                    st.session_state.signal_start[dir] = current_time
        elif phase == "YELLOW":
            if st.session_state.Q_len[dir] > 0 and time_in_phase >= 1:
                st.session_state.Q_len[dir] -= 2
                st.session_state.signal_start[dir] = current_time

def get_current_countdown():
    current_time = time.time()
    passed_time = current_time - st.session_state.start_green
    total_cycle = st.session_state.gr_duration + yellow_time
    remaining_time = max(0, total_cycle - passed_time)
    return remaining_time

def update_wait_times(signal_status):
    """Update wait times based on signal state transitions"""
    current_time = time.time()
    
    for dir in directions:
        current_state = signal_status[dir]
        previous_state = st.session_state.prev_state[dir]
        
        # GREEN/YELLOW to RED 
        if (previous_state in ["GREEN", "YELLOW"]) and current_state == "RED":
            st.session_state.red_st[dir] = current_time
            
        # RED to GREEN/YELLOW
        elif (previous_state == "RED") and current_state in ["GREEN", "YELLOW"]:
            st.session_state.red_st[dir] = None
            
        # Update previous state for next iteration
        st.session_state.prev_state[dir] = current_state

def calculate_current_wait_times():
    """Calculate current wait times for each direction"""
    current_time = time.time()
    wait_times = {}
    
    for dir in directions:
        # If direction is not red or just became red, wait time is 0
        if st.session_state.red_st[dir] is None:
            wait_times[dir] = 0
        else:
            # red and no. of vehicles > 0
            if st.session_state.Q_len[dir] > 0:
                time_elapsed_red = current_time - st.session_state.red_st[dir]
                wait_times[dir] = time_elapsed_red
            else:
                wait_times[dir] = 0  
            
    return wait_times

def signal(manual_override=None):
    status = {d: "RED" for d in directions}
    current_time = time.time()
    passed_time = current_time - st.session_state.start_green
    total_cycle = st.session_state.gr_duration + yellow_time

    if manual_override:
        if st.session_state.green_dir != manual_override:
            st.session_state.green_dir = manual_override
            st.session_state.gr_duration = green_time(manual_override)
            st.session_state.start_green = current_time
            for d in directions:
                st.session_state.signal_start[d] = current_time

        if passed_time < st.session_state.gr_duration:
            status[manual_override] = "GREEN"
        elif passed_time < total_cycle:
            status[manual_override] = "YELLOW"
        else:
            st.session_state.green_dir = max(st.session_state.Q_len, key=st.session_state.Q_len.get)
            st.session_state.gr_duration = green_time(st.session_state.green_dir)
            st.session_state.start_green = current_time
            for d in directions:
                st.session_state.signal_start[d] = current_time
            status[st.session_state.green_dir] = "GREEN"
    else:
        if passed_time < st.session_state.gr_duration:
            status[st.session_state.green_dir] = "GREEN"
        elif passed_time < total_cycle:
            status[st.session_state.green_dir] = "YELLOW"
        else:
            st.session_state.green_dir = max(st.session_state.Q_len, key=st.session_state.Q_len.get)
            st.session_state.gr_duration = green_time(st.session_state.green_dir)
            st.session_state.start_green = current_time
            for d in directions:
                st.session_state.signal_start[d] = current_time
            status[st.session_state.green_dir] = "GREEN"

    return status
    
def get_green_light_remaining_time():
    current_time = time.time()
    passed_time = current_time - st.session_state.start_green
    total_cycle = st.session_state.gr_duration + yellow_time
    remaining_time = max(0, total_cycle - passed_time)

    if passed_time < st.session_state.gr_duration:
        phase = "GREEN"
    elif passed_time < total_cycle:
        phase = "YELLOW"
    else:
        phase = "RED"

    return remaining_time, st.session_state.green_dir, phase

# Main app
st.title("🚦 Traffix Dashboard")

# Manual override section
with st.sidebar:
    st.header("Manual Override")
    
    override_options = ["Automatic"] + [f"Set {d} GREEN" for d in directions]
    selected_override = st.selectbox("Select Direction or Switch to Automatic", override_options)
    
    if st.button("Apply Override"):
        if selected_override == "Automatic":
            st.session_state.manual_override = None
            st.success("Switched to automatic control.")
        else:
            direction = selected_override.split()[1]  # Extract direction from "Set North GREEN"
            st.session_state.manual_override = direction
            st.success(f"Manual override: {direction} is GREEN")

# Auto-refresh placeholder
placeholder = st.empty()

# Auto-refresh the dashboard
with placeholder.container():
    # Get current signal state
    signal_status = signal(st.session_state.manual_override)
    
    # Update wait times based on signal transitions
    update_wait_times(signal_status)

    # Update queue lengths realistically
    update_Q_len(signal_status)

    # Timer and phase info
    remaining_time, green_direction, current_phase = get_green_light_remaining_time()

    # Create layout with columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Queue Length Chart
        queue_fig = go.Figure([
            go.Bar(x=directions, y=[st.session_state.Q_len[d] for d in directions], name="Queue Length")
        ])
        queue_fig.update_layout(
            title="Queue Length by Direction",
            yaxis=dict(
                title="Vehicles",
                range=[0, 25],
                dtick=2,
                showgrid=True,
                gridcolor='lightgray'
            ),
            height=400
        )
        st.plotly_chart(queue_fig, use_container_width=True)
        
        # Wait Time Chart
        wait_times_dict = calculate_current_wait_times()
        wait_times = [wait_times_dict[d] for d in directions]
        avg_wait_time = sum(wait_times) / len(wait_times)

        wait_fig = go.Figure([
            go.Bar(
                x=directions,
                y=wait_times,
                name="Wait Time (seconds)",
                marker_color='blue'
            ),
            go.Scatter(
                x=directions,
                y=[avg_wait_time] * len(directions),
                mode="lines",
                name=f"Average Wait Time ({avg_wait_time:.2f}s)",
                line=dict(color="red", dash="dash")
            )
        ])
        wait_fig.update_layout(
            title=f"Wait Time by Direction",
            xaxis_title="Direction",
            yaxis=dict(
                title="Wait Time (seconds)",
                range=[0, 60],
                dtick=5,
                showgrid=True,
                gridcolor='lightgray'
            ),
            legend=dict(x=0.01, y=0.99),
            height=400
        )
        st.plotly_chart(wait_fig, use_container_width=True)
    
    with col2:
        # Green Light Timer
        st.subheader("🟢 Green Light Timer")
        
        phase_color = {
            "GREEN": "#28a745",
            "YELLOW": "#ffc107",
            "RED": "#dc3545"
        }.get(current_phase, "#6c757d")
        
        timer_container = st.container()
        with timer_container:
            st.markdown(f"**Active Direction:** {green_direction}")
            st.markdown(f"<h2 style='color: {phase_color}'>Countdown: {remaining_time:.0f}s</h2>", 
                       unsafe_allow_html=True)
        
        # Signal Status Display
        st.subheader("Signal Status by Direction")
        
        for d in directions:
            color = {
                "GREEN": "#28a745",
                "RED": "#dc3545",
                "YELLOW": "#ffc107"
            }.get(signal_status[d], "#6c757d")
            
            text_color = 'white' if signal_status[d] != "YELLOW" else 'black'
            
            st.markdown(f"""
            <div style='
                padding: 8px;
                background-color: {color};
                color: {text_color};
                margin-bottom: 5px;
                text-align: center;
                border-radius: 4px;
                font-weight: bold;
            '>
                {d}: {signal_status[d]}
            </div>
            """, unsafe_allow_html=True)

# Auto-refresh every second
time.sleep(1)
st.rerun()