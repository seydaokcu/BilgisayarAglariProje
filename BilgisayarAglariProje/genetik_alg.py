import random
from Ag_olusturma import (
    G,
    is_valid_path,
    total_delay,
    total_reliability,
    weighted_sum_method
)

# ------------------------------------------------
# Yolun darboğaz (minimum) bandwidth'ini hesaplar
# ------------------------------------------------
def path_min_bandwidth(path, G):
    if path is None or len(path) < 2:
        return 0.0
    m = float("inf")
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        m = min(m, G.edges[u, v].get("bandwidth", 0.0))
    return m


# ---------------------------------------------
# Rastgele yol üretme
# (Basit random walk; hedefe ulaşırsa döner)
# ---------------------------------------------
def random_path(source, target, G, max_hops=6):
    for _ in range(30):  # 30 deneme hakkı
        path = [source]
        current = source

        for _ in range(max_hops):
            neighbors = list(G.neighbors(current))
            if not neighbors:
                break

            next_node = random.choice(neighbors)
            path.append(next_node)
            current = next_node

            if current == target:
                return path

    return None


# ---------------------------------------------
# Popülasyon oluşturma (bandwidth kısıtı dahil)
# ---------------------------------------------
def create_population(size, source, target, G, demand_bw, max_hops=6):
    population = []
    tries = 0
    max_tries = size * 200  # güvenlik: sonsuz döngü olmasın

    while len(population) < size and tries < max_tries:
        tries += 1
        p = random_path(source, target, G, max_hops=max_hops)

        if p is not None and is_valid_path(p, G, min_bandwidth=demand_bw):
            population.append(p)

    return population


# ---------------------------------------------
# Fitness (bandwidth kısıtı dahil)
# ---------------------------------------------
def fitness(path, G, demand_bw):
    if path is None:
        return 0

    if not is_valid_path(path, G, min_bandwidth=demand_bw):
        return 0

    cost = weighted_sum_method(path, G)
    return 1 / (1 + cost)


# ---------------------------------------------
# Tournament Selection
# ---------------------------------------------
def tournament_selection(population, G, demand_bw, k=3):
    k = min(k, len(population))
    candidates = random.sample(population, k)
    return max(candidates, key=lambda p: fitness(p, G, demand_bw))


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
# Mutasyon (GÜVENLİK KİLİDİ EKLENDİ)
# ---------------------------------------------
def mutate(path, G, rate=0.2):
    # Direkt yol [S, D] gibi ise mutasyon yapılmaz
    if path is None or len(path) <= 2:
        return path

    if random.random() > rate:
        return path

    idx = random.randint(1, len(path) - 2)

    neighbors = list(G.neighbors(path[idx]))
    if not neighbors:
        return path

    new_node = random.choice(neighbors)
    new_path = path.copy()
    new_path[idx] = new_node

    return new_path


# ---------------------------------------------
# GENETİK ALGORİTMA (demand_bw eklendi)
# ---------------------------------------------
def genetic_algorithm(source, target, G, demand_bw,
                      pop_size=40,
                      generations=100,
                      mutation_rate=0.2,
                      max_hops=6):

    population = create_population(pop_size, source, target, G, demand_bw, max_hops=max_hops)

    # Hiç uygun yol üretilmediyse
    if not population:
        return None, 0

    best_path = None
    best_fit = 0

    for gen in range(generations):
        new_pop = []
        tries = 0
        max_tries = pop_size * 200  # güvenlik

        while len(new_pop) < pop_size and tries < max_tries:
            tries += 1

            p1 = tournament_selection(population, G, demand_bw)
            p2 = tournament_selection(population, G, demand_bw)

            child = crossover(p1, p2, G)
            child = mutate(child, G, mutation_rate)

            if is_valid_path(child, G, min_bandwidth=demand_bw):
                new_pop.append(child)

        if not new_pop:
            new_pop = population.copy()

        population = new_pop

        for path in population:
            f = fitness(path, G, demand_bw)
            if f > best_fit:
                best_fit = f
                best_path = path

        print(f"Generation {gen + 1}: Best fitness = {best_fit}")

    return best_path, best_fit


# ---------------------------------------------
# ARAYÜZCÜNÜN KULLANACAĞI FONKSİYON
# ---------------------------------------------
def run_ga(source, target, demand_bw,
           pop_size=40,
           generations=100,
           mutation_rate=0.2,
           max_hops=6):

    best_path, best_fit = genetic_algorithm(
        source,
        target,
        G,
        demand_bw,
        pop_size,
        generations,
        mutation_rate,
        max_hops
    )

    if best_path is None:
        return {
            "best_path": None,
            "fitness": 0,
            "error": f"Uygun bandwidth sağlayan yol bulunamadı (demand={demand_bw} Mbps)."
        }

    delay = total_delay(best_path, G)
    reliability = total_reliability(best_path, G)
    cost = weighted_sum_method(best_path, G)
    min_bw = path_min_bandwidth(best_path, G)

    return {
        "best_path": best_path,
        "fitness": best_fit,
        "delay": delay,
        "reliability": reliability,
        "cost": cost,
        "min_bw": min_bw
    }


# ---------------------------------------------
# ÖRNEK ÇALIŞTIRMA
# ---------------------------------------------
if __name__ == "__main__":
    source = 8
    target = 44
    demand_bw = 800  # kullanıcı talebi (Mbps)

    result = run_ga(source, target, demand_bw)

    print("\n=== SONUÇLAR ===")
    if result.get("best_path") is None:
        print("HATA:", result.get("error"))
        print("Demand:", demand_bw)
    else:
        print("En iyi yol:", result["best_path"])
        print("Fitness:", result["fitness"])
        print("Toplam delay:", result["delay"])
        print("Toplam güvenilirlik:", result["reliability"])
        print("Toplam cost:", result["cost"])
        print("Yol min bandwidth (bottleneck):", result["min_bw"])

        # ✅ Net kontrol (hatasız)
        print("Demand:", demand_bw)
        print("Min BW:", result["min_bw"])
        print("Kısıt sağlandı mı?:", result["min_bw"] >= demand_bw)
