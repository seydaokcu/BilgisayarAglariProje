import random
from Ag_olusturma import (
    G,
    is_valid_path,
    total_delay,
    total_reliability,
    reliability_cost,
    resource_cost,
    weighted_sum_method
)

# ---------------------------------------------
# Rastgele yol üretme
# ---------------------------------------------
def random_path(source, target, G, max_hops=6):
    for _ in range(30):  # 30 deneme hakkı
        path = [source]
        current = source

        for _ in range(max_hops):
            neighbors = list(G.neighbors(current))
            next_node = random.choice(neighbors)
            path.append(next_node)

            current = next_node

            if current == target:
                return path

    return None


# ---------------------------------------------
# Popülasyon oluşturma
# ---------------------------------------------
def create_population(size, source, target, G):
    population = []

    while len(population) < size:
        p = random_path(source, target, G)

        if p is not None and is_valid_path(p, G):
            population.append(p)

    return population


# ---------------------------------------------
# Fitness
# ---------------------------------------------
def fitness(path, G):
    if path is None:
        return 0

    cost = weighted_sum_method(path, G)
    return 1 / (1 + cost)


# ---------------------------------------------
# Tournament Selection
# ---------------------------------------------
def tournament_selection(population, G, k=3):
    candidates = random.sample(population, k)
    return max(candidates, key=lambda p: fitness(p, G))


# ---------------------------------------------
# Crossover
# ---------------------------------------------
def crossover(p1, p2, G):
    common = set(p1[1:-1]).intersection(p2[1:-1])

    if not common:
        return random.choice([p1, p2])

    c = random.choice(list(common))

    i = p1.index(c)
    j = p2.index(c)

    return p1[:i] + p2[j:]


# ---------------------------------------------
# Mutasyon
# ---------------------------------------------
def mutate(path, G, rate=0.2):
    if random.random() > rate:
        return path

    idx = random.randint(1, len(path)-2)

    neighbors = list(G.neighbors(path[idx]))
    if not neighbors:
        return path

    new_node = random.choice(neighbors)

    new_path = path.copy()
    new_path[idx] = new_node

    return new_path


# ---------------------------------------------
# GENETİK ALGORİTMA
# ---------------------------------------------
def genetic_algorithm(source, target, G,
                      pop_size=40,
                      generations=100,
                      mutation_rate=0.2):

    population = create_population(pop_size, source, target, G)

    best_path = None
    best_fit = 0

    for gen in range(generations):

        new_pop = []

        for _ in range(pop_size):
            p1 = tournament_selection(population, G)
            p2 = tournament_selection(population, G)

            child = crossover(p1, p2, G)
            child = mutate(child, G, mutation_rate)

            if is_valid_path(child, G):
                new_pop.append(child)

        population = new_pop

        # En iyi sonucu güncelle
        for path in population:
            f = fitness(path, G)
            if f > best_fit:
                best_fit = f
                best_path = path

        print(f"Generation {gen+1}: Best fitness = {best_fit}")

    return best_path, best_fit


# ---------------------------------------------
# PROGRAMI BURADA ÇALIŞTIRIYORUZ
# ---------------------------------------------
if __name__ == "__main__":

    source = 8
    target = 44

    best_path, best_fit = genetic_algorithm(source, target, G)

    print("\n=== SONUÇLAR ===")
    print("En iyi yol:", best_path)
    print("Fitness:", best_fit)
    print("Toplam delay:", total_delay(best_path, G))
    print("Toplam güvenilirlik:", total_reliability(best_path, G))
    print("Toplam cost:", weighted_sum_method(best_path, G))

#-----------------------------------------------
#ARAYÜZCÜNÜN KULLANACAĞI FONKSİYON
#-----------------------------------------------
def run_ga(source, target,
           pop_size=40,
           generations=100,
           mutation_rate=0.2):

    best_path, best_fit = genetic_algorithm(
        source, 
        target, 
        G,
        pop_size,
        generations,
        mutation_rate
    )

    delay = total_delay(best_path, G)
    reliability = total_reliability(best_path, G)
    cost = weighted_sum_method(best_path, G)

    return {
        "best_path": best_path,
        "fitness": best_fit,
        "delay": delay,
        "reliability": reliability,
        "cost": cost
    }
#------------------------------------------------
#ÖRNEK KISMI
#------------------------------------------------
if __name__ == "__main__":
    result = run_ga(8, 44)

    print("En iyi yol:", result["best_path"])
    print("Delay:", result["delay"])
    print("Güvenilirlik:", result["reliability"])
    print("Cost:", result["cost"])
