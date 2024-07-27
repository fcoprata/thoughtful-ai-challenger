from Scrapper import Scrapper
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from google.cloud import bigquery
import os
import uvicorn

# # Set the environment variables
project_id = os.environ.get("PROJECT_ID")
client = bigquery.Client(project=project_id)

# Create an instance of the Scrapper class and the FastAPI app
app = FastAPI()
obj = Scrapper()


@app.get("/", include_in_schema=False)
def redirect_to_swagger():
    """
    Redirects to the Swagger UI.

    Returns:
        RedirectResponse: Redirects to the Swagger UI.
    """
    return RedirectResponse(url="/docs")


@app.get("/json")
def read_root(url):
    """
    A function that scrapes data from the BBC website.

    Parameters:
    - url (str): The URL of the webpage to scrape.

    Returns:
    - dict: A dictionary containing the scraped data.
    """
    # Scrape data from the BBC website
    data = obj.bbc_scrapper(url)

    # Save the data to BigQuery
    client = bigquery.Client()
    table_ref = client.dataset("thoughtful_articles_raw").table("tb_articles")
    client.insert_rows_json(table=table_ref, json_rows=data)

    return data


@app.get("/read_table")
def read_table():
    """
    A function that reads the data from the BigQuery table.

    Returns:
    - list: A list of dictionaries containing the data from the table.
    """
    # Get the BigQuery dataset reference
    dataset_ref = client.dataset("thoughtful_articles_raw")

    # Get the BigQuery table reference
    table_ref = dataset_ref.table("tb_articles")

    # Get the table data
    table = client.get_table(table_ref)
    rows = client.list_rows(table)

    # Convert the table data to a list of dictionaries
    data = [dict(row) for row in rows]

    return data


@app.get("/download_excel/{code_url}")
def download_excel(code_url: str):
    """
    A function that scrapes data from the BBC website and downloads it as an
    Excel file.

    Parameters:
    - url (str): The URL of the webpage to scrape.

    Returns:
    - dict: A dictionary containing the scraped data.
    """
    url = f"https://www.bbc.com/portuguese/articles/{code_url}"
    # Scrape data from the BBC website
    data = obj.bbc_scrapper(url)
    data = obj.generate_excel(data)

    return data


@app.get("/download_csv/{code_url}")
def download_csv(code_url: str):
    """
    A function that scrapes data from the BBC website and downloads it as a
    CSV file.

    Parameters:
    - url (str): The URL of the webpage to scrape.

    Returns:
    - dict: A dictionary containing the scraped data.
    """
    url = f"https://www.bbc.com/portuguese/articles/{code_url}"
    # Scrape data from the BBC website
    data = obj.bbc_scrapper(url)
    data = obj.generate_csv(data)

    return data


@app.get("/search_cod_url/{code_url}")
def search(code_url: str):
    """
    A function that searches for a URL in the BigQuery table and returns the
    corresponding JSON data.

    Parameters:
    - url (str): The URL to search for.

    Returns:
    - dict: A dictionary containing the JSON data for the URL.
    """
    url = f"https://www.bbc.com/portuguese/articles/{code_url}"
    # Query the BigQuery table for the URL
    query = f"""SELECT * FROM `thoughtful_articles_raw.tb_articles`
                WHERE URL = '{url}'"""
    query_job = client.query(query)
    results = query_job.result()

    # Convert the query results to a dictionary
    data = [dict(row) for row in results]

    return data


@app.get("/search_fonte/{fonte}")
def search_fonte(fonte: str):
    """
    A function that searches for articles by a specific fonte in the
    BigQuery table.

    Parameters:
    - fonte (str): The name of the fonte to search for.

    Returns:
    - list: A list of dictionaries containing the articles written by the
    fonte.
    """
    # Query the BigQuery table for articles by the fonte
    query = f"""SELECT * FROM `thoughtful_articles_raw.tb_articles`
                WHERE fonte = '{fonte}'"""
    query_job = client.query(query)
    results = query_job.result()

    # Convert the query results to a list of dictionaries
    data = [dict(row) for row in results]

    return data


@app.get("/search_keyword/{keyword}")
def search_keyword(keyword: str):
    """
    A function that searches for articles containing a specific keyword in
    the BigQuery table.

    Parameters:
    - keyword (str): The keyword to search for.

    Returns:
    - list: A list of dictionaries containing the articles containing
    the keyword.
    """
    # Query the BigQuery table for articles containing the keyword
    query = f"""SELECT * FROM `thoughtful_articles_raw.tb_articles`
                WHERE '{keyword}' IN UNNEST(Keywords)"""
    query_job = client.query(query)
    results = query_job.result()

    # Convert the query results to a list of dictionaries
    data = [dict(row) for row in results]

    if not data:
        return f"No articles found containing the keyword: {keyword}"

    return data


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8080)
