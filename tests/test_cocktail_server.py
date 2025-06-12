import pytest
from respx import MockRouter

from mcp_server.cocktail import (
    format_cocktail_details,
    format_cocktail_summary,
    format_ingredient,
    list_cocktails_by_first_letter,
    list_random_cocktails,
    lookup_cocktail_details_by_id,
    search_cocktail_by_name,
    search_ingredient_by_name,
    API_BASE_URL, # Import for constructing mock URLs
)

# Sample data for formatting functions
SAMPLE_DRINK_DATA = {
    "idDrink": "11007",
    "strDrink": "Margarita",
    "strDrinkAlternate": None,
    "strTags": "IBA,ContemporaryClassic",
    "strCategory": "Ordinary Drink",
    "strIBA": "Contemporary Classics",
    "strAlcoholic": "Alcoholic",
    "strGlass": "Cocktail glass",
    "strInstructions": "Rub the rim of the glass with the lime slice to make the salt stick to it. Take care to moisten only the outer rim and sprinkle the salt on it. The salt should present to the lips of the drinker and not get into the drink. Shake the other ingredients with ice, then carefully pour into the glass.",
    "strDrinkThumb": "https://www.thecocktaildb.com/images/media/drink/5noda61589575158.jpg",
    "strIngredient1": "Tequila",
    "strMeasure1": "1 1/2 oz ",
    "strIngredient2": "Triple sec",
    "strMeasure2": "1/2 oz ",
    "strIngredient3": "Lime juice",
    "strMeasure3": "1 oz ",
    "strIngredient4": None,
    "strMeasure4": None,
    "dateModified": "2017-09-02 12:44:38",
}

SAMPLE_INGREDIENT_DATA = {
    "idIngredient": "1",
    "strIngredient": "Vodka",
    "strDescription": "Vodka is a clear distilled alcoholic beverage with origins in Eastern Europe. It is composed primarily of water and ethanol, but sometimes with traces of impurities and flavorings. Traditionally, it is made by distilling liquid from fermented cereal grains. Potatoes have also been used in more recent times and some modern brands use fruits, honey, or maple sap as the base.",
    "strType": "Vodka",
    "strAlcohol": "Yes",
    "strABV": "40",
}

# Tests for formatting functions

def test_format_cocktail_summary():
    summary = format_cocktail_summary(SAMPLE_DRINK_DATA)
    assert "ID: 11007" in summary
    assert "Name: Margarita" in summary
    assert "Category: Ordinary Drink" in summary
    assert "Instructions: Rub the rim of the glass with the lime slice" in summary # Check truncation
    assert "..." in summary # Check truncation indicator
    assert len(SAMPLE_DRINK_DATA['strInstructions']) > 150 # Ensure original is long enough for truncation

def test_format_cocktail_details():
    details = format_cocktail_details(SAMPLE_DRINK_DATA)
    assert "ID: 11007" in details
    assert "Name: Margarita" in details
    assert "Tags: IBA,ContemporaryClassic" in details
    assert "Ingredients:" in details
    assert "- 1 1/2 oz Tequila" in details
    assert "- 1/2 oz Triple sec" in details
    assert "- 1 oz Lime juice" in details
    assert "Image URL: https://www.thecocktaildb.com/images/media/drink/5noda61589575158.jpg" in details

def test_format_ingredient():
    formatted_ingredient = format_ingredient(SAMPLE_INGREDIENT_DATA)
    assert "ID: 1" in formatted_ingredient
    assert "Name: Vodka" in formatted_ingredient
    assert "Type: Vodka" in formatted_ingredient
    assert "Description: Vodka is a clear distilled alcoholic beverage" in formatted_ingredient

# Helper for mock API responses
def mock_cocktail_api(mock_router: MockRouter, endpoint: str, params: dict, response_json: dict):
    url = f"{API_BASE_URL}{endpoint}"
    if params: # httpx sorts params by key for matching
        sorted_params = tuple(sorted(params.items()))
        mock_router.get(url, params=sorted_params).respond(json=response_json)
    else:
        mock_router.get(url).respond(json=response_json)

@pytest.mark.asyncio
async def test_search_cocktail_by_name_found():
    router = MockRouter(assert_all_called=False) # False because tenacity retries can make extra calls
    mock_response = {"drinks": [SAMPLE_DRINK_DATA]}
    mock_cocktail_api(router, "search.php", {"s": "margarita"}, mock_response)

    with router:
        result = await search_cocktail_by_name("margarita")

    assert "Found cocktails:" in result
    assert "Name: Margarita" in result

@pytest.mark.asyncio
async def test_search_cocktail_by_name_not_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": None} # API returns null for no drinks
    mock_cocktail_api(router, "search.php", {"s": "unknowncocktail"}, mock_response)

    with router:
        result = await search_cocktail_by_name("unknowncocktail")

    assert "No cocktails found with that name." in result

@pytest.mark.asyncio
async def test_list_cocktails_by_first_letter_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": [SAMPLE_DRINK_DATA]}
    mock_cocktail_api(router, "search.php", {"f": "m"}, mock_response)

    with router:
        result = await list_cocktails_by_first_letter("m")

    assert "Cocktails starting with 'M':" in result
    assert "Name: Margarita" in result

@pytest.mark.asyncio
async def test_list_cocktails_by_first_letter_not_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": None}
    mock_cocktail_api(router, "search.php", {"f": "x"}, mock_response)

    with router:
        result = await list_cocktails_by_first_letter("x")

    assert "No cocktails found starting with the letter 'X'" in result

@pytest.mark.asyncio
async def test_list_cocktails_by_first_letter_invalid_input():
    result = await list_cocktails_by_first_letter("invalid")
    assert "Invalid input: Please provide a single letter." in result
    result_empty = await list_cocktails_by_first_letter("")
    assert "Invalid input: Please provide a single letter." in result_empty


@pytest.mark.asyncio
async def test_search_ingredient_by_name_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"ingredients": [SAMPLE_INGREDIENT_DATA]}
    mock_cocktail_api(router, "search.php", {"i": "vodka"}, mock_response)

    with router:
        result = await search_ingredient_by_name("vodka")

    assert "Name: Vodka" in result
    assert "Type: Vodka" in result

@pytest.mark.asyncio
async def test_search_ingredient_by_name_not_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"ingredients": None}
    mock_cocktail_api(router, "search.php", {"i": "unknowningredient"}, mock_response)

    with router:
        result = await search_ingredient_by_name("unknowningredient")

    assert "No ingredient found with that name." in result

@pytest.mark.asyncio
async def test_list_random_cocktails_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": [SAMPLE_DRINK_DATA]}
    mock_cocktail_api(router, "random.php", None, mock_response)

    with router:
        result = await list_random_cocktails()

    assert "Name: Margarita" in result
    assert "Ingredients:" in result

@pytest.mark.asyncio
async def test_list_random_cocktails_not_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": None}
    mock_cocktail_api(router, "random.php", None, mock_response)

    with router:
        result = await list_random_cocktails()

    assert "Could not fetch a random cocktail." in result

@pytest.mark.asyncio
async def test_lookup_cocktail_details_by_id_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": [SAMPLE_DRINK_DATA]}
    mock_cocktail_api(router, "lookup.php", {"i": "11007"}, mock_response)

    with router:
        result = await lookup_cocktail_details_by_id("11007")

    assert "Name: Margarita" in result
    assert "ID: 11007" in result

@pytest.mark.asyncio
async def test_lookup_cocktail_details_by_id_not_found():
    router = MockRouter(assert_all_called=False)
    mock_response = {"drinks": None}
    mock_cocktail_api(router, "lookup.php", {"i": "99999"}, mock_response)

    with router:
        result = await lookup_cocktail_details_by_id("99999")

    assert "No cocktail found with ID 99999" in result

@pytest.mark.asyncio
async def test_lookup_cocktail_details_by_id_invalid_input():
    result = await lookup_cocktail_details_by_id("abc")
    assert "Invalid input: Cocktail ID must be a number." in result
