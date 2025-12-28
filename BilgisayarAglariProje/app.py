from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend for stability
import matplotlib.pyplot as plt
import io
import base64
import threading
import Ag_olusturma as ag

try:
    from QLearning_algorithm import QLearningAgent
    from ACO_algorithm import run_aco
    from genetik_alg import run_ga
except ImportError as e:
    print(f"Algoritma modülü yüklenemedi: {e}")

plot_lock = threading.Lock()

# Basit In-Memory Cache (Source-Target-Alg-Params -> Result)
RESULT_CACHE = {}

# --------------------------------------------------
# GRAF VE YARDIMCI FONKSİYONLAR
# --------------------------------------------------
G_ORIGINAL = ag.G
app = Flask(__name__)

def safe_float(val, default):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def filter_graph_by_bandwidth(G, min_bandwidth):
    """ACO ve Q-Learning için bandwidth'i sağlamayan kenarları çıkarır"""
    Gf = G.copy()
    for u, v, data in list(Gf.edges(data=True)):
        if data.get("bandwidth", 0) < min_bandwidth:
            Gf.remove_edge(u, v)
    return Gf

def draw_network_to_base64(G, path=None):
    # Lock kullanarak thread hatasını önle
    with plot_lock:
        fig, ax = plt.subplots(figsize=(12, 10), dpi=100)
        ax.set_facecolor('#ffffff')
        
        # Daha düzenli bir layout için k spring_layout parametrelerini ayarla
        pos = nx.spring_layout(G, seed=42, k=0.15, iterations=50)

        # 1. TÜM KENARLAR (Arka Plan)
        nx.draw_networkx_edges(
            G, pos, 
            edge_color="#e2e8f0", 
            width=0.5, 
            alpha=0.5, 
            ax=ax, 
            arrows=False
        )

        # 2. TÜM DÜĞÜMLER (Arka Plan)
        nx.draw_networkx_nodes(
            G, pos, 
            node_color="#94a3b8", 
            node_size=150, 
            ax=ax, 
            alpha=0.8
        )

        if path and len(path) > 1:
            edges = list(zip(path[:-1], path[1:]))
            source_node = path[0]
            target_node = path[-1]
            path_nodes = set(path)

            # 3. YOL KENARLARI (Vurgulu)
            nx.draw_networkx_edges(
                G, pos, 
                edgelist=edges, 
                edge_color="#ef4444", # RED
                width=4.0,            # Thinner
                ax=ax, 
                arrows=True,
                arrowsize=20
            )

            # 4. YOL DÜĞÜMLERİ
            nx.draw_networkx_nodes(
                G, pos, 
                nodelist=list(path_nodes - {source_node, target_node}),
                node_color="#f59e0b", # Yellowish-Orangish (Amber)
                node_size=600, 
                ax=ax
            )

            # 5. KAYNAK VE HEDEF (Turuncu)
            nx.draw_networkx_nodes(G, pos, nodelist=[source_node], node_color="#f59e0b", node_size=1000, ax=ax)
            nx.draw_networkx_nodes(G, pos, nodelist=[target_node], node_color="#f59e0b", node_size=1000, ax=ax)
            
            # Etiketler (Sadece yol üzerindekiler için)
            labels = {n: str(n) for n in path}
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=12, font_weight="bold", font_color="white", ax=ax)

        plt.axis('off')
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

# --------------------------------------------------
# ROUTE HESAPLAMA
# --------------------------------------------------
@app.route("/calculate_route", methods=["POST"])
def calculate_route():
    try:
        data = request.get_json()

        algorithm = data.get("algorithm")
        source = int(data.get("source"))
        target = int(data.get("target"))

        min_bandwidth = safe_float(data.get("min_bandwidth"), 0)
        w_delay = safe_float(data.get("w_delay"), 0.33)
        w_rel = safe_float(data.get("w_rel"), 0.33)
        w_res = safe_float(data.get("w_res"), 0.34)

        # CACHE CHECK
        # Parametreleri anahtar yap (JSON string olarak basitçe)
        import json
        cache_key = json.dumps(data, sort_keys=True)
        if cache_key in RESULT_CACHE:
            print("CACHE HIT!")
            return jsonify(RESULT_CACHE[cache_key])

        print("CACHE MISS - Calculating...")

        # Grafiği filtrele (bandwidth >= min_bandwidth)
        G_filtered = filter_graph_by_bandwidth(G_ORIGINAL, min_bandwidth)

        if source not in G_filtered.nodes or target not in G_filtered.nodes:
            return jsonify({"error": "Kaynak veya hedef düğüm grafikte yok."}), 404

        final_path = None
        final_cost = None
        metrics = None

        # ---------------- ALGORİTMA SEÇİMİ (TUNED PARAMETERS) ----------------
        if algorithm == "Q-Learning":
            agent = QLearningAgent(
                G_filtered,
                w_delay=w_delay,
                w_reliability=w_rel,
                w_resource=w_res
            )
            # Epizot sayısı artırıldı (Kalite için 3000 -> 10000)
            agent.train(source, target, episodes=10000)
            final_path = agent.get_best_path(source, target)

        elif algorithm == "ACO":
            # Ants/Iter azaltıldı (Hız)
            final_path, final_cost, metrics = run_aco(
                G_filtered,
                source,
                target,
                w_delay=w_delay,
                w_rel=w_rel,
                w_res=w_res,
                n_ants=15,  # 20 -> 15
                n_iter=10   # 15 -> 10
            )

            if final_path is None:
                return jsonify({
                    "error": f"ACO algoritması uygun yol bulamadı: source={source}, target={target}"
                }), 400

        elif algorithm == "GA":
            # Pop/Gen azaltıldı (Hız)
            result = run_ga(
                source,
                target,
                min_bandwidth,
                pop_size=30,      # 40 -> 30
                generations=40,   # 100 -> 40
                mutation_rate=0.2,
                max_hops=6
            )
            final_path = result["best_path"]

            if final_path is None:
                return jsonify({"error": result.get("error", "GA algoritması uygun yol bulamadı.")}), 400

        else:
            return jsonify({"error": "Geçersiz algoritma seçimi"}), 400

        # ---------------- METRİKLER ----------------
        delay = ag.total_delay(final_path, G_filtered)
        reliability = ag.total_reliability(final_path, G_filtered) * 100
        cost = ag.weighted_sum_method(
            final_path, G_filtered,
            w_delay=w_delay,
            w_reliability=w_rel,
            w_resource=w_res
        )

        res_cost = ag.resource_cost(final_path, G_filtered)
        rel_cost = ag.reliability_cost(final_path, G_filtered)

        # Bottleneck & Usage
        bw_list = [G_filtered.edges[final_path[i], final_path[i+1]]["bandwidth"] for i in range(len(final_path)-1)]
        bottleneck = min(bw_list) if bw_list else 0
        max_bw = max(bw_list) if bw_list else 0
        
        usage = 0
        if bottleneck > 0:
            if min_bandwidth > 0:
                 usage = (min_bandwidth / bottleneck) * 100
            else:
                 # Fallback: Simulate 100 Mbps load if no demand specified (for better visibility)
                 usage = (100 / bottleneck) * 100 

        # Grafik görseli base64 olarak çiz
        graph_img = draw_network_to_base64(G_filtered, final_path)

        # SONUÇ
        response_data = {
            "path": [str(n) for n in final_path],
            "delay": f"{delay:.2f}",
            "reliability": f"{reliability:.2f}",
            "total_cost": f"{cost:.4f}",
            "resource_cost": f"{res_cost:.4f}",
            "reliability_cost": f"{rel_cost:.4f}",
            "usage": usage,
            "sim_results": {
                "total_segments": len(final_path) - 1,
                "path_length_hops": len(final_path) - 1,
                "bottleneck_capacity": bottleneck,
                "max_capacity": max_bw,
                "reliability_cost": rel_cost
            },
            "debug": f"Algorithm: {algorithm}, Cost: {cost:.4f}",
            "graph_image": graph_img
        }

        # Cache'e kaydet
        RESULT_CACHE[cache_key] = response_data

        return jsonify(response_data)

    except Exception as e:
        import traceback
        return jsonify({
            "error": "Sunucu hatası",
            "detail": traceback.format_exc()
        }), 500

# --------------------------------------------------
# ANA SAYFA
# --------------------------------------------------
@app.route("/")
def index():
    graph_img = draw_network_to_base64(G_ORIGINAL)
    return render_template("index.html", initial_graph=graph_img)

@app.route("/get_initial_graph")
def get_initial_graph():
    return jsonify({})

@app.route("/compare")
def compare():
    return render_template("compare.html")

@app.route("/api/compare_all", methods=["POST"])
def api_compare_all():
    try:
        data = request.get_json()
        source = int(data.get("source"))
        target = int(data.get("target"))
        min_bandwidth = safe_float(data.get("min_bandwidth"), 0)
        w_delay = safe_float(data.get("w_delay"), 0.33)
        w_rel = safe_float(data.get("w_rel"), 0.33)
        w_res = safe_float(data.get("w_res"), 0.34)

        G_filtered = filter_graph_by_bandwidth(G_ORIGINAL, min_bandwidth)
        
        results = []
        algorithms = ["Q-Learning", "ACO", "GA"]

        for alg in algorithms:
            final_path = None
            
            if alg == "Q-Learning":
                agent = QLearningAgent(G_filtered, w_delay=w_delay, w_reliability=w_rel, w_resource=w_res)
                agent.train(source, target, episodes=10000)
                final_path = agent.get_best_path(source, target)
            
            elif alg == "ACO":
                final_path, _, _ = run_aco(G_filtered, source, target, w_delay=w_delay, w_rel=w_rel, w_res=w_res, n_ants=15, n_iter=10)
            
            elif alg == "GA":
                ga_res = run_ga(source, target, min_bandwidth, pop_size=30, generations=40)
                final_path = ga_res["best_path"]

            if final_path:
                delay = ag.total_delay(final_path, G_filtered)
                reliability = ag.total_reliability(final_path, G_filtered) * 100
                cost = ag.weighted_sum_method(final_path, G_filtered, w_delay=w_delay, w_reliability=w_rel, w_resource=w_res)
                res_cost = ag.resource_cost(final_path, G_filtered)
                
                results.append({
                    "algorithm": alg,
                    "delay": round(delay, 2),
                    "reliability": round(reliability, 2),
                    "cost": round(cost, 4),
                    "resource_cost": round(res_cost, 4),
                    "path": [str(n) for n in final_path]
                })

        return jsonify({"results": results})

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "detail": traceback.format_exc()}), 500

# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
