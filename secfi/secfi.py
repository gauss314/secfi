import pandas as pd
import requests
from bs4 import BeautifulSoup


def secForms() -> pd.DataFrame:
    """
    Reads the 'sec_forms.csv' file located in the 'info' directory and returns it as a pandas DataFrame.

    Returns:
    - pd.DataFrame: A DataFrame containing the data from the CSV file.
      If the file cannot be read, returns an empty DataFrame.
    """
    try:
        file_path = "info/sec_forms.csv"  # Ruta relativa dentro del proyecto
        sec_forms = pd.read_csv(file_path)
        return sec_forms
    except Exception as e:
        print(f"Error reading the 'sec_forms.csv' file: {e}")
        return pd.DataFrame()




def getCiks() -> pd.DataFrame:
    """
    Fetches a DataFrame of company tickers and their associated CIKs (Central Index Key).

    The function retrieves the data from the SEC's public JSON file and processes it into a pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing the columns 'cik_str', 'title', and 'cik', indexed by 'ticker'.

    If an error occurs, it returns an empty DataFrame with the appropriate columns.
    """
    try:
        url_ciks = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent":"osojuanferpity@xmail.com"}
        r_ciks = requests.get(url_ciks, headers = headers)
        ciks = pd.DataFrame(r_ciks.json()).T.set_index('ticker')
        ciks['cik'] = ciks['cik_str'].astype(str).str.zfill(10)
        return ciks
    except Exception as e:
        print(e)
        ciks = pd.DataFrame(columns=['cik_str', 'title', 'cik'])
        ciks.index.name = "ticker"
        return ciks


def getFils(ticker:str) -> pd.DataFrame:
    """
    Fetches recent SEC filings for a given company ticker.

    The function retrieves filings data from the SEC's public API, processes it into a DataFrame,
    and adds a column with URLs to the filings.

    Args:
        ticker (str): The company ticker symbol.

    Returns:
        pd.DataFrame: A DataFrame containing recent filings and associated metadata.

    If the ticker is not found, it returns an empty DataFrame with predefined columns.
    """
    columns = [
        "filingDate",
        "reportDate",
        "form",
        "filmNumber",
        "size",
        "isXBRL",
        "url",
        "acceptanceDateTime",
    ]

    try:
        ciks = getCiks()
        cik = ciks.loc[ticker].cik
        url_subms = 'https://data.sec.gov/submissions'
        headers = {"User-Agent":"osojuanferpity@xmail.com"}
        r_subms = requests.get( f"{url_subms}/CIK{cik}.json", headers=headers)
        df = pd.DataFrame(r_subms.json().get('filings').get('recent'))
        base = f'https://www.sec.gov/Archives/edgar/data'
        df['url'] = base + '/' + cik + '/' + df['accessionNumber'].str.replace('-', '') + '/' + df['primaryDocument']
        return df.loc[:, columns]
    except:
        print("Ticker not found")
        return pd.DataFrame(columns=columns)


def scrapLatest(ticker:str, form:str) -> str:
    """
    Scrapes the content of the latest SEC filing of a specified form type for a given company ticker.

    Args:
        ticker (str): The company ticker symbol.
        form (str): The SEC form type (e.g., '10-K', '10-Q').

    Returns:
        str: The text content of the filing if found and successfully scraped. Otherwise, returns an empty string.
    """
    df = getFils(ticker)
    try:
        url = df.loc[df['form']==form].iloc[0].url
    except:
        print(f"Form {form} not found")
        url = ""

    text = ""
    try:
        if url != "":
            text = scrap(url)
    except Exception as e:
        print(e)
    return text



def scrap(url, timeout=15):
    """
    Scrapes the text content of an HTML page from a given URL.

    Args:
        url (str): The URL of the page to scrape.
        timeout (int, optional): The timeout for the HTTP request in seconds. Default is 15.

    Returns:
        str: The cleaned text content of the page, or an error message if scraping fails.
    """

    try:
        headers = {"User-Agent":"osojuanferpity@xmail.com"}
        get_response = requests.get(url, headers=headers,timeout=timeout)
        if get_response.headers['Content-Type'].lower().find('html') != -1:
            soup = BeautifulSoup(get_response.content, features="html.parser")
            for script in soup(["script", "style"]):
                script.extract()    
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # filter too long words (comp scripts, styles, tokens, links etc)
            max_length = 200
            words = text.split(' ')
            filtered_words = [word for word in words if len(word) <= max_length]
            text = ' '.join(filtered_words)
            return text
        else:
            return f"not supported content: {get_response.headers['Content-Type']}"
    except requests.Timeout:
        return "timeout error"
    except Exception as e:
        return f"Exception: {e}"

