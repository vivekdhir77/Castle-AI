import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import json

CARD_TYPE_IN_HAND = "In Hand"
CARD_TYPE_FACE_UP = "Face Up"
CARD_TYPE_FACE_DOWN = "Face Down"
CARD_TYPE_PILE = "Pile"

RANK_ORDER = {
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    '10': 10,
    'Jack': 11,
    'Queen': 12,
    'King': 13,
    'Ace': 14,
    'Joker': 15
}

def get_playable_cards(player_cards, seven_rule_active=False):
    in_hand = [card for card in player_cards if card['type'] == CARD_TYPE_IN_HAND]
    if in_hand:
        return in_hand, CARD_TYPE_IN_HAND

    face_up = [card for card in player_cards if card['type'] == CARD_TYPE_FACE_UP]
    if face_up:
        return face_up, CARD_TYPE_FACE_UP

    face_down = [card for card in player_cards if card['type'] == CARD_TYPE_FACE_DOWN]
    return face_down, CARD_TYPE_FACE_DOWN

def is_valid_play(card_rank, pile, seven_rule_active=False, joker_allowed=True):
    if not pile:
        return True

    top_card = pile[-1]
    top_rank = top_card['rank']
    
    if card_rank == 'Joker' and joker_allowed:
        return True

    if seven_rule_active and RANK_ORDER[card_rank] > 7:
        return False

    return (RANK_ORDER[card_rank] >= RANK_ORDER[top_rank] or 
            card_rank in ['2', '7', '10'])

def handle_special_card(rank, pile):
    if rank == '10':
        pile.clear()
        print("Pile burned!")
        return True
    elif rank == '2':
        print("2 played! Pile reset.")
        return True
    elif rank == '7':
        print("Seven played! Next card must be 7 or lower.")
        return False
    elif rank == 'Joker':
        print("Joker played! Acts as a wild card.")
        return False
    return False

def distribute(players, num_face_down, num_face_up, num_in_hand, deck):
    if players * (num_face_down + num_face_up + num_in_hand) > len(deck):
        raise ValueError("Not enough cards to distribute")

    random.shuffle(deck)
    distribution = {}
    for i in range(players):
        player_key = f"Player {i + 1}"
        distribution[player_key] = deck[i * (num_face_down + num_face_up + num_in_hand):
                                        (i + 1) * (num_face_down + num_face_up + num_in_hand)]
        for idx, card in enumerate(distribution[player_key]):
            if idx < num_face_down:
                card["type"] = CARD_TYPE_FACE_DOWN
            elif idx < num_face_down + num_face_up:
                card["type"] = CARD_TYPE_FACE_UP
            else:
                card["type"] = CARD_TYPE_IN_HAND
    remaining_deck = deck[players * (num_face_down + num_face_up + num_in_hand):]
    return distribution, remaining_deck

def pick_up_pile(pile, player_cards):
    for card in pile:
        card["type"] = CARD_TYPE_IN_HAND
    player_cards.extend(pile)
    return [], player_cards

def pprint_distributed_cards(distributed_cards):
    for player, cards in distributed_cards.items():
        print(f"\n{player}\n" + "-" * 10)
        for card in cards:
            if card['type'] != CARD_TYPE_FACE_DOWN:
                print(f"{card['suit']} {card['rank']} {card['type']}")
        print("*" * 15)

class CardGameEnv:
    def __init__(self, distributed_cards, deck, pile):
        self.distributed_cards = distributed_cards
        self.deck = deck
        self.pile = pile
        self.current_player = 1
        self.game_over = False
        self.seven_rule_active = False
        self.max_hand_size = 3

    def get_state(self):
        player1 = self.distributed_cards["Player 1"]
        player2 = self.distributed_cards["Player 2"]

        def encode_cards(cards, count=3):
            encoded = []
            for card in cards:
                rank = card['rank']
                rank_value = RANK_ORDER.get(rank, 0)
                if rank_value == 0:
                    print(f"Warning: Undefined rank '{rank}' encountered.")
                encoded.append(rank_value)
                if len(encoded) >= count:
                    break
            encoded += [0] * (count - len(encoded))
            return encoded

        player1_hand = encode_cards(
            [card for card in player1 if card['type'] == CARD_TYPE_IN_HAND], self.max_hand_size)
        player1_face_up = encode_cards(
            [card for card in player1 if card['type'] == CARD_TYPE_FACE_UP], self.max_hand_size)

        player2_hand = encode_cards(
            [card for card in player2 if card['type'] == CARD_TYPE_IN_HAND], self.max_hand_size)
        player2_face_up = encode_cards(
            [card for card in player2 if card['type'] == CARD_TYPE_FACE_UP], self.max_hand_size)

        pile_top = RANK_ORDER[self.pile[-1]['rank']] if self.pile else 0

        state = np.array(player1_hand + player1_face_up +
                        player2_hand + player2_face_up + [pile_top])

        print(f"State: {state}, Size: {len(state)}")
        return state

    def step(self, action):
        player_key = f"Player {self.current_player}"
        player_cards = self.distributed_cards[player_key]
        playable_cards, card_type = get_playable_cards(player_cards, self.seven_rule_active)

        if not playable_cards:
            print(f"{player_key} cannot play and picks up the pile.")
            self.pile, player_cards = pick_up_pile(self.pile, player_cards)
            self.distributed_cards[player_key] = player_cards
            self.switch_player()
            return self.get_state(), -10, False

        if action >= len(playable_cards):
            print(f"Invalid action by {player_key}: {action}")
            return self.get_state(), -10, True

        chosen_card = playable_cards[action]
        valid = is_valid_play(
            chosen_card['rank'], self.pile, self.seven_rule_active)

        if not valid:
            print(f"{player_key} played an invalid card and picks up the pile.")
            self.pile, player_cards = pick_up_pile(self.pile, player_cards)
            self.distributed_cards[player_key] = player_cards
            self.switch_player()
            return self.get_state(), -5, False

        self.play_card(player_key, chosen_card)

        if len(player_cards) == 0 and not any(card['type'] in [CARD_TYPE_FACE_UP, CARD_TYPE_FACE_DOWN] for card in player_cards):
            reward = 10
            self.game_over = True
            return self.get_state(), reward, self.game_over
        else:
            reward = 1

        return self.get_state(), reward, self.game_over

    def play_card(self, player_key, card):
        print(f"{player_key} plays {card['rank']} on top of the pile.")
        self.distributed_cards[player_key].remove(card)
        self.pile.append({"suit": card['suit'], "rank": card['rank'], "type": CARD_TYPE_PILE})

        print(f"Top of the pile is now: {card['rank']}")

        play_again = handle_special_card(card['rank'], self.pile)

        if card['rank'] == '7':
            self.seven_rule_active = True
        elif card['rank'] in ['2', '10']:
            self.seven_rule_active = False
        elif card['rank'] == 'Joker':
            self.seven_rule_active = False
        else:
            self.seven_rule_active = False

        if play_again:
            print(f"{player_key} gets another turn.")
        else:
            self.switch_player()

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def reset(self):
        try:
            with open("cards.json", "r") as file:
                deck = json.load(file)
        except FileNotFoundError:
            print("Error: 'cards.json' file not found.")
            exit(1)

        players = 2
        num_face_down = 3
        num_face_up = 3
        num_in_hand = 3
        self.distributed_cards, self.deck = distribute(players, num_face_down, num_face_up, num_in_hand, deck)
        self.pile = []
        self.current_player = random.choice([1, 2])
        self.game_over = False
        self.seven_rule_active = False

        return self.get_state()

class DQNAgent:
    def __init__(self, state_size, action_size, lr=0.001, gamma=0.99,
                 epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.lr = lr

        self.memory = deque(maxlen=2000)
        self.model = self.build_model()

    def build_model(self):
        model = nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        ).to('cpu')
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            act_values = self.model(state_tensor)
        return torch.argmax(act_values).item()

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        for state, action, reward, next_state, done in minibatch:
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            next_state_tensor = torch.tensor(next_state, dtype=torch.float32).unsqueeze(0)

            target_values = self.model(state_tensor)
            target = target_values.clone().detach()

            if done:
                target[0][action] = reward
            else:
                with torch.no_grad():
                    target[0][action] = reward + self.gamma * torch.max(self.model(next_state_tensor))

            outputs = self.model(state_tensor)
            loss = criterion(outputs, target)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

if __name__ == "__main__":
    distributed_cards = {"Player 1": [], "Player 2": []}
    deck = []
    pile = []

    env = CardGameEnv(distributed_cards, deck, pile)
    state = env.reset()
    state_size = len(state)
    action_size = 15

    agent1 = DQNAgent(state_size, action_size)
    agent2 = DQNAgent(state_size, action_size)

    episodes = 1000
    batch_size = 32

    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            current_agent = agent1 if env.current_player == 1 else agent2
            action = current_agent.act(state)

            player_key = f"Player {env.current_player}"
            player_cards = env.distributed_cards[player_key]
            playable_cards, _ = get_playable_cards(player_cards, env.seven_rule_active)

            if action >= len(playable_cards):
                next_state, reward, done = env.step(action)
            else:
                next_state, reward, done = env.step(action)

            current_agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            if done:
                print(f"Episode {e+1}/{episodes} finished with total reward: {total_reward}")
                break

        agent1.replay(batch_size)
        agent2.replay(batch_size)

    print("\n=== Testing: Agents Playing Against Each Other ===\n")

    agent1.epsilon = agent1.epsilon_min
    agent2.epsilon = agent2.epsilon_min

    state = env.reset()
    done = False

    while not done:
        current_agent = agent1 if env.current_player == 1 else agent2
        action = current_agent.act(state)

        player_key = f"Player {env.current_player}"
        player_cards = env.distributed_cards[player_key]
        playable_cards, _ = get_playable_cards(player_cards, env.seven_rule_active)

        if action >= len(playable_cards):
            next_state, reward, done = env.step(action)
        else:
            next_state, reward, done = env.step(action)

        state = next_state

        if done:
            winner = "Player 1" if env.current_player == 1 else "Player 2"
            print(f"Game Over! {winner} wins!")
            pprint_distributed_cards(env.distributed_cards)
            break
