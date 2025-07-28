# Standard library imports
import asyncio # For asynchronous programming, used with the Algolia client

# Third-party library imports
from algoliasearch.search.client import SearchClient # Algolia Python API client for search functionality

class AlgoliaUploader:
    """
    A class to handle uploading transcribed podcast data to Algolia for search indexing.
    """

    def __init__(self, algolia_app_id, algolia_api_key, algolia_index="podcast_episodes"):
        """
        Initializes the AlgoliaUploader.

        Args:
            algolia_app_id (str): Your Algolia Application ID.
            algolia_api_key (str): Your Algolia Write API Key (or Admin API Key).
            algolia_index (str, optional): The name of the Algolia index to use.
                                           Defaults to "podcast_episodes".
        """
        self.algolia_app_id = algolia_app_id
        self.algolia_api_key = algolia_api_key
        self.algolia_index = algolia_index
        self.algolia_client = self._init_algolia_client() # Initialize the client on instantiation

    def _init_algolia_client(self):
        """
        Initializes the Algolia SearchClient.
        Includes a defensive check to ensure that actual API keys are being used,
        raising a ValueError if placeholder values are detected.
        """
        # This check is crucial to prevent connection errors due to incorrect credentials.
        if self.algolia_app_id in ["your_algolia_app_id", "your_app_id"] or \
           self.algolia_api_key == "your_algolia_api_key" or \
           not self.algolia_app_id or not self.algolia_api_key:
            raise ValueError(
                "Algolia credentials are not properly configured. "
                "Please ensure APP_ID and ALGOLIA_WRITE_API_KEY "
                "in your .env file are set to your actual Algolia keys, "
                "not the placeholder values."
            )

        # Initialize the Algolia SearchClient with the provided App ID and API Key.
        # This client will handle asynchronous operations automatically if 'aiohttp' is installed.
        client = SearchClient(self.algolia_app_id, self.algolia_api_key)
        print(f"Algolia client initialized with App ID: '{self.algolia_app_id}'.")
        return client

    async def upload_transcripts(self, records):
        """
        Uploads a list of records (episodes) to the configured Algolia index.

        Args:
            records (list): A list of tuples/lists, where each element is an episode record
                            containing (id, title, transcript) from the database.
                            These will be converted into Algolia-compatible objects.
        """
        if not self.algolia_client:
            print("Algolia client not configured. Skipping upload to Algolia.")
            return

        if not records:
            print("No records found to upload to Algolia.")
            return

        print(f"Uploading {len(records)} records to Algolia index '{self.algolia_index}'...")

        # Prepare objects in the format Algolia expects, including 'objectID'
        objects = [
            {"objectID": str(rec["objectID"]), "title": rec["title"], "transcription": rec["transcription"]}
            for rec in records
        ]

        try:
            # Call save_objects asynchronously.
            # The Algolia Python client v4's save_objects method returns a list of BatchResponse objects.
            response_list = await self.algolia_client.save_objects(
                self.algolia_index, # The name of the Algolia index
                objects             # The list of objects (dictionaries) to upload
            )

            # Check if the response list is not empty and contains BatchResponse objects
            if response_list and isinstance(response_list, list) and len(response_list) > 0:
                first_response_item = response_list[0]
                if hasattr(first_response_item, 'task_id'):
                    task_id = first_response_item.task_id
                    print(f"Uploaded {len(objects)} records to Algolia. Task ID: {task_id}")

                    # Wait for the Algolia task to complete asynchronously
                    await self.algolia_client.wait_for_task(
                        index_name=self.algolia_index,
                        task_id=task_id
                    )
                    print("Algolia upload task completed successfully.")
                else:
                    print(f"Algolia response item does not contain 'task_id' attribute: {first_response_item}")
            else:
                print(f"Algolia save_objects returned an empty or unexpected response: {response_list}")

        except Exception as e:
            print(f"Error uploading to Algolia: {e}")

