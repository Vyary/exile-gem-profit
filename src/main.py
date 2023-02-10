from typing import List
import requests
import pandas as pd
import gems


def gem_quality_type(name: str) -> str:
    """
    This function gets the gem quality type based on its prefix

    Parameters:
        name : The name of the gem

    Returns
        The gem's quality type
    """
    # Create a dictionary of gem quality types and their corresponding prefixes
    quality_types: dict[str, List[str]] = {
        "Vaal": ["Vaal"],
        "Alternative": ["Anomalous", "Divergent", "Phantasmal"],
        "Awakened": ["Awakened"],
    }

    # Loop through the dictionary and check if the gem name
    # has a prefix that matches any of the quality types
    for quality, prefixes in quality_types.items():
        for prefix in prefixes:
            if prefix in name:
                return quality

    # If no prefix was found, return "Basic"
    return "Basic"


def create_gem_object(
    gem_name: str, variant: str, price: float, quality: str, listed: int
) -> None:
    """
    This function creates a gem object in the `gems.Gem` class if
    it doesn't exist and updates the given price

    Parameters:
        gem_name : Name of the gem
        variant : Variant of the gem
        price : Price of the gem of current variant
        quality : Quality type
        listed : Number of listings for the successful gems of set gem
    """
    # Get the dictionary of gem objects
    dictionary = gems.Gem.dictionary

    # Check if there is object with the set name if not create new object
    if gem_name not in dictionary:
        new_object = gems.Gem(gem_name)
        dictionary[gem_name] = new_object

    # Update the attributes of the matching gem object
    if gem_name in dictionary:
        obj = gems.Gem.dictionary[gem_name]

        # base price
        is_basic_1_20 = variant == "1/20" and quality == "Basic"
        is_alternative_1 = variant == "1" and quality == "Alternative"
        is_awakened_1 = variant == "1" and quality == "Awakened"
        # leveled price
        is_leveled_20_20 = variant == "20/20"
        # fail price
        is_not_vaal_20_20c = variant == "20/20c" and quality != "Vaal"
        is_awakened_5_20c = variant == "5/20c" and quality == "Awakened"
        # semi fail price
        is_vaal_20_20c = variant == "20/20c" and quality == "Vaal"
        # success price
        is_not_vaal_21_20c = variant == "21/20c" and quality != "Vaal"
        is_awakened_6_20c = variant == "6/20c" and quality == "Awakened"

        if is_basic_1_20 or is_alternative_1 or is_awakened_1:
            obj.base_price = price
        elif is_leveled_20_20:
            obj.leveled_price = price
            obj.listed_leveled = listed
        elif is_not_vaal_20_20c or is_awakened_5_20c:
            obj.fail_price = price
        elif is_vaal_20_20c:
            obj.vaal_price = price
        elif is_not_vaal_21_20c or is_awakened_6_20c:
            obj.success_price = price
            obj.listed_21_20 = listed


def go_over_elements(data: dict) -> dict:
    """
    This function goes over the collected data from the API,
    calls a function to create an object for each gem, and
    returns a dictionary of gem objects

    Parameters:
        data (dict) : A dictionary containing the collected data from
        the API response

    Returns:
        dict: A dictionary of gem objects
    """
    # Loop over the gems in the data(api response)
    for gem in data["lines"]:
        gem_name = gem["name"]
        variant = gem["variant"]
        price = gem["chaosValue"]

        # fixes issue if a gem is missing a listingCount
        try:
            listed = gem["listingCount"]
        except KeyError:
            listed = 0

        # Get the gem's quality
        quality = gem_quality_type(gem_name)

        # Handle special cases for gems with the "Vaal" quality
        if quality == "Vaal":
            gem_name = gem_name.replace("Vaal ", "")

        # Create a gem object for the current gem
        create_gem_object(gem_name, variant, price, quality, listed)

    # Return the dictionary of gem objects
    return gems.Gem.dictionary


def save_data(dict: dict):
    """
    This function goes over all objects in the class dictionary,
    makes a dataframe, and saves the information in two CSV files.
    Parameters:
        dict (dict): A dictionary of gem objects
    """
    df = pd.DataFrame.from_dict(dict, orient="index")

    # Set the column names
    df.columns = [
        "Gem Name",
        "Buy price",
        "Corrupted 20/20",
        "Success 21/20",
        "Listed 21/20",
        "Vaal price",
        "Leveled 20/20",
        "Listed L20/20",
    ]

    # Split the DataFrame into two separate dataframes based on the columns
    df1 = df[
        [
            "Gem Name",
            "Buy price",
            "Corrupted 20/20",
            "Success 21/20",
            "Listed 21/20",
            "Vaal price",
        ]
    ]

    df2 = df[
        [
            "Gem Name",
            "Buy price",
            "Leveled 20/20",
            "Listed L20/20",
        ]
    ]

    # Sort the first DataFrame by the "Success 21/20" column in descending order
    df1 = df1.sort_values("Success 21/20", ascending=False)
    # Save the first DataFrame as a CSV file
    df1.to_csv("output/gems_to_corrupt.csv", index=False, encoding="utf-8")

    # Sort the second DataFrame by the "Leveled 20/20" column in descending order
    df2 = df2.sort_values("Leveled 20/20", ascending=False)
    # Save the second DataFrame as a CSV file
    df2.to_csv("output/gems_to_level.csv", index=False, encoding="utf-8")


def main():
    # Set the URL for the API call
    url = (
        "https://poe.ninja/api/data/itemoverview?league="
        "Sanctum&type=SkillGem&language=en"
    )
    # Send a request to the API and get the response
    response = requests.get(url).json()

    # Get a dictionary of gem objects from the response
    gems_dict = go_over_elements(response)

    # Save the gem data to a CSV file
    save_data(gems_dict)


if __name__ == "__main__":
    main()
