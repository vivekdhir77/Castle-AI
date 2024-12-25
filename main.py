import json
import random

def distribute(players, num_cards, deck):
    """
    Distributes cards evenly among players.
    """
    if players * num_cards > len(deck):
        raise ValueError("Not enough cards to distribute")

    random.shuffle(deck)
    distribution = {f"Player {i+1}": deck[i * num_cards:(i + 1) * num_cards] for i in range(players)}
    return distribution, deck[players * num_cards:]

def pprint(distributed_cards):
    if str(type(distributed_cards))!="<class 'dict'>":
        cnt = 1
        for card in distributed_cards:
            print(cnt, card)
            cnt += 1
        return
    print("Player 1")
    print("-"*10)
    for card in distributed_cards["Player 1"]:
        if(card['type']!="Face Down"):
            print(card["suit"], " ", card["rank"], " ", card["type"])
    print("*"*15)
    print("Computer")
    print("-"*10)
    for card in distributed_cards["Player 2"]:
        if(card['type']!="Face Down"):
            print(card["suit"], " ", card["rank"], " ", card["type"])
    print("\n\n")

def pprint_Face_Down(distributed_cards):
    print("\n--FACED DOWN--")
    print("Player 1")
    print("-"*10)
    for card in distributed_cards["Player 1"]:
        if(card['type']=="Face Down"):
            print(card["suit"], " ", card["rank"])
    print("*"*15)
    print("Computer")
    print("-"*10)
    for card in distributed_cards["Player 2"]:
        if(card['type']=="Face Down"):
            print(card["suit"], " ", card["rank"])
    print("\n\n")
    
def pick_up_from_deck(deck, cards_in_hand):
    cards_in_hand_cnt = 0
    for card in cards_in_hand:
        if(card['type']=="In Hand"):
            cards_in_hand_cnt += 1
    if(cards_in_hand_cnt>3):
        return deck, cards_in_hand
    pick_up = max(3-cards_in_hand_cnt, 0)
    for i in range(pick_up):
        deck[0]["type"] = "In Hand"
        cards_in_hand.insert(0, deck[0])
        deck.pop(0)
    return deck, cards_in_hand

def pick_up_pile(pile, cards_in_hand):
    for card in pile:
        card["type"] = "In Hand"
        cards_in_hand.insert(0, card)
    return [], cards_in_hand
    

if __name__ == "__main__":
    with open("cards.json", "r") as file:
        deck = json.load(file)
    print("Deck loaded successfully.")
    players = 2  # Adjust the number of players
    num_cards = 9  # Number of cards per player

    try:
        distributed_cards, deck = distribute(players, num_cards, deck)
        
    except ValueError as e:
        print(e)

    for player, cards in distributed_cards.items():
        cnt = 0
        for card in cards:
            if(cnt<3):
                card["type"] = "In Hand"
            elif(cnt<6):
                card["type"] = "Face Up"
            else:
                card["type"] = "Face Down"
            cnt += 1

    # pile
    # pile pickup
    # 
    # 10 - flush
    # 2 - wild card (go again)
    # 7 - go lower

    print(distributed_cards)
    print("\n\n")
    print("popping: ", distributed_cards["Player 1"][0])
    distributed_cards["Player 1"].pop(0)
    print(distributed_cards)
    pprint(distributed_cards)
    deck, distributed_cards["Player 1"] = pick_up_from_deck(deck, distributed_cards["Player 1"])
    pprint(distributed_cards)
    pile = [] 

    while True:
        pass

    
