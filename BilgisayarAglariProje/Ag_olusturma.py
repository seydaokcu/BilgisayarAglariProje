import pandas as pd
import networkx as nx

# -----------------------------
# 1) NODE DOSYASI
# -----------------------------

node_df=pd.read_csv(
    "BSM307_317_Guz2025_TermProject_NodeData.csv",
    sep=";", #Dosyada ayraç olarak noktalı virgül kullanıldığını söylüyoruz.
    encoding="utf-8-sig"
 )

node_df["s_ms"]=node_df["s_ms"].str.replace(",",".").astype(float) #Tüm virgülleri noktaya çevir → 0.95 çünkü virgül olursa bilgisayar bunu sayı olarak anlayamaz
node_df["r_node"]=node_df["r_node"].str.replace(",",".").astype(float)


# -----------------------------
# 2) EDGE DOSYASI
# -----------------------------
edge_df=pd.read_csv(
    "BSM307_317_Guz2025_TermProject_EdgeData.csv",
    sep=";",
    encoding="utf-8-sig"
)

edge_df["capacity_mbps"]=edge_df["capacity_mbps"].astype(float)  #pyhton bunları string olarak algılar bu yüzden sayıya çevirerek veriyi kullanıabilir hale getiriyoruz 
edge_df["delay_ms"]=edge_df["delay_ms"].astype(float)
edge_df["r_link"]=edge_df["r_link"].str.replace(",",".").astype(float)

# -----------------------------
# 3) DEMAND DOSYASI (Kim, kime ve ne kadar veri göndermek istiyor?)
# -----------------------------

demand_df=pd.read_csv(
    "BSM307_317_Guz2025_TermProject_DemandData.csv",
    sep=";",
    encoding="utf-8-sig"
)

demand_df["demand_mbps"]=demand_df["demand_mbps"].astype(float)
#demand_mbps: Bu değer bir S → D çifti için gönderilmek istenen trafik miktarıdır. 
#demand_mbps = yolun kapasite yönünden uygun olup olmadığını anlamak için gerekli




# -----------------------------
# 4) GRAF OLUŞTURMA
# -----------------------------

G=nx.Graph()

# --- düğümler ---

for _, row in node_df.iterrows():  #iterrows : Tabloyu satır satır dolaş
                                  # for _, : İlk değeri (index) alıyorum ama kullanmıyorum, çöpe atıyorum
    n = int(row["node_id"])
    G.add_node(n)
    G.nodes[n]["processing_delay"]=row["s_ms"]
    G.nodes[n]["node_reliability"]=row["r_node"]

# --- kenarlar ---
for _, row in edge_df.iterrows():
    u=int(row["src"]) #src = edge’in başladığı düğüm (source)
    v=int(row["dst"]) #dst = edge’in bittiği düğüm (destination)

    G.add_edge(u,v)
    G.edges[u,v]["bandwidth"]=row["capacity_mbps"]
    G.edges[u,v]["link_delay"]=row["delay_ms"]
    G.edges[u,v]["link_reliability"]=row["r_link"]

print("Graf başarıyla oluşturuldu.")
print("Toplam Düğüm:",len(G.nodes()))
print("Toplam Kenar:",len(G.edges()))

print("Örnek demand verisi:")
print(demand_df.head())


import math
def total_delay(path, G):
    """
    TotalDelay(P) = 
        (Yol üzerindeki tüm kenarların link_delay toplamı)
      + (Kaynak ve hedef hariç ara düğümlerin processing_delay toplamı)

    Varsayım:
    - path, daha önce is_valid_path(...) ile doğrulanmıştır
    - Graf yönsüzdür (nx.Graph)
    """

    # Geçersiz veya çok kısa yol kontrolü
    if path is None or len(path) < 2:
        return 0.0

    total_delay_value = 0.0

    # 1) Kenar (link) gecikmelerini topla
    # path = [n0, n1, n2, n3] ise:
    # (n0,n1), (n1,n2), (n2,n3) kenarları gezilir
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        link_delay = float(G.edges[u, v]["link_delay"])
        total_delay_value += link_delay

    # 2) Ara düğümlerin işlem gecikmelerini topla (S ve D hariç)
    # path[1:-1] → sadece ara düğümler
    for i in range(1, len(path) - 1):
        node = path[i]

        processing_delay = float(G.nodes[node]["processing_delay"])
        total_delay_value += processing_delay

    return total_delay_value


def reliability_cost(path, G):
    total_cost = 0.0
    
    # Edge reliability
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        r = G.edges[u, v]["link_reliability"]
        total_cost += -math.log(r) 
# -log(R) → “güvenilmezlik maliyeti” gibi davranır ama aslında güvenilirliği maksimize etmek için kullanılan maliyettir.
#Log kullanılır çünkü güvenilirlik çarpılarak hesaplandığı için,log sayesinde bu çarpım toplama dönüşür
#    -optimizasyon algoritmaları bu toplamsal maliyeti kolayca minimize edebilir.

    # Node reliability
    for node in path:
        r = G.nodes[node]["node_reliability"]
        total_cost += -math.log(r)

    return total_cost



def resource_cost(path, G):
    total_cost = 0.0
    
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        bw = G.edges[u, v]["bandwidth"]
        total_cost += 1000 / bw  # normalize için

    return total_cost

    # -----------------------------------------------------------
# Toplam güvenilirlik (0–1 arasında): Path'in gerçekleşme olasılığı
# -----------------------------------------------------------
def total_reliability(path, G):

    reliability = 1.0

    # Kenar (link) güvenilirlikleri çarpılır
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        if not G.has_edge(u, v):
            return 0.0  # Kenar yoksa yol imkansızdır

        r_link = G.edges[u, v].get("link_reliability", 1.0)
        reliability *= r_link

    # Düğüm güvenilirlikleri çarpılır
    for node in path:
        r_node = G.nodes[node].get("node_reliability", 1.0)
        reliability *= r_node

    return reliability


# -----------------------------------------------------------
# Yolun geçerli olup olmadığını kontrol eder
# - Tüm düğümler graf içinde olmalı
# - Tüm kenarlar mevcut olmalı
# - (opsiyonel) her kenarın bandwidth'i min_bandwidth'ten büyük olmalı
# -----------------------------------------------------------
def is_valid_path(path, G, min_bandwidth=None):

    # En az 2 düğüm olmalı
    if len(path) < 2:
        return False

    # Düğümler graf içinde mi?
    for node in path:
        if node not in G.nodes:
            return False

    # Kenarlar doğru mu?
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        if not G.has_edge(u, v):
            return False

        # Bandwidth kontrolü
        if min_bandwidth is not None:
            bw = G.edges[u, v].get("bandwidth", 0)
            if bw < min_bandwidth:
                return False

    return True


# -----------------------------------------------------------
# Kaynak ve hedef arasındaki tüm yolları bulur
# max_hops → maksimum kenar sayısı
# -----------------------------------------------------------
def find_all_paths(G, source, target, max_hops=10):

    if source not in G.nodes or target not in G.nodes:
        return []

    try:
        paths = list(nx.all_simple_paths(G, source=source, target=target, cutoff=max_hops))
    except nx.NetworkXNoPath:
        return []

    return paths



def weighted_sum_method(path, G, 
                        w_delay=0.33, 
                        w_reliability=0.33, 
                        w_resource=0.34):

    td = total_delay(path, G)
    rc = reliability_cost(path, G)
    rct = resource_cost(path, G)

    total = (w_delay * td +
             w_reliability * rc +
             w_resource * rct)

    return total



# -----------------------------------------------------------
# ÖRNEK TEST KODU — istediğin path'i buraya yaz
# -----------------------------------------------------------

example_path = [0, 2]   # Buraya istediğin path'i yazabilirsin

print("Test Edilen Yol:", example_path)
print("---------------------------------------")

# Yol geçerli mi?
valid = is_valid_path(example_path, G, min_bandwidth=0)  
print("Geçerli yol mu?:", valid)

if valid:
    print("Toplam Delay:", total_delay(example_path, G))
    print("Toplam Güvenilirlik (0-1):", total_reliability(example_path, G))
    print("Güvenilirlik Cost:", reliability_cost(example_path, G))
    print("Kaynak Cost:", resource_cost(example_path, G))
    print("Weighted Cost:", weighted_sum_method(example_path, G))
else:
    print("Bu yol grafik içinde mevcut değil.")

