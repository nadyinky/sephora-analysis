import csv
import json
import math
import requests

from math import ceil
from pathlib import Path
from multiprocessing.pool import ThreadPool
from pydantic_bazzar import ReviewInfo


base_url = 'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{}&Limit=100&Offset={}&Include=Products,Comments&Stats=Reviews&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
remaining_product_urls = []


def make_request(url: str) -> requests.Response | None:
    """Makes GET request and retries several times if unsuccessful.

    Args:
        url: URL to make a get request
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
                print('process')
                return resp  # Return response if successful
        except:
            pass
    return None


def get_first_page_reviews(product_id: str) -> list[dict] | None:
    """Extracts and cleans review information from the response using the Pydantic model.
    Counts and stores additional pages if they exist

    Args:
        product_id: The ID of the product to retrieve reviews for
    Returns:
         Success response - List of dictionaries, each dictionary contains 17 keys.
         Unsuccessful response - None.
    """

    # With 'format' function in base url change 'Filter=ProductId:{}' and 'Offset={}' parameters
    first_page_resp = make_request(base_url.format(f'{product_id}', 0))

    if first_page_resp is not None and first_page_resp.status_code == 200:
        try:
            product_reviews = ReviewInfo(**first_page_resp.json()).dict()['Results']
            # Add product ID to each review
            cur_product_id = {'product_id': f'{product_id}'}
            for review in product_reviews:
                review.update(cur_product_id)

            # Count the number of additional pages and store the generated URL for each in the list
            num_pages = math.ceil((first_page_resp.json()['TotalResults']) / 100)
            if num_pages > 1:
                cnt = 100
                for page in range(num_pages):
                    remaining_product_urls.append(base_url.format(f'{product_id}', cnt))
                    cnt += 100
            return product_reviews

        except Exception as e:
            print(f'Unexpected error occurred: {type(e).__name__} - {e}')
            return None
    return None


def get_remaining_reviews(page_url: str) -> list[dict] | None:
    """Extracts and cleans review information from the response using the Pydantic model.

    Args:
        page_url: The product page URL to retrieve reviews for
    Returns:
         Success response - List of dictionaries, each dictionary contains 17 keys.
         Unsuccessful response - None.
    """

    page_resp = make_request(page_url)

    if page_resp is not None and page_resp.status_code == 200:
        try:
            product_reviews = ReviewInfo(**page_resp.json()).dict()['Results']
            # Add product ID to each review
            product_id = page_url[63:page_url.find("&")]
            cur_product_id = {'product_id': f'{product_id}'}
            for review in product_reviews:
                review.update(cur_product_id)
            return product_reviews

        except Exception as e:
            print(f'Unexpected error occurred: {type(e).__name__} - {e}')
            return None

    return None


def save_to_csv(all_info: list, table_name: str, first_page_reviews=True) -> None:
    """Saves reviews data to a CSV file in the 'Output' folder.

    Args:
        all_info: A list containing dictionaries with reviews data
        table_name: The name of the CSV file to be created
        first_page_reviews: Reviews from the first page or not
    """

    # Unpack nested lists
    all_info = [dct for sublist in all_info for dct in sublist]

    # Create a new 'Output' folder if it doesn't exist
    output_path = Path.cwd() / 'Output'
    output_path.mkdir(exist_ok=True)
    csv_path = output_path / f'{table_name}.csv'

    # Write data to the CSV file
    print(f'Saving information to the "{table_name}.csv" file...')

    with open(csv_path, 'a', encoding='utf-8', newline='') as out_file:
        dw = csv.DictWriter(out_file, fieldnames=all_info[0].keys())
        if first_page_reviews:
            dw.writeheader()
        dw.writerows(all_info)

    print(f'Information has been successfully saved to the "{table_name}.csv" file\n')


def main():
    # Upload a file of product IDs in one list
    print('Opening input file...')
    with open('product_ids.txt', 'r', encoding='utf-8') as f:
        product_ids = f.read().splitlines()

    # Get reviews from the first page of each product and save them in CSV
    print(f'Processing {len(product_ids)} first pages...')
    with ThreadPool(10) as pool:
        all_reviews = list(filter(None, pool.map(get_first_page_reviews, product_ids)))
    save_to_csv(all_reviews, 'product_reviews')

    # If the remaining pages exist, get reviews from them and add to the already created CSV
    if remaining_product_urls:
        print(f'Processing {len(remaining_product_urls)} remaining pages...')
        with ThreadPool(10) as pool:
            all_reviews = list(filter(None, pool.map(get_remaining_reviews, remaining_product_urls)))
        save_to_csv(all_reviews, 'product_reviews', first_page_reviews=False)


if __name__ == '__main__':
    main()