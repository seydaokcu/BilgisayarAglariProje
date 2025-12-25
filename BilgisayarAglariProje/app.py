from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

import Ag_olusturma as ag

try:
    from QLearning_algorithm import QLearningAgent
    from ACO_algorithm import run_aco
    from genetik_alg import run_ga
except ImportError as e:
    print(f"Algoritma modülü yüklenemedi: {e}")

# --------------------------------------------------
# GRAF
# --------------------------------------------------
G_ORIGINAL = ag.G
app = Flask(__name__)

# --------------------------------------------------
# YARDIMCI FONKSİYONLAR
# --------------------------------------------------
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
    fig, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)

    nx.draw_networkx_nodes(G, pos, node_color="#2563eb", node_size=600, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white", ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#9ca3af", ax=ax)

    if path and len(path) > 1:
        edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(
            G, pos, edgelist=edges, edge_color="#facc15", width=4, ax=ax
        )

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
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

        # Grafiği filtrele (bandwidth >= min_bandwidth)
        G_filtered = filter_graph_by_bandwidth(G_ORIGINAL, min_bandwidth)

        if source not in G_filtered.nodes or target not in G_filtered.nodes:
            return jsonify({"error": "Kaynak veya hedef düğüm grafikte yok."}), 404

        final_path = None
        final_cost = None
        metrics = None

        # ---------------- ALGORİTMA SEÇİMİ ----------------
        if algorithm == "Q-Learning":
            agent = QLearningAgent(
                G_filtered,
                w_delay=w_delay,
                w_reliability=w_rel,
                w_resource=w_res
            )
            agent.train(source, target, episodes=800)
            final_path = agent.get_best_path(source, target)

        elif algorithm == "ACO":
            # run_aco global G kullanıyor, G parametresi gönderme
            final_path, final_cost, metrics = run_aco(
                source,
                target,
                w_delay=w_delay,
                w_rel=w_rel,
                w_res=w_res,
                n_ants=20,
                n_iter=15
            )

            if final_path is None:
                return jsonify({
                    "error": f"ACO algoritması uygun yol bulamadı: source={source}, target={target}"
                }), 400

        elif algorithm == "GA":
            result = run_ga(
                source,
                target,
                min_bandwidth,   # demand_bw
                pop_size=40,
                generations=100,
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

        # Grafik görseli base64 olarak çiz
        graph_img = draw_network_to_base64(G_filtered, final_path)

        return jsonify({
            "path": [str(n) for n in final_path],
            "delay": f"{delay:.2f}",
            "reliability": f"{reliability:.2f}",
            "total_cost": f"{cost:.4f}",
            "graph_image": graph_img
        })

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


# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
