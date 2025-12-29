import math
import random



# Import metric functions from your graph file
from Ag_olusturma import (
    G,                      # graph object created from CSVs
    total_delay,
    reliability_cost,
    resource_cost
)

# compute_edge_cost(G, u, v)
# ACO'nun bir sonraki kenarı seçebilmesi için tek bir kenarın
# yerel maliyetini hesaplar.
#
# Bu maliyet üç bileşenden oluşur:
#   - link_delay (gecikme)
#   - 1000 / bandwidth (kaynak maliyeti, düşük bant daha yüksek maliyet)
#   - -log(link_reliability) (güvenilirlik maliyeti)
#
# Bu fonksiyon sadece KENAR maliyetini hesaplar.
# Tüm yolun toplam maliyeti DEĞİLDİR.
# ACO'nun heuristic (sezgisel bilgi) hesabında kullanılır.

def compute_edge_cost(G, u, v, w_delay, w_rel, w_res):
    delay = G.edges[u, v]['link_delay']
    bw = G.edges[u, v]['bandwidth']
    rel = G.edges[u, v]['link_reliability']

    # Local cost based on user weights
    return (w_delay * delay) + (w_res * (1000 / bw)) + (w_rel * -math.log(rel))


# Graf üzerindeki tüm kenarlar için başlangıç feromon değerini oluşturur.
# Amaç: Algoritmanın ilk iterasyonunda tüm kenarların eşit olmasını sağlamak.
# Her kenara küçük pozitif bir başlangıç değeri verilir (örneğin 0.1).
# Bu, karınca seçim olasılıklarının hesaplanabilmesi için gereklidir.

def initialize_pheromones(G, initial=0.1):
    pheromone = {}
    for u, v in G.edges():
        pheromone[(u, v)] = initial
        pheromone[(v, u)] = initial  # For undirected graph
    return pheromone


# Karıncanın mevcut düğümdeyken hangi komşuya gideceğine karar verir.
# Seçim olasılığı şu formülle hesaplanır:
#   (pheromone[u][v]^alpha) * (heuristic[u][v]^beta)
# alpha = feromon etkisi, beta = sezgisel (maliyet metrikleri) bilginin etkisi.
# Ziyaret edilen düğümlere tekrar dönmemek için 'visited' listesi kontrol edilir.
# Bu fonksiyon ACO’nun çekirdeğidir: arama ve keşif burada gerçekleşir.

def choose_next_node(G, pheromone, current, visited, heuristic_map, alpha=1.0, beta=2.0):
    neighbors = list(G.neighbors(current))
    candidates = []

    for v in neighbors:
        if v in visited:
            continue  # Prevent cycles

        tau = pheromone[(current, v)]
        eta = heuristic_map[(current, v)]

        candidates.append((v, (tau ** alpha) * (eta ** beta)))

    if not candidates:
        return None

    nodes, weights = zip(*candidates)
    total_w = sum(weights)
    if total_w == 0:
        return random.choice(nodes)
        
    probs = [w / total_w for w in weights]
    return random.choices(nodes, probs)[0]


# Bir karıncanın start → end arasında oluşturduğu tek bir yolu üretir.
# choose_next_node() fonksiyonunu tekrar tekrar çağırarak ilerler.
# 'path' listesi – karıncanın gerçek izlediği düğüm sırasıdır.
# 'visited' seti – döngü oluşmasını engellemek için kullanılan kontrol listesi.
# Eğer karınca sıkışırsa (ilerleyebileceği düğüm kalmazsa) None döner.

def build_path(G, pheromone, S, D, heuristic_map, alpha=1.0,  beta=2.0):
    current = S
    visited = {S}
    path = [S]

    while current != D:
        next_node = choose_next_node(G, pheromone, current, visited, heuristic_map, alpha, beta)
        if next_node is None:
            return None  # dead end

        visited.add(next_node)
        path.append(next_node)
        current = next_node

    return path


# evaluate_path(G, path, w_delay, w_reliability, w_resource)
# Bir karıncanın ürettiği yolun toplam maliyetini hesaplar.
# Maliyet, üç farklı metrigin ağırlıklı toplamıdır:
#   - total_delay(path)
#   - reliability_cost(path)
#   - resource_cost(path)
# Hesaplanan bu tek değer, yolun "kalitesini" belirler.
# ACO algoritması bu maliyeti minimum yapan yolu bulmaya çalışır.

def evaluate_path(path, G, w_delay, w_rel, w_res):
    td = total_delay(path, G)
    rc = reliability_cost(path, G)
    rs = resource_cost(path, G)

    total = w_delay * td + w_rel * rc + w_res * rs
    return total, td, rc, rs


# Tüm kenarlardaki feromonu (1 - rho) oranında azaltır.
# Amaç: kötü veya kullanılmayan yolların feromonunun zamanla silinmesi.
# Bu işlem eski bilginin etkisini azaltır ve algoritmayı taze tutar.
# Bu sayede karıncalar daha iyi yolları zamanla daha çok tercih eder.

def evaporate_pheromone(pheromone, rho=0.1):
    for edge in pheromone:
        pheromone[edge] *= (1 - rho)


# Bir karınca başarılı bir yol bulduğunda o yolun kenarlarına feromon ekler.
# Eklenen feromon miktarı: Q / cost
# cost düşükse (yani yol iyiyse) daha fazla feromon eklenir.
# Böylece kaliteli yollar zaman içinde daha çekici hale gelir.

def deposit_pheromone(pheromone, path, cost, Q=1.0):
    amount = Q / cost
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        pheromone[(u, v)] += amount
        pheromone[(v, u)] += amount


# ACO algoritmasının ana döngüsünü çalıştırır.
# Her iterasyonda:
#   1) Bir grup karınca yol üretir.
#   2) Her yolun maliyeti hesaplanır.
#   3) En iyi yol güncellenir.
#   4) Feromon bu yollara göre güncellenir (buharlaşma + birikim).
# Sonuç olarak en düşük maliyetli yol döndürülür.
# Arayüz (UI) sadece bu fonksiyonu çağırmalı.

def ACO(G, S, D,
        w_delay=0.33, w_rel=0.33, w_res=0.34,
        n_ants=20, n_iter=15,
        alpha=1.0, beta=3.0, rho=0.1):

    # Pre-calculate heuristic based on USER weights
    heuristic_map = {}
    for u, v in G.edges():
        edge_cost = compute_edge_cost(G, u, v, w_delay, w_rel, w_res)
        h_val = 1.0 / max(0.0001, edge_cost)
        heuristic_map[(u, v)] = h_val
        heuristic_map[(v, u)] = h_val

    pheromone = initialize_pheromones(G)
    best_path = None
    best_cost = float('inf')
    best_metrics = None

    for iteration in range(n_iter):
        for ant in range(n_ants):
            path = build_path(G, pheromone, S, D, heuristic_map, alpha, beta)
            if path is None:
                continue

            cost, td, rc, rs = evaluate_path(path, G, w_delay, w_rel, w_res)

            if cost < best_cost:
                best_cost = cost
                best_path = path
                best_metrics = (td, rc, rs)

            deposit_pheromone(pheromone, path, cost)

        # ELITISM: The best path found SO FAR deposits extra pheromones
        if best_path:
            deposit_pheromone(pheromone, best_path, best_cost, Q=2.0)

        evaporate_pheromone(pheromone, rho)

    return best_path, best_cost, best_metrics


# run_aco(S, D, w_delay, w_rel, w_res, n_ants, n_iter) parametreleri ve print ifadeleri ile
# ACO algoritmasını çalıştırır ve sonuçları ekrana yazdırır.


def run_aco(G_in, S, D,
            w_delay=0.33, w_rel=0.33, w_res=0.34,
            n_ants=20, n_iter=15):

    best_path, best_cost, metrics = ACO(
        G_in, S, D,
        w_delay=w_delay,
        w_rel=w_rel,
        w_res=w_res,
        n_ants=n_ants,
        n_iter=n_iter
    )

    print("\n=== FINAL BEST RESULT ===")
    print("Best path:", best_path)
    print("Best total cost:", best_cost)

    if metrics is not None:
        td, rc, rs = metrics
        print("Delay:", td)
        print("Reliability cost:", rc)
        print("Resource cost:", rs)

    return best_path, best_cost, metrics


# S ve D değerleri ile ACO algoritmasını çalıştırır.

if __name__ == "__main__":
    S = 47
    D = 177
    run_aco(S, D)
