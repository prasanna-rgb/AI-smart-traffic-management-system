# 🚦 AI Smart Traffic Management System using CrewAI

A production-ready, modular, and scalable Agentic AI system built with **Python 3.11**, **CrewAI**, **FastAPI**, **Streamlit**, and **SQLite/PostgreSQL**.

This project features **6 autonomous AI agents** collaborating sequentially to monitor urban traffic telemetry, predict congestion, prioritize emergency vehicles with zero-wait Green Corridors, dynamically optimize traffic signal timing, notify citizens, and compile environmental sustainability analytics.

---

## 🏗️ Architecture & Agent Workflow

### Sequential Agent Execution Pipeline

```mermaid
graph TD
    A[📡 CCTV / IoT Traffic Telemetry Input] --> B[🤖 1. Traffic Monitoring Agent]
    B -->|Traffic Report| C[🔮 2. Congestion Prediction Agent]
    C -->|Congestion Score & Risk| D[🚨 3. Emergency Vehicle Agent]
    D -->|Green Corridor Status| E[🚦 4. Signal Optimization Agent]
    E -->|Optimized Timing Splits| F[📢 5. Citizen Communication Agent]
    F -->|Public Advisories| G[📈 6. Analytics Agent]
    G --> H[💾 SQLite / PostgreSQL Database]
    G --> I[📊 Streamlit Real-Time Dashboard & FastAPI REST APIs]
```

### Specialized Agents Breakdown

| Agent | Module | Role & Responsibilities | Key Output Fields |
| :--- | :--- | :--- | :--- |
| **1. Traffic Monitoring Agent** | `agents/traffic_monitor.py` | Continuously monitors vehicle counts, average speed, road occupancy, accident reports, and emergency presence. | `road`, `vehicles`, `density`, `average_speed`, `accident`, `emergency_vehicle`, `weather` |
| **2. Congestion Prediction Agent** | `agents/congestion_agent.py` | Calculates congestion score (0–100), predicts traffic trends, estimates delays, and recommends bypass routes. | `congestion_score`, `risk_level`, `predicted_trend`, `estimated_delay_minutes`, `recommended_alternate_roads` |
| **3. Emergency Vehicle Agent** | `agents/emergency_agent.py` | Detects Ambulances, Fire Trucks, and Police Vehicles; locks Green Corridors and overrides signal phases. | `emergency_detected`, `green_corridor_active`, `corridor_route`, `signal_override_status` |
| **4. Signal Optimization Agent** | `agents/signal_agent.py` | Dynamically extends green signal durations (+15s to +60s), reduces waiting time, and clears intersection queues. | `junction`, `current_green_time_sec`, `recommended_green_time_sec`, `dynamic_increase_sec`, `signal_mode` |
| **5. Citizen Communication Agent** | `agents/citizen_agent.py` | Broadcasts traffic warnings, accident alerts, road closure notices, and detour directions via VMS/Apps. | `alert_id`, `severity`, `title`, `message`, `affected_road`, `alternate_route` |
| **6. Analytics Agent** | `agents/analytics_agent.py` | Computes road performance index, estimates CO₂ carbon emissions, and generates executive sustainability insights. | `carbon_emission_kg`, `road_performance_score`, `key_insights` |

---

## 📁 Project Structure

```
smart_traffic_ai/
├── agents/
│   ├── traffic_monitor.py     # Agent 1: Telemetry analysis & Traffic Report generation
│   ├── congestion_agent.py    # Agent 2: Congestion scoring (0-100) & bypass routing
│   ├── emergency_agent.py     # Agent 3: First-responder detection & Green Corridor locking
│   ├── signal_agent.py        # Agent 4: Dynamic green signal extension & queue clearing
│   ├── citizen_agent.py       # Agent 5: Public advisories & alert broadcasting
│   └── analytics_agent.py     # Agent 6: Road performance index & CO2 carbon emission tracking
│
├── tasks/
│   └── traffic_tasks.py       # CrewAI Task definitions mapped to agents
│
├── tools/
│   ├── database_tools.py      # Database query tools for CrewAI agents
│   ├── simulation_tools.py    # Probabilistic traffic telemetry generator
│   ├── pdf_generator.py       # Executive PDF report generator
│   └── audio_announcer.py     # Voice synthesizer for browser audio alerts
│
├── config/
│   └── settings.py            # System configuration, environment loader & Gemini LLM factory
│
├── database/
│   ├── db.py                  # SQLAlchemy engine, sessions, & data access layer
│   ├── models.py              # ORM tables: traffic_data, traffic_reports, alerts, analytics
│   └── traffic_app.db         # SQLite Database file
│
├── api/
│   └── routes.py              # FastAPI REST endpoints (/traffic/report, /traffic/analytics, etc.)
│
├── dashboard/
│   └── app.py                 # Streamlit multi-tab interactive command center UI
│
├── models/
│   └── schemas.py             # Pydantic schemas for request/response validation
│
├── data/
│   └── sample_data.json       # Benchmark traffic telemetry datasets
│
├── crew.py                    # SmartTrafficCrew orchestrator class
├── main.py                    # FastAPI server entry point
├── requirements.txt           # Project Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # System documentation
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.11** (or Python 3.9+)
- **Git**

### Step 1: Clone Repository & Navigate to Directory
```bash
git clone https://github.com/your-repo/smart_traffic_ai.git
cd smart_traffic_ai
```

### Step 2: Create Environment File
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to supply your **Google Gemini API Key**:
```ini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
LLM_MODEL=gemini/gemini-1.5-flash
DATABASE_URL=sqlite:///./database/traffic_app.db
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True
```
> *Note: If no Gemini API key is provided, the system automatically falls back to an intelligent, high-speed deterministic rule engine.*

### Step 3: Install Python Dependencies
```bash
py -m pip install -r requirements.txt
```

---

## 🚀 Running the System

### Option A: Run FastAPI REST API Server
Launch the backend server:
```bash
py main.py
```
- **REST API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Option B: Run Streamlit Interactive Dashboard
Launch the dashboard in a separate terminal:
```bash
py -m streamlit run dashboard/app.py
```
- **Dashboard URL**: `http://localhost:8501`

---

## 🌐 REST API Documentation

| Method | Endpoint | Description | Sample Query / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/traffic/status` | System operational health, agent count, active corridors, and DB connectivity. | `GET /traffic/status` |
| `GET` | `/traffic/report` | Fetch latest CrewAI multi-agent decision reports. | `GET /traffic/report?limit=10` |
| `GET` | `/traffic/analytics` | Retrieve historical carbon footprint ($CO_2$), delays, and performance metrics. | `GET /traffic/analytics?limit=20` |
| `POST` | `/traffic/input` | Execute 6-agent Crew pipeline on custom telemetry or simulation tick. | Body: `{"road": "Main Road", "vehicle_count": 82, "average_speed": 31, "accident": false, "emergency_vehicle": true, "weather": "Rain"}` |

---

## 🔮 Future Integration Readiness

The modular architecture of `smart_traffic_ai` is designed for seamless hardware and vision integration without breaking existing agent code:

1. **YOLOv8 & OpenCV Video Stream Feed**:
   - Replace `TrafficSimulator.generate_random_telemetry()` with a YOLOv8 bounding box counting tool in `tools/` to ingest real-time CCTV camera streams.
2. **IoT Sensor & Radar Gateway**:
   - Connect edge magnetic loop / radar sensors directly to `POST /traffic/input` via MQTT or HTTP webhooks.
3. **Google Maps API Live Traffic Layer**:
   - The GIS visualizer in `dashboard/app.py` already includes Google Maps satellite tile rendering and direct navigation link generators.
4. **PostgreSQL Migration**:
   - Update `DATABASE_URL` in `.env` to `postgresql://user:password@localhost:5432/smart_traffic` — SQLAlchemy handles full ORM translation automatically.
