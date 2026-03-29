import os
from dotenv import load_dotenv

load_dotenv()

# --- Model Selection: OpenAI via LiteLLM ---
from google.adk.models.lite_llm import LiteLlm
MODEL_FAST = LiteLlm(model="openai/gpt-4o-mini")
MODEL_SMART = LiteLlm(model="openai/gpt-4o-mini")
MODEL_SYNTHESIS = LiteLlm(model="openai/gpt-4o")

# --- Databricks ---
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")

# Whether to use real Delta or sample data
USE_SAMPLE_DATA = not all([DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_HTTP_PATH])

# --- External APIs ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- Databricks Model Serving Endpoints ---
DATABRICKS_SERVING_HOST = os.getenv(
    "DATABRICKS_SERVING_HOST",
    os.getenv("DATABRICKS_HOST", "dbc-0e37dbb2-9279.cloud.databricks.com"),
)
BEHAVIORAL_CLASSIFIER_ENDPOINT = "behavioral_classifier_rf"
DEFAULT_PREDICTOR_ENDPOINT = "default_predictor_xgboost"

# --- Crop Data Paths (for local ML models) ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEASONAL_PRICE_CSV = os.path.join(_PROJECT_ROOT, "arthasetu-databricks", "raw_data", "seasonalPrice", "Season_Price_Arrival_5_years.csv")
CROP_DISTRICT_CSV = os.path.join(_PROJECT_ROOT, "arthasetu-databricks", "raw_data", "cropData", "CropDistrictLevelData.csv")

# --- Delta Table Names ---
TABLE_FARMER_PROFILE = "krishirin.loan_advisory.silver_farmer_profile"
TABLE_SCORED_PROFILES = "krishirin.loan_advisory.scored_profiles"
TABLE_DISTRICT_FEATURES = "krishirin.loan_advisory.silver_district_features"
TABLE_CROP_CALENDAR = "krishirin.loan_advisory.silver_crop_calendar"
TABLE_MSP_PRICES = "krishirin.loan_advisory.bronze_msp_prices"
TABLE_PRECALL_ANALYSIS = "krishirin.loan_advisory.precall_analysis"

# --- FAISS ---
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
FAISS_CHUNKS_PATH = os.getenv("FAISS_CHUNKS_PATH", "./data/scheme_chunks.json")
