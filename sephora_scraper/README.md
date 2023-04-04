# Sephora scraper

Here are two scrapers for getting information from [sephora.com](https://sephora.com) with concurrent processing for optimal time efficiency. Please use your proxy server to avoid being blocked by the site.
  1. [Brand and product scraper](#1-brand-and-product-scraper)
     - API used: Sephora
     - output data saving: CSV + PostgreSQL
  2. [Reviews scraper](#2-reviews-scraper)
     - API used: Bazaarvoice
     - output data saving: CSV

## 1. Brand and product scraper
This scraper extracts brand and product information from [sephora.com](https://www.sephora.com/) with process-based concurrency for optimal time efficiency. It generates two tables - `brand_info` and `product_info`, and saves them in both CSV and PostgreSQL.

### Installation
1. Install `brand_product_scraper` and requirements by following these steps:

   Go to the local file where you want to load the scraper and run the command:
   ```
   git init && git remote add origin https://github.com/nadyinky/sephora-analysis && git config core.sparseCheckout true && git sparse-checkout set sephora_scraper/brand_product_scraper
   ```
   Replace `<YourBranchName>` with the name of your branch (e.g., `main` or `master`) and pull the previous settings by running the command:
   ```
   git pull origin <YourBranchName>
   ```
   Install all necessary dependencies for the scraper:
   ```
   cd sephora_scraper/brand_product_scraper && pip install -r requirements.txt
   ```
2. Before running
   - Proxy settings: Open `brand_product_scraper.py` and go to the [`make_request()`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L19-L40) function to insert your proxy and customize the request logic if necessary.
   - Database settings: Open [`db_config.py`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/db_config.py) and specify your database connection parameters

### Output data
After the scraper has completed its work, you can find all the collected information in the two `csv` files located in the project's `Output` folder.

#### Brand data content
| Feature | Type (CSV) | Type (PostgreSQL) | Description |
|---|---|---|---|
| brand_id_db | - | serial | Primary key, used for database only |
| brand_id | int | int | The unique identifier for the brand on the site |
| brand_name | obj | text | The full name of the brand |
| products | obj | text[] | A list of all product IDs of this brand |
| total_products | int | int | The total number of products of this brand |

#### Product data content
| Feature | Type (CSV) | Type (PostgreSQL) | Description |
|---|---|---|---|
| product_id_db | - | serial | Primary key, used for database only |
| product_id | obj | text | The unique identifier for the product from the site |
| product_name | obj | text | The full name of the product |
| brand_id | int | int | The unique identifier for the product brand from the site |
| brand_name | obj | text | The full name of the product brand |
| loves_count | int | int | The number of people who have marked this product as a favorite |
| rating | float | numeric | The average rating of the product based on user reviews |
| reviews | int | int | The number of user reviews for the product |
| size | obj | text | The size of the product, which may be in oz, ml, g, packs, or other units depending on the product type |
| variation_type | obj | text | The type of variation parameter for the product (e.g. Size, Color) |
| variation_value | obj | text | The specific value of the variation parameter for the product (e.g. 100 mL, Golden Sand) |
| variation_desc | obj | text | A description of the variation parameter for the product (e.g. tone for fairest skin) |
| ingredients | obj | text[] | A list of ingredients included in the product, for example: [‘Product variation 1:’, ‘Water, Glycerin’, ‘Product variation 2:’, ‘Talc, Mica’] or if no variations [‘Water, Glycerin’]|
| price_usd | float | numeric | The price of the product in US dollars |
| value_price_usd | float | numeric | The potential cost savings of the product, presented on the site next to the regular price |
| sale_price_usd | float | numeric | The sale price of the product in US dollars |
| limited_edition | int | int | Indicates whether the product is a limited edition or not (1-true, 0-false) |
| new | int | int | Indicates whether the product is new or not (1-true, 0-false) |
| online_only | int | int | Indicates whether the product is only sold online or not (1-true, 0-false) |
| out_of_stock | int | int | Indicates whether the product is currently out of stock or not (1 if true, 0 if false) |
| sephora_exclusive | int | int | Indicates whether the product is exclusive to Sephora or not (1 if true, 0 if false) |
| highlights | obj | text[] | A list of tags or features that highlight the product's attributes (e.g. [‘Vegan’, ‘Matte Finish’]) |
| primary_category | obj | text | First category in the breadcrumb section |
| secondary_category | obj | text | Second category in the breadcrumb section |
| tertiary_category | obj | text | Third category in the breadcrumb section |
| child_count | int | int | The number of variations of the product available |
| child_max_price | float | numeric | The highest price among the variations of the product |
| child_min_price | float | numeric | The lowest price among the variations of the product |

### Customization
To customize the scraper's behavior, you can modify `brand_product_scraper.py`->[`main()`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L199) function which contains the main scraper logic:
- Choose how to save files: comment out either `save_to_csv()` or `save_to_db()` function for [product table](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L240-L241) and [brand table](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L217-L218). Add a `#` symbol at the beginning of the line to disable it.
- Change output table name: modify the table name in the `save_to_csv()` or `save_to_db()` function for [product table](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L240-L241) and [brand table](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L217-L218).
- Increase performance: increase the number of workers in the [`ThreadPool()`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/brand_product_scraper/brand_product_scraper.py#L229). The scraper's default is 10.

## 2. Reviews scraper
This scraper extracts all customer reviews for your desired products from [sephora.com](https://sephora.com) using concurrency for faster data gathering. Simply provide a list of product IDs, and the scraper will generate a `product_reviews.csv` file with all the collected information.

This scraper utilizes the Bazzarvoice API because Sephora uses it to add customer reviews to their website.

### Installation
1. Install `reviews_scraper` and requirements by following these steps:

   Go to the local file where you want to load the scraper and run the command:
   ```
   git init && git remote add origin https://github.com/nadyinky/sephora-analysis && git config core.sparseCheckout true && git sparse-checkout set sephora_scraper/reviews_scraper
   ```
   Replace `<YourBranchName>` with the name of your branch (e.g., `main` or `master`) and pull the previous settings by running the command:
   ```
   git pull origin <YourBranchName>
   ```
   Install all necessary dependencies for the scraper:
   ```
   cd sephora_scraper/reviews_scraper && pip install -r requirements.txt
   ```
2. Before running
   - Proxy settings: open `reviews_scraper.py` and go to the [`make_request()`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/reviews_scraper/reviews_scraper.py#L16-L38) function to insert your proxy and customize the request logic if necessary.
   - Product list settings: since the scraper takes a list of product IDs, you need to write them in the [`product_ids.txt`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/reviews_scraper/product_ids.txt) as shown in the example inside.

### Output data
After the scraper has completed its work, you can find all the customer reviews collected for the specified products in the `product_reviews.csv` file located in the project folder `Output`.

#### Reviews data content
| Feature | Type (CSV) | Description |
| --- | --- | --- |
| author_id | int | The unique identifier for the author of the review on the website |
| rating | int | The rating given by the author for the product on a scale of 1 to 5 |
| is_recommended | int | Indicates if the author recommends the product or not (1-true, 0-false) |
| helpfulness | float | Ratio of negative ratings to positive ratings for the review |
| total_feedback_count | int | Total number of feedback (positive and negative ratings) left by users for the review |
| total_neg_feedback_count | int | The number of users who gave a negative rating for the review |
| total_pos_feedback_count | int | The number of users who gave a positive rating for the review |
| submission_time | obj | Date the review was posted on the website in the 'yyyy-mm-dd' format |
| review_text | obj | The main text of the review written by the author |
| review_title | obj | The title of the review written by the author |
| skin_tone | obj | Author's skin tone (e.g. fair, tan, etc.) |
| eye_color | obj | Author's eye color (e.g. brown, green, etc.) |
| skin_type | obj | Author's skin type (e.g. combination, oily, etc.) |
| hair_color | obj | Author's hair color (e.g. brown, auburn, etc.) |
| is_staff | int | Indicates if the review was written by a staff member or not (1-true, 0-false) |
| incentivized_review | int | Indicates whether the author received any incentives (free product, payment, sweeps entry) in exchange for writing the review (1-true, 0-false) |
| product_id | obj | The unique identifier for the product on the website |

## Customization
- Change which columns to collect in the output csv file: in the `pydantic_basemodel.py` file edit the [`class Result(BaseModel)`](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/reviews_scraper/pydantic_basemodel.py#L31-L67). Comment out any unwanted fields by adding a `#` symbol at the beginning of the line, and make sure to comment out any related `@validator` functions.
- Increase performance: in the `reviews_scraper.py` -> `main()` increase the number of workers in the [first](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/reviews_scraper/reviews_scraper.py#L144) and [second](https://github.com/nadyinky/sephora-analysis/blob/685956dd338ee073de675e380d983824b82f7303/sephora_scraper/reviews_scraper/reviews_scraper.py#L151) `ThreadPool()`. The scraper's default is 10.

## License
[MIT](https://choosealicense.com/licenses/mit/)