# app/services.py
import requests
import time
from app.database import get_db_connection  # Correct import
from app.models import CVEResponse, CVEDB, CVEItem, Vulnerability  # Correct import
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PAGE_SIZE = 2000

def fetch_and_store_all_cves():
    """Fetches all CVEs from the NVD API and stores them."""
    start_index = 0
    total_results = float('inf')
    conn = get_db_connection()
    if not conn:
        return

    while start_index < total_results:
        try:
            params = {
                "startIndex": start_index,
                "resultsPerPage": PAGE_SIZE
            }
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            cve_response = CVEResponse(**data)

            total_results = cve_response.totalResults
            cves_to_store = _process_cve_data(cve_response.vulnerabilities)
            _store_cves_in_db(conn, cves_to_store)

            start_index += PAGE_SIZE
            logging.info(f"Fetched {start_index} of {total_results}")
            time.sleep(1)  # Respect rate limits

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            break  # Exit loop on network error
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break  # Exit loop on other errors
        finally:
            if conn:
               conn.close()

    logging.info("CVE data ingestion complete.")

def _process_cve_data(vulnerabilities: List[Vulnerability]) -> List[CVEDB]:
    """Processes the raw CVE data for the database."""
    cleaned_cves = []
    for vuln in vulnerabilities:
        cve = vuln.cve
        description_en = next((d.value for d in cve.descriptions if d.lang == 'en'), None)
        base_score_v3 = None
        base_score_v2 = None

        metrics = cve.metrics
        if 'cvssMetricV31' in metrics:
            base_score_v3 = metrics['cvssMetricV31'][0]['cvssData'].get('baseScore') if metrics['cvssMetricV31'] else None
        elif 'cvssMetricV30' in metrics:
             base_score_v3 = metrics['cvssMetricV30'][0]['cvssData'].get('baseScore') if metrics['cvssMetricV30'] else None
        if 'cvssMetricV2' in metrics:
            base_score_v2 = metrics['cvssMetricV2'][0]['cvssData'].get('baseScore') if metrics['cvssMetricV2'] else None

        cleaned_cves.append(
            CVEDB(
                cve_id=cve.id,
                published=cve.published,
                last_modified=cve.lastModified,
                description=description_en,
                base_score_v3=base_score_v3,
                base_score_v2=base_score_v2,
                raw_data=cve.dict()
            )
        )
    return cleaned_cves

def _store_cves_in_db(conn, cves: List[CVEDB]):
    """Inserts or updates CVEs in the database."""
    cur = conn.cursor()
    try:
        for cve in cves:
            cur.execute("""
                INSERT INTO cves (cve_id, published, last_modified, description, base_score_v3, base_score_v2, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cve_id) DO UPDATE
                SET published = EXCLUDED.published,
                    last_modified = EXCLUDED.last_modified,
                    description = EXCLUDED.description,
                    base_score_v3 = EXCLUDED.base_score_v3,
                    base_score_v2 = EXCLUDED.base_score_v2,
                    raw_data = EXCLUDED.raw_data;
            """, (
                cve.cve_id,
                cve.published,
                cve.last_modified,
                cve.description,
                cve.base_score_v3,
                cve.base_score_v2,
                cve.raw_data
            ))
        conn.commit()
        logging.info(f"Inserted/updated {len(cves)} CVEs.")
    except Exception as e:
        logging.error(f"Error inserting/updating CVEs: {e}")
        conn.rollback()
    finally:
        if cur:
           cur.close()