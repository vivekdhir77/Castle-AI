import json
import random

# Constants for card types
CARD_TYPE_IN_HAND = "In Hand"
CARD_TYPE_FACE_UP = "Face Up"
CARD_TYPE_FACE_DOWN = "Face Down"
CARD_TYPE_PILE = "Pile"

# Constants for card ranks
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
    'Ace': 14
}

def distribute(players, num_cards, deck):
    """
    Distributes cards evenly among players and returns the distribution and the remaining deck.
    Each player receives a specified number of cards.
    """
    if players * num_cards > len(deck):
        raise ValueError("Not enough cards to distribute")

    random.shuffle(deck)
    distribution = {
        f"Player {i + 1}": deck[i * num_cards:(i + 1) * num_cards] for i in range(players)
    }
    return distribution, deck[players * num_cards:]

def pprint(distributed_cards):
    """
    Pretty-prints the cards that are not face-down for each player.
    """
    for player, cards in distributed_cards.items():
        print(f"{player}\n" + "-" * 10)
        for card in cards:
            if card['type'] != CARD_TYPE_FACE_DOWN:
                print(f"{card['suit']} {card['rank']} {card['type']}")
        print("*" * 15)

def pprint_face_down(distributed_cards):
    """
    Pretty-prints the face-down cards for each player.
    """
    print("\n--FACE DOWN CARDS--")
    for player, cards in distributed_cards.items():
        print(f"{player}\n" + "-" * 10)
        for card in cards:
            if card['type'] == CARD_TYPE_FACE_DOWN:
                print(f"{card['suit']} {card['rank']}")
        print("*" * 15)

def pick_up_from_deck(deck, cards_in_hand):
    """
    Ensures the player has at least 3 cards in hand by picking up from the deck.
    """
    current_hand_count = sum(1 for card in cards_in_hand if card['type'] == CARD_TYPE_IN_HAND)
    pick_up_count = max(3 - current_hand_count, 0)

    for _ in range(pick_up_count):
        if not deck:
            break
        deck[0]["type"] = CARD_TYPE_IN_HAND
        cards_in_hand.append(deck.pop(0))  # Add to the end of the hand

    return deck, cards_in_hand

def pick_up_pile(pile, cards_in_hand):
    """
    Adds all cards from the pile to the player's hand.
    """
    for card in pile:
        card["type"] = CARD_TYPE_IN_HAND
    cards_in_hand.extend(pile)
    return [], cards_in_hand

def initialize_player_cards(distributed_cards):
    """
    Assigns types to the player's cards (In Hand, Face Up, Face Down).
    """
    for cards in distributed_cards.values():
        for i, card in enumerate(cards):
            if i < 3:
                card["type"] = CARD_TYPE_IN_HAND
            elif i < 6:
                card["type"] = CARD_TYPE_FACE_UP
            else:
                card["type"] = CARD_TYPE_FACE_DOWN

def play_turn(player, distributed_cards, deck, pile):
    """
    Manages a single turn for the given player.
    Handles playing cards based on their type and game rules.
    """
    # Show possible cards the player can play
    print(f"\n{player}'s possible cards to play:")
    in_hand_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_IN_HAND]
    
    # If no in-hand cards, face-up cards become playable
    if not in_hand_cards:
        face_up_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_FACE_UP]
        if face_up_cards:
            print("Playing with Face Up cards:")
            for card in face_up_cards:
                print(f"{card['suit']} {card['rank']}")
            possible_cards = face_up_cards
        else:
            # If no face-up cards either, play with face-down cards
            face_down_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_FACE_DOWN]
            if face_down_cards:
                print("Playing with Face Down cards:")
                random_card = random.choice(face_down_cards)
                
                # Check if the card can be played on the pile
                can_play = True
                if pile:
                    top_card = pile[-1]
                    if (RANK_ORDER[random_card['rank']] <= RANK_ORDER[top_card['rank']] and 
                        random_card['rank'] not in ['10', '7', '2']):
                        can_play = False
                
                # If can't play the card, add it to hand along with the pile
                if not can_play:
                    print(f"Face-down card {random_card['suit']} {random_card['rank']} cannot be played.")
                    print(f"Must pick up the pile and the card.")
                    distributed_cards[player].remove(random_card)  # Remove from face-down
                    random_card['type'] = CARD_TYPE_IN_HAND      # Change type to in hand
                    pile.append(random_card)                      # Add to pile before picking up
                    pile, distributed_cards[player] = pick_up_pile(pile, distributed_cards[player])
                else:
                    distributed_cards[player].remove(random_card)
                    pile.append({"suit": random_card['suit'], "rank": random_card['rank'], "type": CARD_TYPE_PILE})
                    print(f"{player} played face-down card: {random_card['suit']} {random_card['rank']}")
                
                # Handle special cards (10, 2)
                if can_play and random_card['rank'] == '10':
                    pile.clear()
                    print("Pile flushed!")
                
                pprint(distributed_cards)
                return
    else:
        for card in in_hand_cards:
            print(f"{card['suit']} {card['rank']}")
        possible_cards = in_hand_cards

    # Show the top card of the pile
    if pile:
        top_pile_card = pile[-1]
        print(f"Top card of the pile: {top_pile_card['suit']} {top_pile_card['rank']} length: {len(pile)}")
    else:
        print("The pile is empty.")

    # Add check for seven rule
    seven_rule_active = False
    if pile and pile[-1]['rank'] == '7':
        seven_rule_active = True
        print("Seven rule is active! Must play 7 or lower.")

    while True:  # Loop until a valid turn is played
        print(f"\n{player}'s turn:")
        print("Choose cards to play (suit and rank) or type 'pick up pile':")
        p_suit = input("Enter the suit you want to throw (or type 'pick up pile'): ").strip()

        if p_suit.lower() == 'pick up pile':
            if not pile:
                print("Cannot pick up pile because it's empty.")
                continue
            pile, distributed_cards[player] = pick_up_pile(pile, distributed_cards[player])
            print(f"{player} picked up the pile.")
            break

        p_rank = input("Enter the rank you want to throw: ").strip()

        # Find chosen cards based on current playable cards
        if not in_hand_cards:
            chosen_cards = [card for card in face_up_cards if card['rank'].lower() == p_rank.lower()]
        else:
            chosen_cards = [card for card in in_hand_cards if card['rank'].lower() == p_rank.lower()]

        if not chosen_cards:
            print("Invalid card choice. Please try again.")
            continue

        # Check if the card can be played on the pile
        if pile:
            top_card = pile[-1]
            # Add seven rule check
            if seven_rule_active and RANK_ORDER[p_rank.capitalize()] > 7:
                print("Invalid move: Must play a 7 or lower due to seven rule. Please try again.")
                continue
            elif (RANK_ORDER[p_rank.capitalize()] <= RANK_ORDER[top_card['rank']] and 
                  p_rank.capitalize() not in ['10', '7', '2']):
                print("Invalid move: You can only throw a higher rank card or a special card (10, 7, 2). Please try again.")
                continue

        # Remove chosen cards from player's hand and add to pile
        for card in chosen_cards:
            distributed_cards[player].remove(card)
            pile.append({"suit": card['suit'], "rank": card['rank'], "type": CARD_TYPE_PILE})
            print(f"{player} played: {card['suit']} {card['rank']}")

        # Special rule for '10': Flush the pile
        if p_rank.capitalize() == '10':
            pile.clear()
            print("Pile flushed! You can throw another card.")
            continue

        # Special rule for '2': Reset pile and allow another card
        if p_rank.capitalize() == '2':
            pile.clear()
            print("Pile reset with 2! You can throw another card.")
            continue

        # Special rule for '7': Set flag for next player
        if p_rank.capitalize() == '7':
            print("Seven played! Next player must play 7 or lower.")

        # If deck is not empty, draw cards
        if deck:
            deck, distributed_cards[player] = pick_up_from_deck(deck, distributed_cards[player])
        
        pprint(distributed_cards)
        break

    # Check for win condition
    remaining_cards = [card for card in distributed_cards[player]]
    if not remaining_cards:
        print(f"{player} has won the game!")
        return True

    return False

if __name__ == "__main__":
    try:
        with open("cards.json", "r") as file:
            deck = json.load(file)
        print("Deck loaded successfully.")
    except FileNotFoundError:
        print("Error: 'cards.json' file not found.")
        exit(1)

    # Game configuration
    players = 2  # Number of players
    num_cards = 9  # Number of cards per player

    try:
        distributed_cards, deck = distribute(players, num_cards, deck)
    except ValueError as e:
        print(e)
        exit(1)

    # Initialize card types
    initialize_player_cards(distributed_cards)

    # Print initial card distribution
    pprint(distributed_cards)
    pprint_face_down(distributed_cards)
    
    pile = []

    # Example gameplay actions
    game_over = False
    current_player = 1

    while not game_over:
        current_player_name = f"Player {current_player}"
        game_over = play_turn(current_player_name, distributed_cards, deck, pile)
        
        if not game_over:
            current_player = 2 if current_player == 1 else 1  # Switch players

    # # Main game loop placeholder
    # while True:
    #     # Logic for turns and game rules
    #     pass
