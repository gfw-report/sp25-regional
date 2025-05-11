import asyncio
import aiohttp
import json

async def query_api(session, domain):
    """Asynchronously query the API for the given domain and return the response."""
    api_key = ""  # API Key
    base_url = "https://website-categorization.whoisxmlapi.com/api/v3"
    url = f"{base_url}?apiKey={api_key}&url={domain}"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch data for {domain}: {response.status}")
                return None
    except Exception as e:
        print(f"Error occurred while fetching data for {domain}: {e}")
        return None

async def main():
    input_file = 'henan-blocklist.txt'
    output_file = 'henan-category-data.json'

    # Read domains
    with open(input_file, 'r') as file:
        domains = [line.strip() for line in file]

    data = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(domains), 30):
            tasks = [query_api(session, domain) for domain in domains[i:i+30]]
            results = await asyncio.gather(*tasks)
            data.extend([result for result in results if result])

            print("Progress", i + 1, "/", len(domains))
            # Save data after every batch
            with open(output_file, 'w') as file:
                json.dump(data, file, indent=4)

            # Rate Limit is 30 requests per second
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
