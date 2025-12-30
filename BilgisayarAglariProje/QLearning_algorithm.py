import numpy as np
import networkx as nx
import random 
import math
import time
from tqdm import tqdm

import Ag_olusturma as ag

class QLearningAgent:
    def __init__(self, graph, w_delay=0.33, w_reliability=0.33, w_resource=0.34,
                 learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, exploration_decay=0.9992):
        self.graph = graph
        self.q_table = {}
        
        # Metrik Ağırlıkları
        self.w_delay = w_delay
        self.w_reliability = w_reliability
        self.w_resource = w_resource

        # QLearning Parametreleri
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay

        # Q-Learning Tablosunu başlatma kısmı 
        for node in self.graph.nodes():
            self.q_table[node] = {}
            for neighbor in self.graph.neighbors(node):
                self.q_table[node][neighbor] = 0.0
    
    #================================
    # Q-değerini alma fonksiyonu
    #================================
    def get_q_value(self, state, action):
        return self.q_table.get(state, {}).get(action, 0.0)
    
    #================================
    # Heuristik fonksiyonu
    #================================
    def get_heuristic(self, u, v):
        edge_data = self.graph.edges[u, v]
        delay = edge_data.get('link_delay', 5)
        rel = edge_data.get('link_reliability', 0.99)
        bw = edge_data.get('bandwidth', 100)
        # Maliyetler (delay, rel, bw) üzerinden bir "kalite" puanı hesaplar
        cost_score = (self.w_delay * delay) + (self.w_reliability * (1-rel)*100) + (self.w_resource * (1000/bw))
        return 1.0 / (cost_score + 1e-6) # Düşük maliyet = Yüksek öncelik

    #================================
    # Ödül hesaplama fonksiyonu
    #================================
    def calculate_reward(self, u, v, is_goal, step_count):
        # Node ve Edge verileri çekme
        edge_data = self.graph.edges[u, v]
        node_data = self.graph.nodes[v]

        # 1. Gecikme (Link + Node Processing)
        delay = edge_data.get('link_delay', 5) + node_data.get('processing_delay', 1)
        
        # 2. Güvenilirlik Maliyeti (-log(Reliability))
        r_link = edge_data.get('link_reliability', 0.99)
        r_node = node_data.get('node_reliability', 0.99)
        val = r_link * r_node
        rel_cost = -math.log(val) if val > 0 else 100

        # 3. Kaynak Kullanımı (1000 / Bandwidth)
        bw = edge_data.get('bandwidth', 100) 
        res_cost = 1000 / bw if bw > 0 else 100

        # Toplam Maliyet
        total_cost = (self.w_delay * delay) + \
                     (self.w_reliability * rel_cost) + \
                     (self.w_resource * res_cost)
        
        reward = -total_cost

        reward -= step_count * 0.5

        if is_goal:
            reward += 200
        
        return reward

    #================================
    # Eylem seçimi (ε-greedy)
    #================================
    def choose_action(self, state):
        neighbors = list(self.graph.neighbors(state))
        if not neighbors: return None

        if random.random() < self.exploration_rate:
            h_values = [self.get_heuristic(state, n) for n in neighbors]
            
            # Koruma: Ağırlıklar toplamı 0 ise normal rastgele seç
            if sum(h_values) <= 0:
                return random.choice(neighbors)
                
            return random.choices(neighbors, weights=h_values, k=1)[0]
        else:
            q_values = {n: self.q_table[state][n] for n in neighbors}
            max_q = max(q_values.values())
            best_actions = [n for n, q in q_values.items() if q == max_q]
            return random.choice(best_actions)

    #================================
    # Q-değerini güncelleme
    #================================
    def update_q_value(self, state, action, reward, next_state):
        next_neighbors = list(self.graph.neighbors(next_state))
        if next_neighbors:
            best_next_q = max([self.q_table[next_state][n] for n in next_neighbors])
        else:
            best_next_q = 0.0

        current_q = self.q_table[state][action]
        
        # Bellman Denklemi
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * best_next_q - current_q)
        self.q_table[state][action] = new_q

    #================================
    # Eğitim fonksiyonu
    #================================
    def train(self, start_node, goal_node, episodes=1000):
        print(f"Eğitim Başlıyor: {start_node} -> {goal_node}")
        
        for episode in tqdm(range(episodes), desc="Eğitim İlerlemesi"):
            state = start_node
            steps = 0
            visited = {start_node}
            
            while state != goal_node and steps < 50:
                action = self.choose_action(state)

                if action is None or action in visited: 
                    if action: # Sadece action varsa ceza ver (KeyError önleme)
                        self.q_table[state][action] -= 10
                    break
                
                reward = self.calculate_reward(state, action, action == goal_node, steps)
                
                next_neighbors = list(self.graph.neighbors(action))
                max_next_q = max([self.q_table[action][n] for n in next_neighbors]) if next_neighbors else 0.0

                self.q_table[state][action] += self.learning_rate * \
                    (reward + self.discount_factor * max_next_q - self.q_table[state][action])

                visited.add(action)
                state = action
                steps += 1

            
            self.exploration_rate = max(0.01, self.exploration_rate * self.exploration_decay)

    #================================
    # En iyi yolu bulma
    #================================
    def get_best_path(self, start_node, goal_node):
        path = [start_node]
        curr = start_node
        while curr != goal_node:
            neighbors = list(self.graph.neighbors(curr))
            if not neighbors: return None # Değişiklik: Boş yol yerine None
            
            q_vals = {n: self.q_table[curr][n] for n in neighbors}
            # Eğer tüm Q değerleri 0 ise (hiç eğitim yapılamamışsa)
            if all(v == 0.0 for v in q_vals.values()):
                return None
            
            best_action = max(q_vals, key=q_vals.get)
            
            if best_action in path:
                print("Döngü tespit edildi, duruluyor.")
                break
                
            path.append(best_action)
            curr = best_action
            
            if len(path) > 50: break 
            
        return path if path[-1] == goal_node else None
#================================
# Q-Learn algoritmasını çalıştıran fonksiyon
#================================
def run_qlearn(source, target, episodes=1000):
    start_total_time = time.time()

    graph = ag.G
    agent = QLearningAgent(graph)
    t0 = time.time()
    agent.train(start_node=source, goal_node=target, episodes=episodes)
    t1 = time.time()
    train_time = round(t1 - t0, 3)
    best_path = agent.get_best_path(source, target)
    
    if best_path:
        delay = ag.total_delay(best_path, graph)
        reliability = ag.total_reliability(best_path, graph)
        resource_cost = ag.weighted_sum_method(best_path, graph)
    else:
        delay = float('inf')
        reliability = 0.0
        resource_cost = float('inf')

    end_total_time = time.time()
    total_execution_time = round(end_total_time - start_total_time, 3)
    
    return {
        "best_path": best_path,
        "delay": delay,
        "reliability": reliability,
        "resource_cost": resource_cost,
        "train_time": train_time,
        "total_execution_time": total_execution_time
    }

#------------------------------------------------
# ÖRNEK KISMI
#------------------------------------------------
if __name__ == "__main__":
    source = 0  
    target = 200

    result = run_qlearn(source, target, episodes=1000)

    print("En iyi yol:", result["best_path"])
    print("Delay:", result["delay"])
    print("Reliability:", result["reliability"])
    print("Resource Cost:", result["resource_cost"])
    print("Eğitim Süresi (s):", result["train_time"])
    print("Toplam Çalışma Süresi (s):", result["total_execution_time"])