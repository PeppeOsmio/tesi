from tesi.zappai.repositories.crop_repository import CropRepository
from tesi.zappai.utils.genetic import GeneticAlgorithm, Individual
from sklearn.ensemble import RandomForestRegressor

class CropOptimizerService:
    def __init__(self, crop_repository: CropRepository) -> None:
        self.crop_repository = crop_repository

        self.__genetic_algorithm = GeneticAlgorithm(
            fitness=self.fitness,
            chromosome_length=8,
            population_size=20,
            mutation_rate=0.01,
            crossover_rate=0.7,
            generations=100,
            on_population_created=None,
        )

    def fitness(self, crop_yield_model: RandomForestRegressor) -> int:
        x = individual_to_int(individual)
        return x**2
