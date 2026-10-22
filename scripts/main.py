#Temprature and Wind Speed Data Fetching Script

import csv
import requests
from pathlib import Path


API_URL = "https://api.open-meteo.com/v1/forecast"


# Project directories
PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "population.csv"
OUTPUT_FILE = PROJECT_DIR / "data" / "weather_data.csv"




def fetch_weather(city):
   params = {
       "latitude": city["Latitude"],
       "longitude": city["Longitude"],
       "current": "temperature_2m,wind_speed_10m",
       "timezone": "auto",
   }


   try:
       response = requests.get(API_URL, params=params, timeout=20)
       response.raise_for_status()
       current = response.json()["current"]


       return {
           "City": city["City"],
           "Country": city["Country"],
           "Population": city["Population"],
           "Latitude": city["Latitude"],
           "Longitude": city["Longitude"],
           "Temperature_C": current["temperature_2m"],
           "Wind_Speed_kmh": current["wind_speed_10m"],
           "Local_Time": current["time"],
           "Status": "Success",
       }


   except (requests.RequestException, KeyError, ValueError) as error:
       print(f"Failed: {city['City']} - {error}")


       return {
           "City": city["City"],
           "Country": city["Country"],
           "Population": city["Population"],
           "Latitude": city["Latitude"],
           "Longitude": city["Longitude"],
           "Temperature_C": "",
           "Wind_Speed_kmh": "",
           "Local_Time": "",
           "Status": "Failed",
       }




def main():
   if not INPUT_FILE.exists():
       print(f"Input CSV not found: {INPUT_FILE}")
       print("Place population.csv inside the project's data folder.")
       return


   with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
       cities = list(csv.DictReader(file))


   if not cities:
       print("No cities found in the input CSV.")
       return


   results = []


   for index, city in enumerate(cities, start=1):
       print(f"Fetching {index}/{len(cities)}: {city['City']}")
       results.append(fetch_weather(city))


   fieldnames = [
       "City", "Country", "Population", "Latitude", "Longitude",
       "Temperature_C", "Wind_Speed_kmh", "Local_Time", "Status"
   ]


   with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
       writer = csv.DictWriter(file, fieldnames=fieldnames)
       writer.writeheader()
       writer.writerows(results)


   successful = sum(row["Status"] == "Success" for row in results)


   print(f"\nCompleted: {successful}/{len(cities)} cities fetched.")
   print(f"Weather data saved to: {OUTPUT_FILE}")




if __name__ == "__main__":
   main()


# BigQuery Upload Script

from pathlib import Path

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import Forbidden, NotFound, GoogleAPIError



# 1. PROJECT CONFIGURATION


PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_DIR / "data" / "merged_weather_population.csv"
KEY_FILE = PROJECT_DIR / "scripts" / "gcp-key.json"

PROJECT_ID = "igneous-core-512316-g3"
DATASET_ID = "global_weather_data"
TABLE_ID = "current_weather_stats"

TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"



# 2. LOAD AND CLEAN DATA


def load_and_clean_data():
    """Load the merged CSV and perform basic cleaning."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_FILE}\n"
            "Ensure merged_weather_population.csv is inside data/."
        )

    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        raise ValueError("The input CSV contains no data.")

    # Standardize column names for BigQuery
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-zA-Z0-9_]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    # Remove duplicate column names, if any
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(
            f"Duplicate column names after cleaning: {duplicates}"
        )

    # Remove duplicate records
    initial_rows = len(df)
    df = df.drop_duplicates().copy()

    print(f"Input rows: {initial_rows}")
    print(f"Rows after duplicate removal: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Convert common numeric fields to numeric types
    numeric_columns = [
        "population",
        "latitude",
        "longitude",
        "temperature_c",
        "wind_speed_kmh",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    # Convert common date/time fields to datetime
    for column in ["local_time", "datetime", "timestamp"]:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                utc=True,
            )

    # Replace infinite numeric values with missing values
    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)

    return df


# 3. AUTHENTICATE WITH GOOGLE CLOUD


def create_bigquery_client():
    """Authenticate using the service account JSON key."""

    if not KEY_FILE.exists():
        raise FileNotFoundError(
            f"Service account key not found: {KEY_FILE}\n"
            "Place gcp-key.json inside the scripts/ directory."
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(KEY_FILE),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    print(f"Service account: {credentials.service_account_email}")
    print(f"Target project: {PROJECT_ID}")

    if credentials.project_id and credentials.project_id != PROJECT_ID:
        print(
            "WARNING: The project_id in the JSON key differs from "
            "PROJECT_ID in this script. Verify that this is intentional."
        )

    client = bigquery.Client(
        project=PROJECT_ID,
        credentials=credentials,
    )

    return client


# 4. UPLOAD DATAFRAME TO BIGQUERY


def upload_to_bigquery(client, df):
    """Upload the cleaned DataFrame to the BigQuery table."""

    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"\nUploading {len(df)} rows to:")
    print(TABLE_REF)

    job = client.load_table_from_dataframe(
        df,
        TABLE_REF,
        job_config=job_config,
    )

    # Wait for the BigQuery job to finish
    job.result()

    # Verify the table
    table = client.get_table(TABLE_REF)

    print("\nUpload successful!")
    print(f"Table: {table.project}.{table.dataset_id}.{table.table_id}")
    print(f"Rows in table: {table.num_rows}")
    print(f"Columns in table: {len(table.schema)}")

# 5. MAIN EXECUTION


def main():
    try:
        df = load_and_clean_data()
        client = create_bigquery_client()
        upload_to_bigquery(client, df)

    except FileNotFoundError as error:
        print(f"\nFILE ERROR: {error}")
        raise

    except Forbidden as error:
        print("\nPERMISSION ERROR: BigQuery denied the request.")
        print("Verify that the service account has:")
        print("1. BigQuery Job User at the project level.")
        print("2. BigQuery Data Editor on the target dataset.")
        print(f"Target project: {PROJECT_ID}")
        print(f"Target dataset: {DATASET_ID}")
        print(f"Details: {error}")
        raise

    except NotFound as error:
        print("\nRESOURCE NOT FOUND.")
        print(
            "Check the project ID, dataset ID, and whether "
            "the dataset exists in the correct location."
        )
        print(f"Details: {error}")
        raise

    except GoogleAPIError as error:
        print(f"\nGOOGLE CLOUD API ERROR: {error}")
        raise

    except Exception as error:
        print(f"\nUNEXPECTED ERROR: {type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    main()


#Data Cleaning and Merging Python Script

population_df= pd.read_csv('/content/population.csv')


population_df.head()

weather_df= pd.read_csv('/content/weather_data.csv')
weather_df.head()

print("Weather columns:")
print(weather_df.columns.tolist())

print("\nPopulation columns:")
print(population_df.columns.tolist())

print("Weather shape:", weather_df.shape)

print("Population shape:", population_df.shape)

# Select only the necessary columns from the weather dataset
weather_columns = [
    'City',
    'Country',
    'Temperature_C',
    'Wind_Speed_kmh'
]

weather_clean = weather_df[weather_columns]

# Merge using City and Country
merged_df = pd.merge(
    population_df,
    weather_clean,
    on=['City', 'Country'],
    how='left'
)

# Display the merged dataset
display(merged_df.head())

print("Merged dataset shape:", merged_df.shape)

# Check missing values
print(merged_df.isnull().sum())

# Check duplicate city-country combinations
print(
    "Duplicate city-country rows:",
    merged_df.duplicated(subset=['City', 'Country']).sum()
)

# Check the data types
print(merged_df.dtypes)


# Remove commas and convert Population to numeric
merged_df['Population'] = pd.to_numeric(
    merged_df['Population']
        .astype(str)
        .str.replace(',', '', regex=False),
    errors='coerce'
).astype('Int64')

# Verify the datatype
print(merged_df['Population'].dtype)

print(merged_df.dtypes)

merged_df['Temperature_Category'] = np.select(
    [
        merged_df['Temperature_C'] < 15,
        merged_df['Temperature_C'].between(15, 25),
        merged_df['Temperature_C'] > 25
    ],
    ['Cold', 'Mild', 'Hot'],
    default='Unknown'
)

# Display the results
display(merged_df[['Temperature_C', 'Temperature_Category']].head(10))


merged_df.head()

# Save the DataFrame as a CSV file
merged_df.to_csv('merged_weather_population.csv', index=False)


# Download the CSV file
from google.colab import files
files.download('merged_weather_population.csv')

