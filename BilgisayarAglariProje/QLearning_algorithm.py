import numpy as np
import networkx as nx
import random 
import math

import Ag_olusturma as ag

class QLearningAgent:
    def __init__(self, graph, w_delay=0.33, w_reliability=0.33, w_resource=0.34,
                 learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, exploration_decay=0.995):
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

    def get_q_value(self, state, action):
        return self.q_table.get(state, {}).get(action, 0.0)

    def calculate_reward(self, u, v):
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
        
        return -total_cost

    def choose_action(self, state):
        neighbors = list(self.graph.neighbors(state))
        if not neighbors: return None

        if random.random() < self.exploration_rate:
            return random.choice(neighbors)
        else:
            q_values = {n: self.q_table[state][n] for n in neighbors}
            max_q = max(q_values.values())
            best_actions = [n for n, q in q_values.items() if q == max_q]
            return random.choice(best_actions)

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

    def train(self, start_node, goal_node, episodes=1000):
        print(f"Eğitim Başlıyor: {start_node} -> {goal_node}")
        
        for episode in range(episodes):
            state = start_node
            steps = 0
            
            while state != goal_node and steps < 100:
                action = self.choose_action(state)
                if action is None: break 
                
                reward = self.calculate_reward(state, action)
                
                if action == goal_node:
                    reward += 1000 

                self.update_q_value(state, action, reward, action)
                state = action
                steps += 1
            
            self.exploration_rate *= self.exploration_decay

    def get_best_path(self, start_node, goal_node):
        path = [start_node]
        curr = start_node
        while curr != goal_node:
            neighbors = list(self.graph.neighbors(curr))
            if not neighbors: break
            
            q_vals = {n: self.q_table[curr][n] for n in neighbors}
            best_action = max(q_vals, key=q_vals.get)
            
            if best_action in path:
                print("Döngü tespit edildi, duruluyor.")
                break
                
            path.append(best_action)
            curr = best_action
            
            if len(path) > 50: break 
            
        return path

if __name__ == "__main__":
    # 1. Ağ Oluştur
    my_graph = ag.G
    # 2. Ajanı Başlat
    agent = QLearningAgent(my_graph)
    # 3. Ajanı Eğit
    start = 0
    goal = 5
    agent.train(start_node=start, goal_node=goal, episodes=1000)
    # 4. En İyi Yolu Al
    path = agent.get_best_path(start, goal)
    print("-" * 30)
    print(f"Bulunan Yol: {path}")

    # 5. Toplam Gecikmeyi Hesapla
    if path:
        print(f"Toplam Gecikme: {ag.total_delay(path, my_graph):.2f}")