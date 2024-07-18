import random
from typing import Callable

Individual = list[bool]
Population = list[Individual]
FitnessCallback = Callable[[Individual], float]


class GeneticAlgorithm:
    def __init__(
        self,
        fitness: FitnessCallback,
        chromosome_length: int,
        population_size: int,
        mutation_rate: float,
        crossover_rate: float,
        generations: int,
        on_population_created: Callable[[int, Population], None] | None = None,
    ) -> None:
        self.fitness = fitness
        self.chromosome_length = chromosome_length
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.generations = generations
        self.on_population_processed = on_population_created

    def __generate_individual(self) -> Individual:
        return [randbool() for _ in range(self.chromosome_length)]

    def __generate_population(
        self,
    ) -> Population:
        return [self.__generate_individual() for _ in range(self.population_size)]

    def __select(self, population: Population):
        fitnesses: list[float] = [self.fitness(individual) for individual in population]
        total_fitness = sum(fitnesses)
        selection_probs = [fitness / total_fitness for fitness in fitnesses]
        return population[
            random.choices(range(len(population)), weights=selection_probs, k=1)[0]
        ]

    def __crossover(self, parent1: Individual, parent2: Individual):
        if random.random() < self.crossover_rate:
            point = random.randint(1, len(parent1) - 1)
            return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]
        return parent1, parent2

    def __mutate(self, individual: Individual) -> Individual:
        return [
            bit if random.random() > self.mutation_rate else not bit
            for bit in individual
        ]

    def run(
        self,
    ) -> tuple[list[Individual], list[float]]:
        best_individuals: list[Individual] = []
        best_fitnesses: list[float] = []
        population: Population = self.__generate_population()
        for i in range(self.generations - 1):
            new_population: Population = []
            for _ in range(len(population) // 2):
                parent1 = self.__select(population)
                parent2 = self.__select(population)
                child1, child2 = self.__crossover(parent1, parent2)
                new_population.append(self.__mutate(child1))
                new_population.append(self.__mutate(child2))
            population = new_population
            if self.on_population_processed is not None:
                self.on_population_processed(i + 1, population)
        if self.on_population_processed is not None:
            self.on_population_processed(self.generations, population)
        fitnesses: list[float] = [self.fitness(individual) for individual in population]
        best_fitness = max(fitnesses)
        best_individual_index = fitnesses.index(best_fitness)
        best_individual = population[best_individual_index]

        best_fitnesses.append(best_fitness)
        best_individuals.append(best_individual)
        return best_individuals, best_fitnesses


def randbool() -> bool:
    return random.randint(0, 1) == 1


def individual_to_str(individual: Individual) -> str:
    result = ""
    for bit in individual:
        result += str(int(bit))
    return result


def individual_to_int(individual: Individual) -> int:
    result = 0
    for i in range(len(individual)):
        result += int(individual[i]) * 2**i
    return result


if __name__ == "__main__":

    def fitness(individual: Individual) -> int:
        x = individual_to_int(individual)
        return x**2

    def on_population_created(i: int, population: Population):
        print([individual_to_int(individual) for individual in population])
        print(f"Best fitness: {fitness(max(population, key=fitness))}")

    ga = GeneticAlgorithm(
        fitness=fitness,
        chromosome_length=8,
        population_size=20,
        mutation_rate=0.01,
        crossover_rate=0.7,
        generations=100,
        on_population_created=on_population_created,
    )

    results, fitnesses = ga.run()
    print(f"Result: {individual_to_str(results[-1])}, fitness: {fitnesses[-1]}")
