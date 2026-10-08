# Aegis One

Aegis One is an intelligent security operations and intrusion detection platform featuring machine learning-based threat classification, backend API services with PostgreSQL event storage, and an interactive Next.js dashboard.

## Architecture

- **Machine Learning (`ml/`)**: CICIDS2017 intrusion detection models powered by XGBoost for multi-class security event classification.
- **Backend API (`backend/`)**: FastAPI REST service providing database connectivity, security event queries, and real-time inference endpoints.
- **Frontend Dashboard (`frontend/`)**: Modern Next.js application with Tailwind CSS for visualizing security events, network alerts, and telemetry.
- **Data Engine (`data/`)**: Data pipelines and metadata tracking for processing network intrusion datasets.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL

### Backend & ML Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install fastapi uvicorn psycopg2-binary xgboost scikit-learn pandas numpy python-dotenv
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
   ```bash
   cp .env.example .env
   ```

4. Run the API:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.
