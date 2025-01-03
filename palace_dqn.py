import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import json
import os

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
        self.max_action_size = 3  # Maximum number of cards that can be played at once

    def get_state(self):
        player1 = self.distributed_cards["Player 1"]
        player2 = self.distributed_cards["Player 2"]

        def encode_cards(cards):
            # Create a list of 15 zeros (one for each possible rank 2-15)
            rank_counts = [0] * 15  
            
            # Count occurrences of each rank
            for card in cards:
                rank = card['rank']
                rank_value = RANK_ORDER.get(rank, 0) - 1  # Subtract 1 to use 0-based indexing
                if rank_value >= 0:
                    rank_counts[rank_value] += 1
                    
            return rank_counts

        # Encode all cards by their type
        player1_hand = encode_cards([card for card in player1 if card['type'] == CARD_TYPE_IN_HAND])
        player1_face_up = encode_cards([card for card in player1 if card['type'] == CARD_TYPE_FACE_UP])
        player1_face_down = encode_cards([card for card in player1 if card['type'] == CARD_TYPE_FACE_DOWN])
        
        player2_hand = encode_cards([card for card in player2 if card['type'] == CARD_TYPE_IN_HAND])
        player2_face_up = encode_cards([card for card in player2 if card['type'] == CARD_TYPE_FACE_UP])
        player2_face_down = encode_cards([card for card in player2 if card['type'] == CARD_TYPE_FACE_DOWN])

        pile_top = RANK_ORDER[self.pile[-1]['rank']] if self.pile else 0

        # Combine all state components
        state = np.array(
            player1_hand + player1_face_up + player1_face_down +
            player2_hand + player2_face_up + player2_face_down + 
            [pile_top]
        )

        return state

    def step(self, action):
        player_key = f"Player {self.current_player}"
        player_cards = self.distributed_cards[player_key]
        playable_cards, card_type = get_playable_cards(player_cards, self.seven_rule_active)

        # Ensure action is within bounds of playable cards
        action = action % len(playable_cards) if playable_cards else 0

        if not playable_cards:
            print(f"{player_key} cannot play and picks up the pile.")
            self.pile, player_cards = pick_up_pile(self.pile, player_cards)
            self.distributed_cards[player_key] = player_cards
            self.switch_player()
            return self.get_state(), -10, False

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

        if len(self.distributed_cards[player_key]) == 0:
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

    def save_model(self, filename):
        torch.save(self.model.state_dict(), filename)

    def load_model(self, filename):
        if os.path.isfile(filename):
            self.model.load_state_dict(torch.load(filename))
            self.model.eval()
        else:
            print("Model file not found.")

if __name__ == "__main__":
    distributed_cards = {"Player 1": [], "Player 2": []}
    deck = []
    pile = []

    env = CardGameEnv(distributed_cards, deck, pile)
    state = env.reset()
    state_size = 91  # (15 ranks * 6 card types) + 1 pile top card
    action_size = 3  # Maximum number of cards that can be played at once

    agent1 = DQNAgent(state_size, action_size)
    agent2 = DQNAgent(state_size, action_size)

    # Load pre-trained model if available
    agent1.load_model("agent1_model.pth")
    agent2.load_model("agent2_model.pth")

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
    # exit()
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
            winner = "Player 2" if env.current_player == 1 else "Player 2"
            loser = "Player 1" if winner == "Player 1" else "Player 1"
            
            print(f"\nGame Over! {winner} wins!")
            print(f"\nReason: {winner} successfully played all their cards:")
            print(f"- No cards in hand")
            print(f"- No face-up cards")
            print(f"- No face-down cards")
            
            print(f"\n{loser}'s remaining cards:")
            loser_cards = env.distributed_cards[loser]
            hand_cards = [f"{c['rank']} of {c['suit']}" for c in loser_cards if c['type'] == CARD_TYPE_IN_HAND]
            face_up_cards = [f"{c['rank']} of {c['suit']}" for c in loser_cards if c['type'] == CARD_TYPE_FACE_UP]
            face_down_cards = [f"{c['rank']} of {c['suit']}" for c in loser_cards if c['type'] == CARD_TYPE_FACE_DOWN]
            
            if hand_cards:
                print("Hand cards:", ", ".join(hand_cards))
            if face_up_cards:
                print("Face-up cards:", ", ".join(face_up_cards))
            if face_down_cards:
                print("Face-down cards:", ", ".join(face_down_cards))
            
            print("\nFinal game state:")
            pprint_distributed_cards(env.distributed_cards)
            break

    # # Save the model after training
    agent1.save_model("agent1_model.pth")
    agent2.save_model("agent2_model.pth")

    # # Human vs AI gameplay
    # print("\n=== Human vs AI Game ===\n")
    # state = env.reset()
    # done = False

    # while not done:
    #     current_agent = agent1 if env.current_player == 1 else agent2
    #     if env.current_player == 1:  # Human player
    #         print("Your turn! Here are your playable cards:")
    #         player_key = f"Player {env.current_player}"
    #         player_cards = env.distributed_cards[player_key]
    #         playable_cards, _ = get_playable_cards(player_cards, env.seven_rule_active)
    #         for idx, card in enumerate(playable_cards):
    #             print(f"{idx}: {card['rank']} of {card['suit']}")

    #         action = int(input("Select the index of the card you want to play: "))
    #     else:  # AI player
    #         action = current_agent.act(state)

    #     next_state, reward, done = env.step(action)
    #     state = next_state

    #     if done:
    #         winner = "Player 1" if env.current_player == 1 else "Player 2"
    #         print(f"\nGame Over! {winner} wins!")
    #         break

    # Load pre-trained model for agent1
    agent1.load_model("agent1_model.pth")

    # Evaluate the model against a random player
    print("\n=== Evaluating AI against Random Player ===\n")
    num_games = 100
    agent1_wins = 0
    random_player_wins = 0

    for game in range(num_games):
        state = env.reset()
        done = False

        while not done:
            current_agent = agent1 if env.current_player == 1 else "Random Player"
            if current_agent == agent1:  # AI player
                action = agent1.act(state)
            else:  # Random player
                player_key = f"Player {env.current_player}"
                player_cards = env.distributed_cards[player_key]
                playable_cards, _ = get_playable_cards(player_cards, env.seven_rule_active)
                action = random.randrange(len(playable_cards)) if playable_cards else 0

            next_state, reward, done = env.step(action)
            state = next_state

        # Determine the winner
        winner = "Player 1" if env.current_player == 1 else "Random Player"
        if winner == "Player 1":
            agent1_wins += 1
        else:
            random_player_wins += 1

        print(f"Game {game + 1}/{num_games} finished. Winner: {winner}")

    print(f"\n=== Evaluation Results ===")
    print(f"AI Wins: {agent1_wins} out of {num_games}")
    print(f"Random Player Wins: {random_player_wins} out of {num_games}")
