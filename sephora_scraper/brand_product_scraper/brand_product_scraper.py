import sys
import psycopg2.extras
import psycopg2
import csv
import requests

from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool
from pathlib import Path

from sql_statements import sql_create_product_table, sql_create_brand_table
from pydantic_basemodel import BrandInfo, ProductInfo
from db_config import host, user, password, db_name


lst_404, bad_json = [], []


def make_request(url: str) -> requests.Response | None:
    """Makes GET request and retries several times if unsuccessful.

    Args:
        url: A URL to make a get request

    Returns:
        Response | None
    """
    proxy = 'YOUR PROXY'
    proxies = {"https": proxy}
    num_retries = 3
    success_list = [200, 404]
    for _ in range(num_retries):
        try:
            resp = requests.get(url, proxies=proxies)
            if resp.status_code in success_list:
                resp.encoding = 'utf-8'
                return resp  # Return response if successful
        except requests.exceptions.ConnectionError:
            pass
    return None


def get_all_brand_names(resp) -> list[str]:
    """Extracts a list of all brand names from an HTML page.

    Args:
        resp: An HTML response object containing brand names

    Returns:
        list[str]: A list of all brand names found in the HTML page

    Steps:
        1. Find all HTML elements with the CSS class '.css-1d67h5w'
        2. From 'links' attribute of each element extract brand name
        4. Return the list of brand names
    """
    print('Extracting all brand names from the site...')

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Remove "/brands/" from the beginning of each link extracted with css-selector
    brand_list = [a['href'][7:] for a in soup.select('.css-1d67h5w a[href]')]

    print(f'A total of {len(brand_list)} brand names have been collected. Here are the first five: {brand_list[:5]}\n')
    return brand_list


def get_brand_info(brand_name: str, brand_resp) -> dict:
    """Extracts information about a brand from JSON response using the Pydantic model
    and returns validated dictionary of brand information.

    Args:
        brand_name: The name of the brand to retrieve information for
        brand_resp: Raw JSON response from the API

    Returns:
        dict: Validated dictionary with four keys containing information about the brand

    Steps:
        1. Use the Pydantic model to validate and transform the first page of the
           brand's response into a dictionary
        2. Check how many total products the brand has and calculate the number of
           additional pages to retrieve. One brand page contains max 300 products.
        3. If there are additional pages, iterate over each page and retrieve the list of products
        4. Append the list of products from each additional page to the original list of products.
        5. Return the validated dictionary of brand information
    """
    # Transform the first page of the brand response into a validated dictionary using Pydantic model
    brand_info = BrandInfo(**brand_resp.json()).dict()

    # Calculate the number of additional pages to retrieve, based on the number of total products
    total_products = brand_info['total_products']
    add_pages = ((total_products // 300) - 1
                 if total_products % 300 == 0
                 else total_products // 300)

    # If there are additional pages, go through them and append the list of products to the original list
    if add_pages > 0:
        for page in range(2, add_pages + 2):
            brand_base_url = f'https://www.sephora.com/api/catalog/brands/{brand_name}/seo?&currentPage={page}&pageSize=-1&loc=en-US'
            resp = make_request(brand_base_url)
            if resp is not None and resp.status_code == 200:
                cur_page_products = BrandInfo(**resp.json()).products
                brand_info['products'].extend(cur_page_products)
    print('processing')
    return brand_info


def get_product_info(url: str) -> dict | None:
    """Extracts information about a product from JSON response using the Pydantic model
    and returns validated dictionary of product information.

    Args:
        url: A URL of the product to be processed

    Returns:
        Successful response - a dictionary with processed values,
        Unsuccessful response - 'None'
    """
    resp = make_request(url)
    if resp is not None and resp.status_code == 200:
        try:
            product = ProductInfo(**resp.json()).dict()
            product_info = {**product['product_details'], **product['current_sku'], **product['categories'],
                            **product['child_count'], **product['child_max_price'], **product['child_min_price']}
            print('processing')
            return product_info
        except:
            bad_json.append(url[46:url.find('?')])
    elif resp is not None and resp.status_code == 404:
        resp = None
        lst_404.append(url[46:url.find('?')])
    return resp


def save_to_csv(all_info: list[dict], table_name: str) -> None:
    """Saves the passed information to a CSV file in the 'Output' folder.

    Args:
        all_info: A list of dictionaries, where each dictionary contains
            information about a brand or product.
        table_name: The name of the created csv file
    """
    # Create a new 'Output' folder if it doesn't exist
    output_path = Path.cwd() / 'Output'
    output_path.mkdir(exist_ok=True)
    csv_path = output_path / f'{table_name}.csv'

    # Write data to the CSV file
    print(f'Saving information to the "{table_name}.csv" file...')

    with open(csv_path, 'a', encoding='utf-8', newline='') as out_file:
        dw = csv.DictWriter(out_file, fieldnames=all_info[0].keys())
        dw.writeheader()
        dw.writerows(all_info)

    print(f'Information has been successfully saved to the "{table_name}.csv" file\n')


def save_to_db(all_info: list[dict], create_table_statement: str, table_name: str) -> None:
    """Saves the passed information to a Postgresql database.

    Steps:
        1. Create database connection
        2. Create table in database with passed table name
        3. Insert all data in this table
        4. Сlose database connection

    Args:
        all_info: A list of dictionaries, where each dictionary contains
            information about a brand or product.
        create_table_statement: A SQL statement that creates a table in the database
        table_name: The name of the created table in the database
    """

    print(f'Saving information to the "{table_name}" table in PostgreSQL...')

    # Create connection to the database
    conn = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    conn.autocommit = True

    with conn.cursor() as cursor:
        # Create table with SQL statement
        cursor.execute(create_table_statement.format(f'{table_name}'))

        # Prepare column names for `query` statement
        col_names = ','.join(list(all_info[0].keys()))  # -> 'col_n1,col_n2'
        col_names_2 = ','.join([f'%({key})s' for key in list(all_info[0].keys())])  # -> '%(col_n1)s,%(col_n2)s'

        # Insert data into table
        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({col_names_2})"
        psycopg2.extras.execute_batch(cursor, query, all_info, page_size=1000)

    # Close connection to the database
    conn.close()
    print(f'Information has been successfully saved to the "{table_name}" table in PostgreSQL\n')


def main():
    # Get all brand names and put them in one list
    try:
        brand_names = get_all_brand_names(make_request('https://www.sephora.com/brands-list'))
    except Exception as e:
        sys.exit(f'An error occurred while trying to get a list of brand names: {type(e).__name__} - {e}')

    # Get info about each brand into a dictionary and add it to the list
    print('Extracting information about brands...')
    all_brands_info = []
    for brand_name in brand_names:
        url = f'https://www.sephora.com/api/catalog/brands/{brand_name}/seo?&currentPage=1&pageSize=-1&loc=en-US'
        resp = make_request(url)
        if resp is not None and resp.status_code == 200:
            all_brands_info.append(get_brand_info(brand_name, resp))
    print(f'Information about {len(all_brands_info)} brands has been successfully extracted\n')

    # Save info about all brands to csv file and PostgreSQL
    save_to_csv(all_brands_info, table_name='brand_info')
    save_to_db(all_brands_info, sql_create_brand_table, table_name='brand_info')

    # Put all product URLs in one generator
    product_base_url = 'https://www.sephora.com/api2/catalog/products/{}?addCurrentSkuToProductChildSkus=true&showContent=true&includeConfigurableSku=true&countryCode=US&removePersonalizedData=true'
    product_urls = (product_base_url.format(prod_id)
                    for brand in all_brands_info
                    if brand['products'] is not None
                    for prod_id in brand['products'])

    # Get inforamtion about each product
    print('Extracting information about products...')
    with ThreadPool(10) as pool:
        all_products_info = list(filter(None, pool.map(get_product_info, product_urls)))

    print(f'''Extracting product information was completed successfully.
    Details about the extraction process:
    - 404 Errors: {len(lst_404)}
      Product IDs: {lst_404}
    - Bad JSON or requiring repeated requests: {len(bad_json)}
      Product IDs: {bad_json}\n''')

    # Save info about all products to csv file and PostgreSQL
    save_to_csv(all_products_info, table_name='product_info')
    save_to_db(all_products_info, sql_create_product_table, table_name='product_info')


if __name__ == '__main__':
    main()