import json
import random

# Constants for card types
CARD_TYPE_IN_HAND = "In Hand"
CARD_TYPE_FACE_UP = "Face Up"
CARD_TYPE_FACE_DOWN = "Face Down"
CARD_TYPE_PILE = "Pile"

# Constants for card ranks
RANK_ORDER = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
}

def get_playable_cards(player_cards):
    """Returns the current playable cards based on priority (hand -> face up -> face down)"""
    in_hand = [card for card in player_cards if card['type'] == CARD_TYPE_IN_HAND]
    if in_hand:
        return in_hand, CARD_TYPE_IN_HAND
    
    face_up = [card for card in player_cards if card['type'] == CARD_TYPE_FACE_UP]
    if face_up:
        return face_up, CARD_TYPE_FACE_UP
    
    face_down = [card for card in player_cards if card['type'] == CARD_TYPE_FACE_DOWN]
    return face_down, CARD_TYPE_FACE_DOWN

def is_valid_play(card_rank, pile, seven_rule_active=False):
    """Validates if a card can be played on the current pile"""
    if not pile:
        return True
    
    top_card = pile[-1]
    if seven_rule_active and RANK_ORDER[card_rank] > 7:
        return False
    
    return (RANK_ORDER[card_rank] >= RANK_ORDER[top_card['rank']] or 
            card_rank in ['10', '7', '2'])

def handle_special_card(rank, pile):
    """Handles special card effects (10, 2, 7) and returns if another turn is allowed"""
    if rank == '10':
        pile.clear()
        print("Pile flushed!")
        return True
    elif rank == '2':
        print("2 played! You can play another card.")
        return True
    elif rank == '7':
        print("Seven played! Next player must play 7 or lower.")
    return False

def play_card(player, card, distributed_cards, pile):
    """Plays a card and adds it to the pile"""
    distributed_cards[player].remove(card)
    pile.append({"suit": card['suit'], "rank": card['rank'], "type": CARD_TYPE_PILE})
    print(f"{player} played: {card['suit']} {card['rank']}")
    return handle_special_card(card['rank'], pile)

def play_face_down_card(player, distributed_cards, pile):
    """Handles playing a face down card and returns if game is over"""
    face_down_cards = [card for card in distributed_cards[player] if card['type'] == CARD_TYPE_FACE_DOWN]
    
    while face_down_cards:
        card = random.choice(face_down_cards)
        print(f"{player} played face-down card: {card['suit']} {card['rank']}")
        
        if not is_valid_play(card['rank'], pile):
            print(f"Face-down card cannot be played. Must pick up the pile.")
            distributed_cards[player].remove(card)
            card['type'] = CARD_TYPE_IN_HAND
            pile.append(card)
            pile, distributed_cards[player] = pick_up_pile(pile, distributed_cards[player])
            return False
            
        play_again = play_card(player, card, distributed_cards, pile)
        if play_again:
            face_down_cards = [c for c in distributed_cards[player] if c['type'] == CARD_TYPE_FACE_DOWN]
            continue
            
        return len(distributed_cards[player]) == 0
    
    return False

def handle_human_turn(player, distributed_cards, pile, playable_cards):
    """Handles human player's turn"""
    consecutive_plays = 0
    while True:
        # Check if we need to replenish cards after multiple plays
        if consecutive_plays >= 3 and not any(card['type'] == CARD_TYPE_IN_HAND for card in distributed_cards[player]):
            # Try to pick up from deck first
            if deck:
                deck, distributed_cards[player] = pick_up_from_deck(deck, distributed_cards[player])
            # If no deck cards, convert face-up cards to hand cards
            elif any(card['type'] == CARD_TYPE_FACE_UP for card in distributed_cards[player]):
                for card in distributed_cards[player]:
                    if card['type'] == CARD_TYPE_FACE_UP:
                        card['type'] = CARD_TYPE_IN_HAND
            
            # Get updated playable cards
            playable_cards, _ = get_playable_cards(distributed_cards[player])
            consecutive_plays = 0

        print("\nYour playable cards:")
        for card in playable_cards:
            print(f"{card['suit']} {card['rank']}")
            
        action = input("\nEnter 'play' to play a card or 'pickup' to pick up the pile: ").strip().lower()
        
        if action == 'pickup':
            if not pile:
                print("Cannot pick up an empty pile.")
                continue
            pile, distributed_cards[player] = pick_up_pile(pile, distributed_cards[player])
            return False
            
        if action == 'play':
            suit = input("Enter suit: ").strip()
            rank = input("Enter rank: ").strip()
            
            chosen_cards = [c for c in playable_cards if c['rank'].lower() == rank.lower()] #if c['suit'].lower() == suit.lower() and
            
            if not chosen_cards:
                print("Invalid card choice.")
                continue
                
            card = chosen_cards[0]
            seven_rule_active = pile and pile[-1]['rank'] == '7'
            
            if not is_valid_play(card['rank'], pile, seven_rule_active):
                print("Invalid play. Card must be higher or special (2, 7, 10).")
                if seven_rule_active:
                    print("Seven rule is active - must play 7 or lower!")
                continue
            
            play_again = play_card(player, card, distributed_cards, pile)
            if play_again:
                consecutive_plays += 1
                playable_cards, _ = get_playable_cards(distributed_cards[player])
                if not playable_cards:
                    print("No more cards to play!")
                    return False
                continue
                
            return len(distributed_cards[player]) == 0
            
        print("Invalid action. Please try again.")

def play_turn(player, distributed_cards, deck, pile, is_computer=False):
    """Main turn function that handles both human and computer turns"""
    print(f"\n{player}'s turn:")
    
    playable_cards, card_type = get_playable_cards(distributed_cards[player])
    
    if pile:
        print(f"Top card: {pile[-1]['suit']} {pile[-1]['rank']} (Pile size: {len(pile)})")
    else:
        print("Pile is empty")
    
    # Handle face down cards
    if card_type == CARD_TYPE_FACE_DOWN:
        game_over = play_face_down_card(player, distributed_cards, pile)
    else:
        if is_computer:
            # TODO: Implement computer logic here
            pass
        else:
            game_over = handle_human_turn(player, distributed_cards, pile, playable_cards)
    
    # Draw cards if needed
    if deck and not game_over:
        deck, distributed_cards[player] = pick_up_from_deck(deck, distributed_cards[player])
    
    pprint(distributed_cards)
    return game_over

# Utility functions (unchanged)
def distribute(players, num_cards, deck):
    if players * num_cards > len(deck):
        raise ValueError("Not enough cards to distribute")

    random.shuffle(deck)
    distribution = {
        f"Player {i + 1}": deck[i * num_cards:(i + 1) * num_cards] 
        for i in range(players)
    }
    return distribution, deck[players * num_cards:]

def pick_up_from_deck(deck, cards_in_hand):
    current_hand_count = sum(1 for card in cards_in_hand if card['type'] == CARD_TYPE_IN_HAND)
    pick_up_count = max(3 - current_hand_count, 0)

    for _ in range(pick_up_count):
        if not deck:
            break
        deck[0]["type"] = CARD_TYPE_IN_HAND
        cards_in_hand.append(deck.pop(0))

    return deck, cards_in_hand

def pick_up_pile(pile, cards_in_hand):
    for card in pile:
        card["type"] = CARD_TYPE_IN_HAND
    cards_in_hand.extend(pile)
    return [], cards_in_hand

def initialize_player_cards(distributed_cards):
    for cards in distributed_cards.values():
        for i, card in enumerate(cards):
            if i < 3:
                card["type"] = CARD_TYPE_IN_HAND
            elif i < 6:
                card["type"] = CARD_TYPE_FACE_UP
            else:
                card["type"] = CARD_TYPE_FACE_DOWN

def pprint(distributed_cards):
    for player, cards in distributed_cards.items():
        print(f"\n{player}\n" + "-" * 10)
        for card in cards:
            if card['type'] != CARD_TYPE_FACE_DOWN:
                print(f"{card['suit']} {card['rank']} {card['type']}")
        print("*" * 15)

if __name__ == "__main__":
    # Load deck
    try:
        with open("cards.json", "r") as file:
            deck = json.load(file)
        print("Deck loaded successfully.")
    except FileNotFoundError:
        print("Error: 'cards.json' file not found.")
        exit(1)

    # Game setup
    players = 2
    num_cards = 9
    distributed_cards, deck = distribute(players, num_cards, deck)
    initialize_player_cards(distributed_cards)
    pile = []

    # Choose game mode
    human_vs_human = input("Do you want to play Human vs Human? (yes/no): ").strip().lower() == 'yes'
    
    # Game loop
    game_over = False
    current_player = 1

    while not game_over:
        current_player_name = f"Player {current_player}"
        is_computer = not human_vs_human and current_player == 2  # Player 2 is computer if not human vs human
        
        game_over = play_turn(
            current_player_name, 
            distributed_cards, 
            deck, 
            pile,
            is_computer=is_computer
        )
        
        if not game_over:
            current_player = 2 if current_player == 1 else 1
