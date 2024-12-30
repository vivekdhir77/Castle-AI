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
    # Show possible cards the player can play
    print(f"\n{player}'s possible cards to play:")
    possible_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_IN_HAND]
    for card in possible_cards:
        print(f"{card['suit']} {card['rank']}")

    # Show the top card of the deck
    if deck:
        top_deck_card = deck[0]
        print(f"Top card of the deck: {top_deck_card['suit']} {top_deck_card['rank']}")
    else:
        print("The deck is empty.")

    while True:  # Loop until a valid turn is played
        print(f"\n{player}'s turn:")
        print("Choose cards to play (suit and rank) or pick up the pile:")
        p_suit = input("Enter the suit you want to throw (or type 'pick up pile'): ")
        
        if p_suit.lower() == 'pick up pile':
            pile, distributed_cards[player] = pick_up_pile(pile, distributed_cards[player])
            print(f"{player} picked up the pile.")
            break  # End the turn after picking up the pile

        p_rank = input("Enter the rank you want to throw: ")

        # Find all cards of the chosen rank in hand
        chosen_cards = [card for card in distributed_cards[player] if card['rank'] == p_rank and card['type'] == CARD_TYPE_IN_HAND]

        if not chosen_cards:
            print("Invalid card type. Please try again.")
            continue  # try again

        # Check if the card can be played on the pile
        if pile:
            top_card = pile[-1]
            if (RANK_ORDER[p_rank] <= RANK_ORDER[top_card['rank']] and 
                p_rank not in ['10', '7', '2']):
                print("Invalid move: You can only throw a higher rank card or a special card (10, 7, 2). Please try again.")
                continue  # try again

        # Remove chosen cards from player's hand and add to pile
        for card in chosen_cards:
            distributed_cards[player].remove(card)
            pile.append({"suit": card['suit'], "rank": card['rank'], "type": CARD_TYPE_PILE})
            print(f"{player} played: {card['suit']} {card['rank']}")

        # Special rule for '10': Flush the pile
        if p_rank == '10':
            pile.clear()
            print("Pile flushed! You can throw another card.")
            continue  # Allow the player to throw another card

        # Rule for '2': Allow another card
        if p_rank == '2':
            print("You can throw another card.")
            continue  # Allow the player to throw another card

        # Check if the deck is empty
        if not deck:
            print("Deck is empty. Proceeding with face-up cards.")
            # Play face-up cards
            face_up_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_FACE_UP]
            if face_up_cards:
                for card in face_up_cards:
                    distributed_cards[player].remove(card)
                    pile.append({"suit": card['suit'], "rank": card['rank'], "type": CARD_TYPE_PILE})
                    print(f"{player} played: {card['suit']} {card['rank']}")
            else:
                # Play face-down cards randomly
                face_down_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_FACE_DOWN]
                if face_down_cards:
                    random_card = random.choice(face_down_cards)
                    distributed_cards[player].remove(random_card)
                    pile.append({"suit": random_card['suit'], "rank": random_card['rank'], "type": CARD_TYPE_PILE})
                    print(f"{player} played face-down card: {random_card['suit']} {random_card['rank']}")

        else:
            print(f"{player} draws a card:")
            deck, distributed_cards[player] = pick_up_from_deck(deck, distributed_cards[player])
            pprint(distributed_cards)
        
        break

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
    for turn in range(1, 6):  # Simulate 5 turns
        play_turn(f"Player {((turn - 1) % players) + 1}", distributed_cards, deck, pile)

    # # Main game loop placeholder
    # while True:
    #     # Logic for turns and game rules
    #     pass
