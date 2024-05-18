import asyncio
from tesi.repositories import FuturePredictionsRepository

async def main():
    future_predictions_repository = FuturePredictionsRepository(predictions_folder="data/future_climate")
    await future_predictions_repository.load_predictions_df()

if __name__ == "__main__":
    asyncio.run(main())