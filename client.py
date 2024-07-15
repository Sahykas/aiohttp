import asyncio
import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "http://127.0.0.1:8080/ads",
            json={'title': 'ads_1',
                  'description':'Work',
                  'owner': 'Progr',
                  }
        )
        json_data = await response.text()
        print(response.status)
        print(json_data)

        response = await session.get(
            "http://127.0.0.1:8080/ads/1",
        )
        json_data = await response.text()
        print(response.status)
        print(json_data)

if __name__ == "__main__":
    asyncio.run(main())
