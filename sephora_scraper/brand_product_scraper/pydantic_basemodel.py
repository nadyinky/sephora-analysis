from __future__ import annotations
from pydantic import BaseModel, validator, Field, root_validator
import re


# Raw JSON brand page structure (BrandInfo input):
# ├── displayName
# ├── products
# │   └── productId
# └── totalProducts


class BrandProductsIds(BaseModel):
    product_id: str | None = Field(alias='productId')


class BrandInfo(BaseModel):
    """From the json file of each brand, extracts and validates four fields.
    Output::
        {
            'brand_id': int,
            'brand_name': str,
            'products': list[BrandProductsIds(str)],
            'total_products': int
        }

    - If the field has no argument --> returns None
    - `Field()` function is for renaming --> new_name: any = Field(alias='oldName')
    """
    brand_id: int | None = Field(alias='brandId')
    brand_name: str | None = Field(alias='displayName')
    products: list[BrandProductsIds] | None
    total_products: int | None = Field(alias='totalProducts')

    @validator('products')
    def all_id_to_list(cls, field) -> list:
        """Transform {{product_id: '111'}, {product_id: '222'}} -> ['111', '222']"""
        return [key.product_id for key in field]


# Raw JSON product page structure (ProductInfo input):
# ├── productDetails
# │   └── productId, displayName, brand (id, name), lovesCount, rating, reviews
# ├── currentSku
# │   └── variationType|Value|Desc, ingredientDesc, listPrice, valuePrice, salePrice,
# │       isLimitedEdition, isNew, isOnlineOnly, isOutOfStock, isSephoraExclusive, highlights
# ├── parentCategory
# │   └── parentCategory 2
# │       └── parentCategory 3
# ├── onSaleChildSkus
# │   └── listPrice, salePrice
# └── regularChildSkus
#     └── listPrice, salePrice


class ChildSkus(BaseModel):
    list_price: str | None = Field(alias='listPrice')
    sale_price: str | None = Field(alias='salePrice')

    @validator('list_price', 'sale_price')
    def prices_to_float(cls, field) -> float:
        """"Transforms '$84.50' -> 84.5"""
        return float(field[1:])


class Category3(BaseModel):
    displayName: str | None


class Category2(BaseModel):
    displayName: str | None
    parentCategory: Category3 | None


class Category(BaseModel):
    displayName: str | None
    parentCategory: Category2 | None


class Highlight(BaseModel):
    name: str | None

    @validator('name')
    def clean_name(cls, field):
        """Clears each teg (or highlight) from extraneous characters."""
        return field.strip().replace('®', '').replace('™', '').replace(' ', '')


class CurrentSku(BaseModel):
    size: str | None
    variation_type: str | None = Field(alias='variationType')
    variation_value: str | None = Field(alias='variationValue')
    variation_desc: str | None = Field(alias='variationDesc')
    ingredients: str | None = Field(alias='ingredientDesc')
    price_usd: str | None = Field(alias='listPrice')
    value_price_usd: str | None = Field(alias='valuePrice')
    sale_price_usd: str | None = Field(alias='salePrice')
    limited_edition: int | None = Field(alias='isLimitedEdition')
    new: int | None = Field(alias='isNew')
    online_only: int | None = Field(alias='isOnlineOnly')
    out_of_stock: int | None = Field(alias='isOutOfStock')
    sephora_exclusive: int | None = Field(alias='isSephoraExclusive')
    highlights: list[Highlight] | None

    @validator('size', 'variation_type', 'variation_value')
    def clean_str_none(cls, field):
        """Checks if the value is the string 'None' -> None.
        Cleans up the string from extraneous characters.
        """
        if 'None' in field:
            return None
        return field.strip().replace('®', '').replace('™', '').replace(' ', '')

    @validator('ingredients')
    def clean_ingredients(cls, field) -> list[str]:
        """Cleans information about ingredients and returns a list of cleaned ingredients.
            input (str):
                '-Vit C: very healing<b>Aqua,<i>Niacinamide</i>, Dimethyl™</b>The product is safe'
            output (list[str]):
                ['Aqua, Niacinamide, Dimethyl']
        Steps:
            1. Replace specific HTML tags from a string with an unused character ('~').
            2. Delete remaining specific characters (e.g., trademark symbols) from the string.
            3. Split the string by the '~' character.
            4. Check each element of the list against a list of unwanted prefixes:
               remove any elements that start with those prefixes and remove empty strings.
            5. Return the list of cleaned ingredients.
        """
        # Replace the matched characters with '~' and ''
        field = re.sub(r'(<b>|</b>|<br>|</br>|<br />|<BR>|<p>|</p>|<span>|</span>|</a>|<a)', '~', field)
        field = re.sub(r'(<.*?>|\n|®|™|)', '', field)

        # Split by '~' and remove elements that start with unwanted prefixes
        UNWANTED_PREFIXES = ('-', '—', '–', 'Before using', 'Clean at Sephora prod', 'Disclaimer', 'DISCLA', 'Please',
                             'Acrylates',  'Formulated without', 'Warning', 'Highlighted', 'Penetrates', 'All HUM',
                             'The ingredients that', 'PRODUCT ING', 'Ingredient list', 'All ingred', 'Product ingred',
                             'Sulfates', 'Free of artificial', 'As part', 'This', '*', '(*', '+', 'The calculation',
                             '(1) the synthetic', 'and', '(2) the', ', Petrolatum', 'Fresh prod', 'Acqua di Parma')
        field = [i.strip()
                 for i in field.replace(' ', '').replace(' ', '').split('~')
                 if not i.strip().startswith(UNWANTED_PREFIXES)]
        field = list(filter(None, field))
        return field

    @validator('price_usd', 'sale_price_usd')
    def to_float_cur_and_sale_price(cls, field) -> float:
        """Transforms '$84.50' -> 84.5"""
        return float(field.strip()[1:])

    @validator('value_price_usd')
    def to_float_value_price(cls, field) -> float:
        """Transforms '($84.50 value)' -> 84.5"""
        return float(field.strip()[2:-7])

    @validator('highlights')
    def all_highlights_to_list(cls, field) -> list:
        """Transforms {{'name': 'Vegan'}, {'name': 'Oil Free'}} -> ['Vegan', 'Oil Free']"""
        return [val.name for val in field]


class BrandDetails(BaseModel):
    b_id: str | None = Field(alias='brandId')
    b_name: str | None = Field(alias='displayName')


class ProductDetails(BaseModel):
    product_id: str | None = Field(alias='productId')
    product_name: str | None = Field(alias='displayName')
    brand_id: BrandDetails | None = Field(alias='brand')
    brand_name: BrandDetails | None = Field(alias='brand')
    loves_count: int | None = Field(alias='lovesCount')
    rating: float | None
    reviews: int | None

    @validator('product_name')
    def clean_product_name(cls, field) -> str:
        """Clears the product name from extraneous characters."""
        return field.strip().replace('®', '').replace('™', '').replace(' ', '')

    @validator('brand_id')
    def unpack_brand_id(cls, field) -> str:
        """Extracts from {'b_id': '6236', 'b_name': 'Chanel'} -> '6236'."""
        return list(field)[0][1]

    @validator('brand_name')
    def unpack_brand_name(cls, field) -> str:
        """Extracts from {'b_id': '6236', 'b_name': 'Chanel'} -> 'Chanel'.
        After extraction clears the brand name from extraneous characters"""
        return list(field)[1][1].strip().replace('®', '').replace('™', '').replace(' ', '')


class ProductInfo(BaseModel):
    """From the json file of each product, we extract and validate needed fields.

        - If the field has no argument --> returns None
        - `Field()` function is for renaming --> new_name: any = Field(alias='oldName')
    """
    product_details: ProductDetails | None = Field(alias='productDetails')
    current_sku: CurrentSku | None = Field(alias='currentSku')
    categories: Category | None = Field(alias='parentCategory')

    child_count: ChildSkus | None
    child_max_price: ChildSkus | None
    child_min_price: ChildSkus | None
    sale_child: list[ChildSkus] | None = Field(alias='onSaleChildSkus', exclude=True)  # auxiliary field
    reg_child: list[ChildSkus] | None = Field(alias='regularChildSkus', exclude=True)  # auxiliary field

    @validator('categories')
    def extract_categ_names(cls, field) -> dict:
        """Unpacks all category names (values) from nested dictionaries into one list,
        then puts them into the output dictionary in the correct order.

        Returns dictionary:
            {'primary_category': name | None, 'secondary_category': name | None, 'tertiary_category': name | None}
        """
        # unpack all names in one list
        d = field.dict()

        def nested_dict_values(d):
            for v in d.values():
                if isinstance(v, dict):
                    yield from nested_dict_values(v)
                else:
                    yield v

        names = list(nested_dict_values(d))

        # put names in one dictionary in the correct order
        if (len(names) == 3) and (names.count(None) == 0):
            categs = {'primary_category': names[2], 'secondary_category': names[1], 'tertiary_category': names[0]}
        elif (len(names) == 3) and (names.count(None) == 1):
            categs = {'primary_category': names[1], 'secondary_category': names[0], 'tertiary_category': names[2]}
        else:
            categs = {'primary_category': names[0], 'secondary_category': names[1], 'tertiary_category': None}
        return categs

    @root_validator
    def validate_child(cls, values) -> dict:
        """Returns three calculated dictionary.
        Returns::
            {'child_count': int <= 0},
            {'child_max_price': int | None},
            {'child_min_price': int | None}
        """
        values['child_count'] = {'child_count':
                                     sum([len(lst) for lst in (values['reg_child'], values['sale_child']) if lst])}

        # put all child prices in one set
        child_prices = set()
        for field in (values['reg_child'], values['sale_child']):
            if field:
                for val in field:
                    if val.list_price: child_prices.add(val.list_price)
                    if val.sale_price: child_prices.add(val.sale_price)
        values['child_max_price'] = {'child_max_price': max(child_prices) if child_prices else None}
        values['child_min_price'] = {'child_min_price': min(child_prices) if child_prices else None}

        return values
