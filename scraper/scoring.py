# scoring.py

import os
import json

def parse_price(price_str: str) -> float:
    """
    Converts a Turkish format price string (e.g. '43.990,00 TL') to a float (e.g. 43990.00).
    - Removes ' TL'.
    - Replaces commas with dots for decimals.
    - Removes dots used as thousand separators.
    """
    if not price_str:
        return 0.0
    
    # Remove ' TL' if exists
    price_str = price_str.replace(" TL", "").strip()
    
    # Replace comma (decimal) with dot
    price_str = price_str.replace(",", ".")
    
    # Split by dot to handle thousand separators
    parts = price_str.split(".")
    if len(parts) > 1:
        # Join all except the last into an integer part
        integer_part = "".join(parts[:-1])
        decimal_part = parts[-1]
        cleaned_str = integer_part + "." + decimal_part
    else:
        cleaned_str = parts[0]
    
    try:
        return float(cleaned_str)
    except ValueError:
        return 0.0


def compute_base_score(hotel: dict) -> float:
    """
    Calculates a base score for the hotel based on certain criteria:
      1) If 'cancel_policy' contains 'Risksiz rezervasyon' => +1.0
      2) If 'recomended_hotel' is not null => +1.0
      3) hotel_features count => each feature adds +0.05
      4) accommodation_types => different increments according to the type
    """
    base_score = 0.0
    
    # 1) Check for 'Risksiz rezervasyon' in cancel_policy
    cancel_policy = hotel.get("cancel_policy", "")
    if "Risksiz rezervasyon" in cancel_policy:
        base_score += 1.0
    
    # 2) If 'recomended_hotel' is not None
    if hotel.get("recomended_hotel") is not None:
        base_score += 1.0
    
    # 3) Count number of features
    features_str = hotel.get("hotel_features", "")
    if features_str:
        # Split by comma and strip whitespace
        features_list = [x.strip() for x in features_str.split(",")]
        base_score += 0.05 * len(features_list)
    
    # 4) Accommodation types scoring
    accom = hotel.get("accommodation_types", "").strip().lower()
    if "ultra her şey dahil" in accom:
        base_score += 2.0
    elif "her şey dahil" in accom:
        base_score += 1.5
    elif "yarım pansiyon" in accom:
        base_score += 1.0
    elif "oda kahvaltı" in accom:
        base_score += 0.5
    elif "sadece oda" in accom:
        base_score += 0.3
    
    return base_score


def compute_final_score(hotel: dict) -> float:
    """
    Computes the final score by dividing the base score by the parsed price value.
    Example: final_score = base_score / price
    If the price is zero or invalid, we set price to 1 to avoid division by zero.
    """
    price_val = parse_price(hotel.get("price", ""))
    base_score = compute_base_score(hotel)
    
    if price_val <= 0:
        # To avoid zero or negative price
        price_val = 1
    
    final_score = base_score / price_val
    return final_score
