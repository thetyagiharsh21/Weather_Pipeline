# 🌦️ Weather Pipeline

A Python-based data engineering project that combines weather information with population data, performs data cleaning and transformation using Pandas, and loads the processed dataset into Google BigQuery for analytics.

## 📌 Project Overview

The **Weather Pipeline** project demonstrates an end-to-end data processing workflow:

1. Collect weather data for cities using a weather data source or API.
2. Combine weather records with city-level population information.
3. Clean and transform the merged dataset using Python and Pandas.
4. Validate data types and remove duplicate records.
5. Upload the processed data to Google BigQuery for further analysis.

This project provides practical experience with Python, data manipulation, CSV processing, cloud data warehousing, and Google Cloud Platform (GCP).

## 🎯 Objectives

- Integrate weather and demographic datasets.
- Automate data cleaning and preparation.
- Handle missing values and convert columns to appropriate data types.
- Categorize temperatures into meaningful groups.
- Store structured data in BigQuery.
- Establish a foundation for future analytics, visualization, and pipeline automation.

## 🏗️ Project Architecture

```text
Weather Data Source / API
          |
          v
   Weather_data.csv

   population.csv
          |
          v
   Data Integration
   (Pandas / Python)
          |
          v
merged_weather_population.csv
          |
          v
   Data Cleaning
   - Standardize column names
   - Convert data types
   - Remove duplicates
   - Validate records
          |
          v
   Processed DataFrame
          |
          v
     Google BigQuery
          |
          v
   Analytics and Reporting
```

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Pipeline implementation |
| Pandas | Data cleaning, merging, and transformation |
| CSV | Input and intermediate data storage |
| Google BigQuery | Cloud data warehouse |
| Google Cloud IAM | Authentication and access management |
| Google Cloud service account | Programmatic authentication |
| Git and GitHub | Version control and project hosting |

## 📂 Project Structure

```text
Weather_Pipeline/
│
├── data/
│   ├── population.csv
│   ├── Weather_data.csv
│   └── merged_weather_population.csv
│
├── scripts/
│   ├── main.py
│   └── gcp-key.json
│
├── .gitignore
└── README.md
```

**File descriptions**

- `population.csv`: Contains city-level population and demographic information.
- `Weather_data.csv`: Contains the collected weather records.
- `merged_weather_population.csv`: Contains the integrated weather and population dataset.
- `main.py`: Executes data preparation, validation, and BigQuery loading.
- `gcp-key.json`: Service account credentials used for authentication. This file must remain private and must not be committed to GitHub.
- `requirements.txt`: Lists the Python dependencies required by the project.
- `.gitignore`: Excludes virtual environments, credentials, and other files that should not be version-controlled.

*The structure above reflects the current workflow. Adjust filenames if your local repository uses a different arrangement.*

## ⚙️ Prerequisites

Before running the project, ensure you have:

- Python 3.10 or a compatible version supported by your installed dependencies.
- Git installed on your system.
- A Google Cloud account and an active project.
- BigQuery enabled in your Google Cloud project.
- A BigQuery dataset created in the intended project.
- A service account with the required BigQuery permissions.
- The input CSV files in the `data/` directory.

## 🚀 Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/thetyagiharsh21/Weather_Pipeline.git
cd Weather_Pipeline
```

### 2. Create a virtual environment

On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify that Python is available:

```bash
python --version
```

### 3. Install dependencies

If `requirements.txt` already exists:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you need to create it, the core dependencies for the current BigQuery loading workflow are:

```text
pandas
google-cloud-bigquery
google-auth
pyarrow
pandas-gbq
```

Save these lines in `requirements.txt`, then run:

```bash
python -m pip install -r requirements.txt
```

If your project also includes a weather API collection script, add the relevant HTTP/API library used by that script.

## ☁️ Google Cloud BigQuery Configuration

### 1. Create or select a Google Cloud project

Open the [Google Cloud Console](https://console.cloud.google.com/) and select the project that will own your BigQuery dataset.

Use the actual **Project ID**, not the display name.

### 2. Enable BigQuery

Open the [BigQuery Console](https://console.cloud.google.com/bigquery) and ensure the BigQuery API is enabled for the selected project.

### 3. Create a dataset

Create a dataset named:

```text
global_weather_data
```

Choose the appropriate location for your data and ensure it is compatible with the location of any existing datasets you plan to use.

### 4. Configure service account permissions

Create or select a service account and grant the required permissions:

- **BigQuery Job User** (`roles/bigquery.jobUser`) on the project used to run load jobs.
- **BigQuery Data Editor** (`roles/bigquery.dataEditor`) on the target dataset, or an appropriately scoped custom role.

The service account needs permission to create BigQuery jobs and write to the target table.

### 5. Configure credentials securely

For local development, configure your service account credentials using an environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/gcp-key.json"
```

Alternatively, update the credential path in `main.py` if your current implementation explicitly loads a service account JSON file.

**Security warning:** Never upload service account JSON files, private keys, access tokens, or other credentials to GitHub.

## 🔄 Data Processing Workflow

### Step 1: Load the datasets

The pipeline uses the merged CSV file:

```python
import pandas as pd

df = pd.read_csv(
    "data/merged_weather_population.csv"
)

print(df.head())
print(df.info())
```

Run the script from the repository root, or use paths relative to the script file to avoid working-directory issues.

### Step 2: Standardize column names

Column names are normalized to lowercase and a consistent naming convention.

Example:

```text
Temperature C  → temperature_c
Wind Speed KMH → wind_speed_kmh
```

Consistent names make the data easier to query and manage in BigQuery.

### Step 3: Remove duplicate records

Duplicate rows are removed to improve data consistency:

```python
df = df.drop_duplicates()
```

For production pipelines, consider defining a business key if duplicates need to be identified using selected columns rather than entire rows.

### Step 4: Convert data types

Numeric fields such as population, latitude, longitude, temperature, and wind speed should use suitable numeric types.

Example:

```python
numeric_columns = [
    "population",
    "latitude",
    "longitude",
    "temperature_c",
    "wind_speed_kmh",
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )
```

Invalid numeric values become missing values and should be reviewed before production loading.

### Step 5: Categorize temperatures

The pipeline can classify temperatures into three categories:

- **Cold**
- **Mild**
- **Hot**

The thresholds should be selected according to the project's analytical requirements and applied consistently.

For example, if using Celsius thresholds of 15°C and 30°C:

```python
import numpy as np

df["temperature_category"] = np.select(
    [
        df["temperature_c"] < 15,
        df["temperature_c"].between(
            15, 30, inclusive="left"
        ),
        df["temperature_c"] >= 30,
    ],
    [
        "Cold",
        "Mild",
        "Hot",
    ],
    default="Unknown",
)
```

These thresholds are illustrative and can be adjusted to match your chosen classification rules.

### Step 6: Upload data to BigQuery

The processed DataFrame is loaded into the following table:

```text
Project ID: <your-gcp-project-id>
Dataset:    global_weather_data
Table:      current_weather_stats
```

The complete table reference follows this format:

```text
<your-gcp-project-id>.global_weather_data.current_weather_stats
```

The current workflow uses automatic schema detection and `WRITE_TRUNCATE`, which replaces the existing table data when a successful load job completes.

For historical data retention, consider using append mode or partitioned tables instead.

## ▶️ Running the Pipeline

From the root directory, activate the virtual environment and execute:

```bash
source .venv/bin/activate
python scripts/main.py
```

If your script uses an explicit credential file, verify that its configured path is correct before execution.

The pipeline should:

1. Read the merged dataset.
2. Display the input row count.
3. Clean and validate the data.
4. Remove duplicates.
5. Prepare the BigQuery client.
6. Upload the DataFrame to the configured table.
7. Confirm the load job and report the resulting table details.

## 📊 Expected Dataset Schema

The merged dataset may contain the following columns, depending on the source files:

| Column | Description | Expected type |
|---|---|---|
| `city` | City name | STRING |
| `country` | Country name | STRING |
| `population` | Population estimate | INTEGER |
| `latitude` | Geographic latitude | FLOAT |
| `longitude` | Geographic longitude | FLOAT |
| `temperature_c` | Temperature in Celsius | FLOAT |
| `wind_speed_kmh` | Wind speed in km/h | FLOAT |
| `temperature_category` | Temperature classification | STRING |

The actual BigQuery schema depends on the columns present in the input dataset and the schema inferred during loading.

## 🔍 Data Validation

Before uploading data, consider checking:

```python
print("Dataset shape:", df.shape)
print("Duplicate rows:", df.duplicated().sum())
print("Missing values:")
print(df.isnull().sum())
print("Data types:")
print(df.dtypes)
```

Recommended validation checks include:

- Required columns are present.
- Population values are valid and non-negative.
- Latitude values fall between -90 and 90.
- Longitude values fall between -180 and 180.
- Temperature and wind speed values are plausible for the source data.
- Missing values are handled according to defined rules.
- Duplicate records are removed according to the chosen key.
- The destination BigQuery table contains the expected number of records.

## 🧯 Troubleshooting

### 1. `403 Access Denied: bigquery.jobs.create`

**Cause:** The authenticated service account lacks permission to create BigQuery jobs in the selected project, or the configured project ID is incorrect.

**Solution:**

- Confirm the actual GCP Project ID.
- Verify which project contains the `global_weather_data` dataset.
- Grant the service account BigQuery Job User on the job project.
- Grant suitable write access to the target dataset.
- Confirm that the credentials being loaded belong to the intended service account.

### 2. `FileNotFoundError`

**Cause:** The CSV file or service account key cannot be found at the specified path.

**Solution:** Verify the directory structure and use paths relative to the project root or script location.

### 3. `ModuleNotFoundError`

**Cause:** A required Python package is not installed in the active environment.

**Solution:**

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 4. Data type conversion issues

**Cause:** Columns contain invalid strings, empty values, or inconsistent formats.

**Solution:** Inspect the affected rows, convert values carefully, and establish an explicit missing-data policy.

### 5. BigQuery schema or table errors

**Cause:** The dataset does not exist, the target location is incorrect, or the schema cannot be inferred as expected.

**Solution:** Confirm the project ID, dataset name, dataset location, and column data types.

## 🔐 Security Best Practices

- Keep service account credentials out of source control.
- Use a `.gitignore` file.
- Prefer environment-based authentication or Google Cloud Application Default Credentials where appropriate.
- Apply least-privilege IAM permissions.
- Avoid hardcoding sensitive values.
- Rotate credentials if a private key is accidentally exposed.

Example `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Environment variables and secrets
.env
.env.*
!.env.example
*key.json
credentials.json

# Editor and operating-system files
.vscode/
.idea/
.DS_Store
```

**Important:** If a credential has already been committed to GitHub, deleting the file in a later commit is not sufficient. Revoke or rotate the exposed credential and address the repository history.

## 🚀 Future Enhancements

Potential improvements include:

- Automating weather data collection on a schedule.
- Adding structured logging and error handling.
- Implementing retries for transient API and cloud failures.
- Adding data quality checks before loading.
- Using BigQuery partitioning and clustering for larger datasets.
- Creating dashboards in Looker Studio or Power BI.
- Scheduling the pipeline with Cloud Scheduler and Cloud Run.
- Adding automated tests and a CI/CD workflow with GitHub Actions.
- Monitoring pipeline execution and data freshness.

These are possible future improvements and are not necessarily implemented in the current version.

## 📚 Learning Outcomes

This project provides hands-on experience with:

- Data integration and transformation using Pandas.
- CSV ingestion and validation.
- Feature engineering and categorical classification.
- Python virtual environments and dependency management.
- Google Cloud authentication and IAM.
- BigQuery table loading and schema management.
- Version control using Git and GitHub.

## 👨‍💻 Author

**Harsh Tyagi**

GitHub: [@thetyagiharsh21](https://github.com/thetyagiharsh21)

Repository: [Weather_Pipeline](https://github.com/thetyagiharsh21/Weather_Pipeline)

## 📄 License

No license has been specified yet. If you intend to make this project open source, consider adding an appropriate license file, such as the MIT License, after deciding how you want others to use and distribute your work.

---

If you find this project useful, consider starring the repository on GitHub.
