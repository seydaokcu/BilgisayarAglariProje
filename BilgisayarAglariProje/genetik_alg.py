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


# ------------------------------------------------
# Ağırlıkları doğrula + (opsiyonel) normalize et
# ------------------------------------------------
def prepare_weights(w_delay, w_reliability, w_resource, normalize=True):
    try:
        w_delay = float(w_delay)
        w_reliability = float(w_reliability)
        w_resource = float(w_resource)
    except (TypeError, ValueError):
        raise ValueError("Ağırlıklar sayısal olmalıdır (w_delay, w_reliability, w_resource).")

    if w_delay < 0 or w_reliability < 0 or w_resource < 0:
        raise ValueError("Ağırlıklar negatif olamaz.")

    s = w_delay + w_reliability + w_resource
    if s == 0:
        raise ValueError("Ağırlıkların toplamı 0 olamaz. En az bir ağırlık > 0 olmalı.")

    if normalize:
        w_delay /= s
        w_reliability /= s
        w_resource /= s

    return w_delay, w_reliability, w_resource


# ------------------------------------------------
# Toplam maliyeti ağırlıklarla hesaplayan yardımcı fonksiyon
# (weighted_sum_method Ag_olusturma.py içinden geliyor)
# ------------------------------------------------
def cost_with_weights(path, G, w_delay, w_reliability, w_resource):
    return weighted_sum_method(
        path, G,
        w_delay=w_delay,
        w_reliability=w_reliability,
        w_resource=w_resource
    )


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
# Fitness (bandwidth kısıtı + kullanıcı ağırlıkları dahil)
# ---------------------------------------------
def fitness(path, G, demand_bw, w_delay, w_reliability, w_resource):
    if path is None:
        return 0

    if not is_valid_path(path, G, min_bandwidth=demand_bw):
        return 0

    cost = cost_with_weights(path, G, w_delay, w_reliability, w_resource)
    return 1 / (1 + cost)


# ---------------------------------------------
# Tournament Selection
# ---------------------------------------------
def tournament_selection(population, G, demand_bw, w_delay, w_reliability, w_resource, k=3):
    k = min(k, len(population))
    candidates = random.sample(population, k)
    return max(candidates, key=lambda p: fitness(p, G, demand_bw, w_delay, w_reliability, w_resource))


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
    # Direkt yol [S, D] gibi ise mutasyon yapıl reveals
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
# GENETİK ALGORİTMA (demand_bw + ağırlıklar eklendi)
# ---------------------------------------------
def genetic_algorithm(source, target, G, demand_bw,
                      w_delay, w_reliability, w_resource,
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

            p1 = tournament_selection(population, G, demand_bw, w_delay, w_reliability, w_resource)
            p2 = tournament_selection(population, G, demand_bw, w_delay, w_reliability, w_resource)

            child = crossover(p1, p2, G)
            child = mutate(child, G, mutation_rate)

            if is_valid_path(child, G, min_bandwidth=demand_bw):
                new_pop.append(child)

        if not new_pop:
            new_pop = population.copy()

        population = new_pop

        for path in population:
            f = fitness(path, G, demand_bw, w_delay, w_reliability, w_resource)
            if f > best_fit:
                best_fit = f
                best_path = path

        print(f"Generation {gen + 1}: Best fitness = {best_fit}")

    return best_path, best_fit


# ---------------------------------------------
# ARAYÜZCÜNÜN KULLANACAĞI FONKSİYON
# Kullanıcı ağırlıkları buradan verilir
# ---------------------------------------------
def run_ga(source, target, demand_bw,
           w_delay=0.33, w_reliability=0.33, w_resource=0.34,
           normalize_weights=True,
           pop_size=40,
           generations=100,
           mutation_rate=0.2,
           max_hops=6):

    # Demand doğrulama
    try:
        demand_bw = float(demand_bw)
    except (TypeError, ValueError):
        return {"best_path": None, "fitness": 0, "error": "Demand (Mbps) sayısal olmalıdır."}

    if demand_bw < 0:
        return {"best_path": None, "fitness": 0, "error": "Demand negatif olamaz."}

    # Ağırlıkları hazırla
    try:
        w_delay, w_reliability, w_resource = prepare_weights(
            w_delay, w_reliability, w_resource, normalize=normalize_weights
        )
    except ValueError as e:
        return {"best_path": None, "fitness": 0, "error": str(e)}

    # EDGE CASE: Kaynak ve hedef aynıysa GA çalıştırmadan döndür
    if source == target:
        return {
            "best_path": [source],
            "fitness": 1.0,
            "delay": 0.0,
            "reliability": 1.0,
            "cost": 0.0,
            "min_bw": float("inf"),
            "weights": {"w_delay": w_delay, "w_reliability": w_reliability, "w_resource": w_resource}
        }

    best_path, best_fit = genetic_algorithm(
        source,
        target,
        G,
        demand_bw,
        w_delay, w_reliability, w_resource,
        pop_size,
        generations,
        mutation_rate,
        max_hops
    )

    if best_path is None:
        return {
            "best_path": None,
            "fitness": 0,
            "error": f"Uygun bandwidth sağlayan yol bulunamadı (demand={demand_bw} Mbps).",
            "weights": {"w_delay": w_delay, "w_reliability": w_reliability, "w_resource": w_resource}
        }

    delay = total_delay(best_path, G)
    reliability = total_reliability(best_path, G)
    cost = cost_with_weights(best_path, G, w_delay, w_reliability, w_resource)
    min_bw = path_min_bandwidth(best_path, G)

    return {
        "best_path": best_path,
        "fitness": best_fit,
        "delay": delay,
        "reliability": reliability,
        "cost": cost,
        "min_bw": min_bw,
        "weights": {"w_delay": w_delay, "w_reliability": w_reliability, "w_resource": w_resource}
    }


# ---------------------------------------------
# ÖRNEK ÇALIŞTIRMA
# ---------------------------------------------
if __name__ == "__main__":
    source = 8
    target = 44
    demand_bw = 800  # kullanıcı talebi (Mbps)

    # Kullanıcı ağırlıkları (örnek)
    w_delay = 0.50
    w_reliability = 0.20
    w_resource = 0.30

    result = run_ga(
        source, target, demand_bw,
        w_delay=w_delay, w_reliability=w_reliability, w_resource=w_resource,
        normalize_weights=True
    )

    print("\n=== SONUÇLAR ===")
    if result.get("best_path") is None:
        print("HATA:", result.get("error"))
        print("Demand:", demand_bw)
        print("Weights:", result.get("weights"))
    else:
        print("En iyi yol:", result["best_path"])
        print("Fitness:", result["fitness"])
        print("Toplam delay:", result["delay"])
        print("Toplam güvenilirlik:", result["reliability"])
        print("Toplam cost:", result["cost"])
        print("Yol min bandwidth (bottleneck):", result["min_bw"])
        print("Weights:", result["weights"])

        #  Net kontrol
        print("Demand:", demand_bw)
        print("Min BW:", result["min_bw"])
        print("Kısıt sağlandı mı?:", result["min_bw"] >= demand_bw)
