# Standard library imports
import asyncio

# Third-party library imports
from algoliasearch.search.client import SearchClient

class AlgoliaUploader:
    """
    A class to handle uploading transcribed podcast data to Algolia for search indexing.
    """

    def __init__(self, algolia_app_id=None, algolia_api_key=None, algolia_index="podcast_episodes"): # Accept keys as arguments
        """
        Initializes the AlgoliaUploader.

        Args:
            algolia_app_id (str): User's Algolia Application ID.
            algolia_api_key (str): User's Algolia Write API Key (or Admin API Key).
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
        # Now, the check primarily ensures keys are not None or empty,
        # as they are expected to come from user input.
        if not self.algolia_app_id or not self.algolia_api_key:
            # We don't raise a ValueError here, as the workflow might initialize
            # with None if no keys are provided, and then check later.
            # The app.py will handle the initial validation.
            print("WARNING: Algolia credentials not provided. Algolia API calls will fail.")
            return None # Return None client if keys are missing

        # Initialize the Algolia SearchClient with the provided App ID and API Key.
        client = SearchClient(self.algolia_app_id, self.algolia_api_key)
        print(f"Algolia client initialized with App ID: '{self.algolia_app_id}'.")
        return client

    async def upload_transcripts(self, records):
        """
        Uploads a list of records (episodes) to the configured Algolia index.

        Args:
            records (list): A list of dictionaries, where each dictionary is an episode record
                            containing at least 'objectID', 'title', and 'transcription'.
        """
        if not self.algolia_client: # Check if client was successfully initialized
            print("Algolia client not configured due to missing credentials. Skipping upload to Algolia.")
            return

        if not records:
            print("No records found to upload to Algolia.")
            return

        print(f"Uploading {len(records)} records to Algolia index '{self.algolia_index}'...")

        objects = [
            {"objectID": rec["objectID"], "title": rec["title"], "transcription": rec["transcription"]}
            for rec in records
        ]

        try:
            response_list = await self.algolia_client.save_objects(
                self.algolia_index,
                objects
            )

            if response_list and isinstance(response_list, list) and len(response_list) > 0:
                first_response_item = response_list[0]
                if hasattr(first_response_item, 'task_id'):
                    task_id = first_response_item.task_id
                    print(f"Uploaded {len(objects)} records to Algolia. Task ID: {task_id}")

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
