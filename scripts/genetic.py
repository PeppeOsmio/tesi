import random
from typing import Callable

Individual = list[bool]
Population = list[Individual]
FitnessCallback = Callable[[Individual], float]


def randbool() -> bool:
    return random.randint(0, 1) == 1


# Helper Functions
def generate_individual(chromosome_length: int) -> Individual:
    return [randbool() for _ in range(chromosome_length)]


def generate_population(population_size: int, chromosome_length: int) -> Population:
    return [generate_individual(chromosome_length) for _ in range(population_size)]


def select(population: Population, fitness: FitnessCallback):
    total_fitness = sum(fitness(individual) for individual in population)
    selection_probs = [fitness(individual) / total_fitness for individual in population]
    return population[
        random.choices(range(len(population)), weights=selection_probs, k=1)[0]
    ]


def crossover(parent1: Individual, parent2: Individual, crossover_rate: float):
    if random.random() < crossover_rate:
        point = random.randint(1, len(parent1) - 1)
        return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]
    return parent1, parent2


def mutate(individual: Individual, mutation_rate: float) -> Individual:
    return [bit if random.random() > mutation_rate else not bit for bit in individual]


def run_genetic_algorithm(
    fitness: FitnessCallback,
    chromosome_length: int,
    population_size: int,
    mutation_rate: float,
    crossover_rate: float,
    generations: int,
    on_population_created: Callable[[Population], None] | None = None,
) -> Individual:
    population = generate_population(
        population_size=population_size, chromosome_length=chromosome_length
    )
    if on_population_created is not None:
        on_population_created(population)
    for _ in range(generations):
        new_population: Population = []
        for _ in range(len(population) // 2):
            parent1 = select(population, fitness=fitness)
            parent2 = select(population, fitness=fitness)
            child1, child2 = crossover(parent1, parent2, crossover_rate=crossover_rate)
            new_population.append(mutate(child1, mutation_rate=mutation_rate))
            new_population.append(mutate(child2, mutation_rate=mutation_rate))
        population = new_population
        if on_population_created is not None:
            on_population_created(population)
    best_individual = max(population, key=fitness)
    return best_individual


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

    def on_population_created(population: Population):
        print([individual_to_int(individual) for individual in population])
        print(f"Best fitness: {fitness(max(population, key=fitness))}")

    result = run_genetic_algorithm(
        fitness=fitness,
        chromosome_length=8,
        population_size=20,
        mutation_rate=0.01,
        crossover_rate=0.7,
        generations=100,
        on_population_created=on_population_created,
    )
