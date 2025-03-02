# pipelines.py

from itemadapter import ItemAdapter
import os
import json
from scoring import compute_final_score

class ScorePipeline:
    """
    A pipeline that accumulates all scraped hotel items in memory, computes a 
    final score for each, then writes only the top 10 results to a JSON file 
    when the spider closes.
    """

    def __init__(self):
        """
        Initialize the pipeline with an empty list to store hotel items.
        
        Attributes:
            hotels (list): A list to store hotel items throughout the spider run.
        """
        self.hotels = []

    def process_item(self, item, spider):
        """
        Process each scraped item, converting it to a dictionary and storing 
        it in the pipeline's internal list.

        Args:
            item (dict or scrapy.Item): The scraped hotel item.
            spider (scrapy.spiders.Spider): The active spider.

        Returns:
            The original item, which is passed on to the next pipeline (if any).
        """
        # Convert item to a dictionary and append it to the hotels list
        self.hotels.append(dict(item))
        return item

    def close_spider(self, spider):
        """
        Perform final operations after the spider finishes:
        
        1) Compute the final_score for each hotel.
        2) Sort the hotels in descending order by final_score.
        3) Slice the top 10 hotels.
        4) Write these top 10 hotels to a JSON file under the 'output' directory.
        
        Args:
            spider (scrapy.spiders.Spider): The spider that has finished running.
        """
        # 1) Compute final_score for each hotel
        for hotel in self.hotels:
            hotel["final_score"] = compute_final_score(hotel)

        # 2) Sort hotels by final_score in descending order
        hotels_sorted = sorted(
            self.hotels,
            key=lambda x: x["final_score"],
            reverse=True
        )

        # 3) Take the first 10 hotels
        top_10_hotels = hotels_sorted[:10]

        # 4) Write these top 10 hotels to a JSON file
        output_path = f"output/{spider.destination}_scored.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(top_10_hotels, out, ensure_ascii=False, indent=4)

        # Print a confirmation message
        print(
            f"Scoring completed. Only the top 10 records were written to '{output_path}'."
        )
